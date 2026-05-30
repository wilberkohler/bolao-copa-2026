import os
import random
import hmac
import re
import smtplib
from datetime import datetime, date, timedelta
from email.message import EmailMessage
from functools import wraps
from html import escape
from pathlib import Path

import pytz
from flask import (Flask, render_template, redirect, url_for,
                   request, flash, session, jsonify, g,
                   send_from_directory, make_response)
from sqlalchemy import func, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.orm import selectinload
from models import db, Competidor, Jogo, Palpite, Resultado, Pontuacao, HistoricoPalpite, User, Grupo, SolicitacaoExclusaoDados, RelatorioRodadaEnvio
from runtime_config import load_runtime_config
from seed_jogos_copa_2026 import seed_jogos
from result_sync import sync_finished_results_football_data
from scoring import (calcular_pontuacao_jogo, get_ranking,
                     prazo_aberto, status_palpite_para_jogo, palpite_editavel)

BR_TZ = pytz.timezone("America/Sao_Paulo")
ADMIN_EMAIL = "wilber.kohler@naest.com.br"
WK3_GROUP_NAME = "WK3"
WK3_GROUP_CODE = os.environ.get("WK3_GROUP_CODE", "WK3")
PUBLIC_GROUP_COUNT = int(os.environ.get("PUBLIC_GROUP_COUNT", "100"))
RANKING_ETAPAS = {
    "geral": "Geral",
    "grupos": "Fase de Grupos",
    "mata_mata": "Mata-mata ate a Final",
}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "bolao-copa-2026-secret")
database_url = os.environ.get("DATABASE_URL", "sqlite:///bolao.db")
# Alguns provedores ainda expõem postgres://; SQLAlchemy requer postgresql://.
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

db.init_app(app)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


def normalize_email(email):
    return (email or "").strip().lower()


def email_valido(email):
    return bool(EMAIL_RE.match(normalize_email(email)))


def find_user_by_email(email):
    email = normalize_email(email)
    if not email:
        return None
    return User.query.filter(func.lower(User.email) == email).first()


def email_serializer():
    return URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="confirmar-email")


def password_reset_serializer():
    return URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="redefinir-senha")


def make_email_token(user):
    return email_serializer().dumps({"id": user.id, "email": normalize_email(user.email)})


def make_password_reset_token(user):
    return password_reset_serializer().dumps({
        "id": user.id,
        "email": normalize_email(user.email),
        "senha_hash": user.senha_hash,
    })


def send_email_message(to_email, subject, text_body, html_body=None):
    host = os.environ.get("SMTP_HOST", "").strip()
    if not host:
        app.logger.warning("SMTP_HOST não configurado; e-mail não enviado para %s", to_email)
        return False

    port = int(os.environ.get("SMTP_PORT", "587"))
    username = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "")
    from_email = os.environ.get("SMTP_FROM", username or "no-reply@bolao2026.com").strip()
    use_ssl = os.environ.get("SMTP_SSL", "").lower() in {"1", "true", "yes"}
    use_tls = os.environ.get("SMTP_TLS", "true").lower() in {"1", "true", "yes"}

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = to_email
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    smtp_cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with smtp_cls(host, port, timeout=30) as smtp:
        if use_tls and not use_ssl:
            smtp.starttls()
        if username or password:
            smtp.login(username, password)
        smtp.send_message(message)
    return True


def send_email_confirmation(user):
    token = make_email_token(user)
    confirm_url = url_for("confirmar_email", token=token, _external=True)
    subject = "Confirme seu e-mail - Bolão Copa 2026"
    text = (
        f"Olá, {user.nome}!\n\n"
        "Confirme seu e-mail para receber os relatórios das rodadas do Bolão Copa 2026:\n"
        f"{confirm_url}\n\n"
        "Se você não fez este cadastro, ignore esta mensagem."
    )
    html = f"""
    <p>Olá, {escape(user.nome)}!</p>
    <p>Confirme seu e-mail para receber os relatórios das rodadas do Bolão Copa 2026.</p>
    <p><a href="{confirm_url}">Confirmar e-mail</a></p>
    <p>Se você não fez este cadastro, ignore esta mensagem.</p>
    """
    return send_email_message(user.email, subject, text, html)


def send_password_reset_email(user):
    token = make_password_reset_token(user)
    reset_url = url_for("redefinir_senha", token=token, _external=True)
    subject = "Redefina sua senha - Bolão Copa 2026"
    text = (
        f"Olá, {user.nome}!\n\n"
        "Recebemos uma solicitação para redefinir sua senha no Bolão Copa 2026.\n"
        f"Acesse este link em até 1 hora para criar uma nova senha:\n{reset_url}\n\n"
        "Se você não solicitou esta alteração, ignore esta mensagem."
    )
    html = f"""
    <p>Olá, {escape(user.nome)}!</p>
    <p>Recebemos uma solicitação para redefinir sua senha no Bolão Copa 2026.</p>
    <p><a href="{reset_url}">Criar nova senha</a></p>
    <p>Este link expira em 1 hora. Se você não solicitou esta alteração, ignore esta mensagem.</p>
    """
    return send_email_message(user.email, subject, text, html)


def is_authorized_admin(user):
    return bool(user and user.ativo and normalize_email(user.email) == ADMIN_EMAIL)


def sync_admin_flags():
    """Garante que apenas o e-mail autorizado tenha permissao administrativa."""
    changed = False
    for user in User.query.all():
        should_be_admin = normalize_email(user.email) == ADMIN_EMAIL
        if user.eh_admin != should_be_admin:
            user.eh_admin = should_be_admin
            changed = True
    if changed:
        db.session.commit()


def ensure_group_publication_columns():
    """Adds group publication columns for existing Render databases."""
    inspector = inspect(db.engine)
    existing = {column["name"] for column in inspector.get_columns("grupos")}
    dialect = db.engine.dialect.name
    bool_type = "BOOLEAN" if dialect != "sqlite" else "INTEGER"
    bool_true = "TRUE" if dialect != "sqlite" else "1"
    bool_false = "FALSE" if dialect != "sqlite" else "0"
    statements = []

    if "publico" not in existing:
        statements.append(f"ALTER TABLE grupos ADD COLUMN publico {bool_type} DEFAULT {bool_true}")
    if "requer_codigo" not in existing:
        statements.append(f"ALTER TABLE grupos ADD COLUMN requer_codigo {bool_type} DEFAULT {bool_false}")
    if "codigo_acesso_hash" not in existing:
        statements.append("ALTER TABLE grupos ADD COLUMN codigo_acesso_hash VARCHAR(255)")
    if "criado_pelo_sistema" not in existing:
        statements.append(f"ALTER TABLE grupos ADD COLUMN criado_pelo_sistema {bool_type} DEFAULT {bool_false}")

    if not statements:
        return

    with db.engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def ensure_user_email_columns():
    """Adds email confirmation columns for existing databases."""
    inspector = inspect(db.engine)
    existing = {column["name"] for column in inspector.get_columns("users")}
    dialect = db.engine.dialect.name
    bool_type = "BOOLEAN" if dialect != "sqlite" else "INTEGER"
    bool_false = "FALSE" if dialect != "sqlite" else "0"
    bool_true = "TRUE" if dialect != "sqlite" else "1"
    statements = []

    if "email_confirmado" not in existing:
        statements.append(f"ALTER TABLE users ADD COLUMN email_confirmado {bool_type} DEFAULT {bool_false}")
    if "email_confirmado_em" not in existing:
        statements.append("ALTER TABLE users ADD COLUMN email_confirmado_em TIMESTAMP")
    if "receber_relatorios" not in existing:
        statements.append(f"ALTER TABLE users ADD COLUMN receber_relatorios {bool_type} DEFAULT {bool_true}")

    if not statements:
        return

    with db.engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def grupo_publico_payload(grupo):
    return {
        "id": grupo.id,
        "nome": grupo.nome,
        "descricao": grupo.descricao,
        "publico": bool(grupo.publico),
        "requer_codigo": bool(grupo.requer_codigo),
    }


def grupos_para_cadastro():
    return (Grupo.query
            .filter(Grupo.publico == True)
            .order_by(Grupo.requer_codigo, Grupo.nome)
            .all())


def validar_grupo_cadastro(grupo_id, codigo_grupo=""):
    if not grupo_id:
        return None, None

    try:
        grupo_id_int = int(grupo_id)
    except (TypeError, ValueError):
        return None, "Grupo invalido."

    grupo = Grupo.query.get(grupo_id_int)
    if not grupo or not grupo.publico:
        return None, "Grupo indisponivel para cadastro."

    if grupo.requer_codigo and not grupo.check_codigo_acesso(codigo_grupo):
        return None, "Codigo do grupo privado invalido."

    return grupo, None


def seed_public_groups():
    changed = False
    existing = {grupo.nome: grupo for grupo in Grupo.query.all()}

    for numero in range(1, PUBLIC_GROUP_COUNT + 1):
        nome = f"Grupo {numero:03d}"
        grupo = existing.get(nome)
        if grupo:
            if grupo.publico is None:
                grupo.publico = True
                changed = True
            continue

        db.session.add(Grupo(
            nome=nome,
            descricao="Grupo aberto para participantes do Bolao Copa 2026.",
            publico=True,
            requer_codigo=False,
            criado_pelo_sistema=True,
        ))
        changed = True

    grupo_wk3 = existing.get(WK3_GROUP_NAME)
    if not grupo_wk3:
        grupo_wk3 = Grupo(
            nome=WK3_GROUP_NAME,
            descricao="Grupo privado WK3.",
            publico=True,
            requer_codigo=True,
            criado_pelo_sistema=True,
        )
        grupo_wk3.set_codigo_acesso(WK3_GROUP_CODE)
        db.session.add(grupo_wk3)
        changed = True
    else:
        if grupo_wk3.publico is not True:
            grupo_wk3.publico = True
            changed = True
        if grupo_wk3.requer_codigo is not True:
            grupo_wk3.requer_codigo = True
            changed = True
        if not grupo_wk3.codigo_acesso_hash and WK3_GROUP_CODE:
            grupo_wk3.set_codigo_acesso(WK3_GROUP_CODE)
            changed = True

    if changed:
        db.session.commit()


def normalizar_etapa_ranking(etapa):
    etapa = (etapa or "geral").strip()
    return etapa if etapa in RANKING_ETAPAS else "geral"


def ranking_kwargs_por_etapa(etapa):
    return {} if etapa == "geral" else {"etapa": etapa}


def etapa_atual_ranking():
    primeiro_mata_mata = (Jogo.query
                          .filter_by(mata_mata=True)
                          .order_by(Jogo.data_jogo)
                          .first())
    if primeiro_mata_mata and date.today() >= primeiro_mata_mata.data_jogo:
        return "mata_mata"
    return "grupos"


def podium_payload(ranking):
    return [
        {
            "posicao": item["posicao"],
            "nome": item["competidor"].nome,
            "apelido": item["competidor"].apelido,
            "pontos": item["pontos"],
        }
        for item in ranking[:3]
    ]


def is_simulated_result(resultado):
    return bool(resultado and (resultado.usuario_lancamento or "").startswith("simulacao:"))


def clear_simulated_results():
    simulated_results = Resultado.query.filter(Resultado.usuario_lancamento.like("simulacao:%")).all()
    jogo_ids = [r.jogo_id for r in simulated_results]

    if not jogo_ids:
        return 0

    Pontuacao.query.filter(Pontuacao.jogo_id.in_(jogo_ids)).delete(synchronize_session=False)

    for resultado in simulated_results:
        db.session.delete(resultado)

    for jogo in Jogo.query.filter(Jogo.id.in_(jogo_ids)).all():
        jogo.status = "Agendado"

    db.session.commit()

    for jogo in Jogo.query.filter(Jogo.resultado.has()).all():
        if jogo.resultado and not is_simulated_result(jogo.resultado):
            calcular_pontuacao_jogo(db, Palpite, Pontuacao, Resultado, jogo)

    db.session.commit()
    return len(jogo_ids)


def group_items_by_world_cup_group(items, item_to_jogo):
    grupos_ordenados = []
    grupos_map = {}

    for item in items:
        jogo = item_to_jogo(item)
        grupo = jogo.grupo if jogo and jogo.grupo else "Outros"
        if grupo not in grupos_map:
            grupos_map[grupo] = []
            grupos_ordenados.append(grupo)
        grupos_map[grupo].append(item)

    return [
        {
            "id": f"grupo-{idx}",
            "nome": grupo,
            "label": f"Grupo {grupo}" if grupo != "Outros" else "Outros",
            "itens": grupos_map[grupo],
        }
        for idx, grupo in enumerate(grupos_ordenados)
    ]


def rodada_key_label(jogos):
    primeiro = jogos[0]
    rodada = primeiro.rodada if primeiro.rodada is not None else 0
    key = f"{primeiro.fase}|{rodada}"
    label = f"{primeiro.fase} - Rodada {rodada}" if rodada else primeiro.fase
    return key, label


def rodadas_fechadas_com_resultado():
    jogos = Jogo.query.options(selectinload(Jogo.resultado)).order_by(Jogo.fase, Jogo.rodada, Jogo.data_jogo).all()
    grupos = {}
    for jogo in jogos:
        if jogo.rodada is None:
            continue
        grupos.setdefault((jogo.fase, jogo.rodada), []).append(jogo)

    fechadas = []
    for _, itens in grupos.items():
        if itens and all(j.resultado for j in itens):
            key, label = rodada_key_label(itens)
            fechadas.append({"key": key, "label": label, "jogos": itens})
    return fechadas


def montar_relatorio_rodada(user, competidor, rodada):
    jogo_ids = [j.id for j in rodada["jogos"]]
    pontuacoes = Pontuacao.query.filter(
        Pontuacao.competidor_id == competidor.id,
        Pontuacao.jogo_id.in_(jogo_ids),
    ).all()
    pontos_rodada = sum(p.pontos for p in pontuacoes)
    placares = sum(1 for p in pontuacoes if p.placar_exato)
    ranking = get_ranking(db, Competidor, Pontuacao, Palpite, Jogo)
    posicao = next((item["posicao"] for item in ranking if item["competidor"].id == competidor.id), None)
    top5 = ranking[:5]
    jogos_linhas = []

    for jogo in rodada["jogos"]:
        resultado = jogo.resultado
        pont = next((p for p in pontuacoes if p.jogo_id == jogo.id), None)
        jogos_linhas.append(
            f"- {jogo.time_a} {resultado.gols_a} x {resultado.gols_b} {jogo.time_b}: "
            f"{pont.pontos if pont else 0} ponto(s)"
        )

    top_linhas = [
        f"{item['posicao']}. {item['competidor'].apelido} - {item['pontos']} pts"
        for item in top5
    ]
    subject = f"Relatório da {rodada['label']} - Bolão Copa 2026"
    text = (
        f"Olá, {user.nome}!\n\n"
        f"Relatório da {rodada['label']}:\n"
        f"Seus pontos na rodada: {pontos_rodada}\n"
        f"Placares exatos na rodada: {placares}\n"
        f"Sua posição no ranking geral: {posicao or '-'}\n\n"
        "Jogos da rodada:\n"
        + "\n".join(jogos_linhas)
        + "\n\nTop 5 geral:\n"
        + "\n".join(top_linhas)
        + "\n\nAcesse o app para ver todos os detalhes."
    )
    html = (
        f"<p>Olá, {escape(user.nome)}!</p>"
        f"<h2>{escape(rodada['label'])}</h2>"
        f"<p><strong>Seus pontos na rodada:</strong> {pontos_rodada}</p>"
        f"<p><strong>Placares exatos na rodada:</strong> {placares}</p>"
        f"<p><strong>Sua posição no ranking geral:</strong> {posicao or '-'}</p>"
        "<h3>Jogos da rodada</h3><ul>"
        + "".join(f"<li>{escape(linha[2:])}</li>" for linha in jogos_linhas)
        + "</ul><h3>Top 5 geral</h3><ol>"
        + "".join(f"<li>{escape(item['competidor'].apelido)} - {item['pontos']} pts</li>" for item in top5)
        + "</ol><p>Acesse o app para ver todos os detalhes.</p>"
    )
    return subject, text, html


def send_pending_round_reports():
    if not os.environ.get("SMTP_HOST", "").strip():
        return {"sent": 0, "skipped": 0, "errors": ["SMTP_HOST não configurado."]}

    sent = 0
    skipped = 0
    errors = []
    rodadas = rodadas_fechadas_com_resultado()
    users = User.query.filter_by(ativo=True, email_confirmado=True, receber_relatorios=True).all()

    for rodada in rodadas:
        for user in users:
            envio = RelatorioRodadaEnvio.query.filter_by(user_id=user.id, rodada_key=rodada["key"]).first()
            if envio and envio.status == "enviado":
                skipped += 1
                continue
            competidor = Competidor.query.filter_by(user_id=user.id, ativo=True).first()
            if not competidor:
                skipped += 1
                continue

            subject, text_body, html_body = montar_relatorio_rodada(user, competidor, rodada)
            if not envio:
                envio = RelatorioRodadaEnvio(user_id=user.id, rodada_key=rodada["key"])
            envio.rodada_label = rodada["label"]
            envio.email = user.email
            envio.enviado_em = datetime.utcnow()
            envio.erro = None
            try:
                send_email_message(user.email, subject, text_body, html_body)
                envio.status = "enviado"
                sent += 1
            except Exception as exc:
                app.logger.exception("Falha ao enviar relatório %s para %s", rodada["key"], user.email)
                envio.status = "erro"
                envio.erro = str(exc)[:1000]
                errors.append(f"{user.email}: {exc}")
            db.session.add(envio)

    db.session.commit()
    return {"sent": sent, "skipped": skipped, "errors": errors}


@app.before_request
def load_logged_in_user():
    """Carrega usuário logado na sessão."""
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        try:
            g.user = User.query.get(user_id)
        except SQLAlchemyError:
            app.logger.exception("Falha ao carregar usuário da sessão")
            db.session.rollback()
            session.clear()
            g.user = None
            return
        if g.user and g.user.eh_admin != is_authorized_admin(g.user):
            g.user.eh_admin = is_authorized_admin(g.user)
            db.session.commit()


def login_required(f):
    """Decorator para exigir login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            flash("Você precisa fazer login.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator para exigir admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authorized_admin(g.user):
            flash("Acesso restrito a administradores.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function


@app.before_request
def init_db():
    pass


@app.route("/manifest.webmanifest")
def manifest_webmanifest():
    return send_from_directory(STATIC_DIR, "manifest.webmanifest", mimetype="application/manifest+json")


@app.route("/service-worker.js")
def service_worker():
    response = make_response(send_from_directory(STATIC_DIR, "service-worker.js", mimetype="application/javascript"))
    response.headers["Cache-Control"] = "no-cache"
    return response


@app.route("/.well-known/assetlinks.json")
def assetlinks_json():
    package_name = os.environ.get("TWA_PACKAGE_ID", "br.com.kohler.bolao2026")
    fingerprint = os.environ.get(
        "TWA_SHA256_CERT_FINGERPRINT",
        "2A:08:AC:0E:64:57:BE:4E:A9:A4:74:DC:E4:56:21:B8:C1:0B:F8:65:39:83:92:CA:40:50:CA:98:3C:2A:DB:2E",
    )
    return jsonify([
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": package_name,
                "sha256_cert_fingerprints": [fingerprint],
            },
        }
    ])


def agora_br():
    return datetime.now(BR_TZ)


def ensure_competidor_profile(user):
    """Cria perfil de competidor para o usuário caso não exista."""
    if not user:
        return None

    existente = Competidor.query.filter_by(user_id=user.id).first()
    if existente:
        return existente

    base_apelido = (user.apelido or user.nome or f"user{user.id}").strip()
    apelido = base_apelido
    sufixo = 1
    while Competidor.query.filter_by(apelido=apelido).first():
        apelido = f"{base_apelido}_{sufixo}"
        sufixo += 1

    competidor = Competidor(
        nome=user.nome,
        apelido=apelido,
        email=user.email,
        user_id=user.id,
        ativo=True,
    )
    db.session.add(competidor)
    db.session.commit()
    return competidor


# ---------------------------------------------------------------------------
# API JSON para Bolao 3 nativo
# ---------------------------------------------------------------------------
def _dt_iso(value):
    if not value:
        return None
    return value.isoformat()


def _current_user_payload(user):
    competidor = ensure_competidor_profile(user)
    grupo = Grupo.query.get(user.grupo_id) if user and user.grupo_id else None
    return {
        "id": user.id,
        "nome": user.nome,
        "email": user.email,
        "apelido": user.apelido,
        "eh_admin": is_authorized_admin(user),
        "email_confirmado": bool(user.email_confirmado),
        "receber_relatorios": bool(user.receber_relatorios),
        "grupo": {"id": grupo.id, "nome": grupo.nome} if grupo else None,
        "competidor": {
            "id": competidor.id,
            "nome": competidor.nome,
            "apelido": competidor.apelido,
        } if competidor else None,
    }


def _jogo_payload(jogo, palpite=None, pontuacao=None):
    resultado = jogo.resultado
    return {
        "id": jogo.id,
        "numero_partida": jogo.numero_partida,
        "fase": jogo.fase,
        "grupo": jogo.grupo,
        "rodada": jogo.rodada,
        "data_jogo": _dt_iso(jogo.data_jogo),
        "hora_brasilia": jogo.hora_brasilia,
        "time_a": jogo.time_a,
        "time_b": jogo.time_b,
        "sigla_time_a": jogo.sigla_time_a,
        "sigla_time_b": jogo.sigla_time_b,
        "estadio": jogo.estadio,
        "cidade": jogo.cidade,
        "pais": jogo.pais,
        "mata_mata": bool(jogo.mata_mata),
        "prazo_palpite": _dt_iso(jogo.prazo_palpite),
        "status": jogo.status,
        "editavel": palpite_editavel(jogo) and resultado is None,
        "resultado": {
            "gols_a": resultado.gols_a,
            "gols_b": resultado.gols_b,
            "classificado": resultado.classificado,
        } if resultado else None,
        "palpite": {
            "gols_a": palpite.palpite_gols_a,
            "gols_b": palpite.palpite_gols_b,
            "classificado": palpite.palpite_classificado,
        } if palpite else None,
        "pontuacao": {
            "pontos": pontuacao.pontos,
            "placar_exato": pontuacao.placar_exato,
            "vencedor_correto": pontuacao.vencedor_correto,
        } if pontuacao else None,
    }


def api_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return jsonify({"ok": False, "error": "unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function


@app.route("/api/v1/health")
def api_health():
    return jsonify({"ok": True, "app": "Bolao 3", "version": "0.1"})


@app.route("/api/v1/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = normalize_email(data.get("email"))
    senha = data.get("senha") or data.get("password") or ""
    user = find_user_by_email(email)

    if not user or not user.check_password(senha) or not user.ativo:
        return jsonify({"ok": False, "error": "E-mail ou senha invalidos."}), 401

    session.clear()
    session["user_id"] = user.id
    session.permanent = True
    return jsonify({"ok": True, "user": _current_user_payload(user)})


@app.route("/api/v1/grupos")
def api_grupos():
    grupos = grupos_para_cadastro()
    return jsonify({"ok": True, "grupos": [grupo_publico_payload(grupo) for grupo in grupos]})


@app.route("/api/v1/registro", methods=["POST"])
def api_registro():
    data = request.get_json(silent=True) or {}
    nome = (data.get("nome") or "").strip()
    email = normalize_email(data.get("email"))
    apelido = (data.get("apelido") or "").strip()
    senha = data.get("senha") or data.get("password") or ""
    grupo, erro_grupo = validar_grupo_cadastro(data.get("grupo_id"), data.get("codigo_grupo"))

    if not nome or not email or not apelido or not senha:
        return jsonify({"ok": False, "error": "Preencha nome, e-mail, apelido e senha."}), 400

    if not email_valido(email):
        return jsonify({"ok": False, "error": "Informe um e-mail válido."}), 400

    if erro_grupo:
        return jsonify({"ok": False, "error": erro_grupo}), 400

    if find_user_by_email(email):
        return jsonify({"ok": False, "error": "E-mail ja cadastrado."}), 409

    user = User(
        nome=nome,
        email=email,
        apelido=apelido,
        grupo_id=grupo.id if grupo else None,
        eh_admin=normalize_email(email) == ADMIN_EMAIL,
        email_confirmado=False,
        receber_relatorios=True,
    )
    user.set_password(senha)
    db.session.add(user)
    db.session.flush()
    db.session.add(Competidor(
        nome=nome,
        apelido=apelido,
        email=email,
        user_id=user.id,
        ativo=True,
    ))
    db.session.commit()

    try:
        send_email_confirmation(user)
    except Exception:
        app.logger.exception("Falha ao enviar confirmação de e-mail para %s", user.email)

    session.clear()
    session["user_id"] = user.id
    session.permanent = True
    return jsonify({"ok": True, "user": _current_user_payload(user)})


@app.route("/api/v1/logout", methods=["POST"])
@api_login_required
def api_logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/v1/reenviar-confirmacao-email", methods=["POST"])
@api_login_required
def api_reenviar_confirmacao_email():
    if g.user.email_confirmado:
        return jsonify({"ok": True, "message": "E-mail ja confirmado."})

    try:
        sent = send_email_confirmation(g.user)
    except Exception as exc:
        app.logger.exception("Falha ao reenviar confirmação para %s", g.user.email)
        return jsonify({"ok": False, "error": str(exc)}), 500

    if not sent:
        return jsonify({"ok": False, "error": "SMTP ainda nao configurado."}), 503
    return jsonify({"ok": True})


@app.route("/api/v1/me")
@api_login_required
def api_me():
    return jsonify({"ok": True, "user": _current_user_payload(g.user)})


@app.route("/api/v1/dashboard")
@api_login_required
def api_dashboard():
    competidor = ensure_competidor_profile(g.user)
    etapa_podium = etapa_atual_ranking()
    ranking_geral = get_ranking(db, Competidor, Pontuacao, Palpite, Jogo)
    ranking_etapa = get_ranking(db, Competidor, Pontuacao, Palpite, Jogo, **ranking_kwargs_por_etapa(etapa_podium))
    podium_geral = podium_payload(ranking_geral)
    podium_etapa = podium_payload(ranking_etapa)
    total_jogos = Jogo.query.count()
    palpites_enviados = Palpite.query.filter_by(competidor_id=competidor.id, valido=True).count()
    proximos = (Jogo.query
                .filter(Jogo.data_jogo >= date.today())
                .order_by(Jogo.data_jogo, Jogo.hora_brasilia)
                .limit(6).all())
    return jsonify({
        "ok": True,
        "summary": {
            "total_jogos": total_jogos,
            "palpites_enviados": palpites_enviados,
            "total_competidores": Competidor.query.filter_by(ativo=True).count(),
        },
        "podium": podium_etapa,
        "podium_geral": podium_geral,
        "podium_etapa": podium_etapa,
        "podium_etapa_key": etapa_podium,
        "podium_etapa_label": RANKING_ETAPAS[etapa_podium],
        "proximos_jogos": [_jogo_payload(j) for j in proximos],
    })


@app.route("/api/v1/jogos")
@api_login_required
def api_jogos():
    fase = request.args.get("fase", "").strip()
    grupo = request.args.get("grupo", "").strip()
    query = Jogo.query.options(selectinload(Jogo.resultado)).order_by(Jogo.data_jogo, Jogo.hora_brasilia)
    if fase:
        query = query.filter_by(fase=fase)
    if grupo:
        query = query.filter_by(grupo=grupo)
    jogos = query.all()
    return jsonify({"ok": True, "jogos": [_jogo_payload(jogo) for jogo in jogos]})


@app.route("/api/v1/palpites", methods=["GET", "POST"])
@api_login_required
def api_palpites():
    competidor = ensure_competidor_profile(g.user)

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        acao = data.get("acao") or "salvar"
        if acao == "limpar_futuros":
            jogo_ids_para_limpar = {
                int(jid)
                for jid in data.get("jogo_ids", [])
                if str(jid).isdigit()
            }
            palpites_futuros = []
            for palpite in Palpite.query.filter_by(competidor_id=competidor.id, valido=True).all():
                if jogo_ids_para_limpar and palpite.jogo_id not in jogo_ids_para_limpar:
                    continue
                jogo = Jogo.query.get(palpite.jogo_id)
                if jogo and palpite_editavel(jogo) and not jogo.resultado:
                    palpites_futuros.append(palpite)

            for palpite in palpites_futuros:
                HistoricoPalpite.query.filter_by(palpite_id=palpite.id).delete(synchronize_session=False)
                db.session.delete(palpite)

            db.session.commit()
            return jsonify({"ok": True, "cleared": len(palpites_futuros)})

        palpites = data.get("palpites") or []
        saved = 0
        errors = []

        for item in palpites:
            jogo_id = item.get("jogo_id")
            jogo = Jogo.query.get(jogo_id) if jogo_id else None
            if not jogo or not palpite_editavel(jogo) or jogo.resultado:
                errors.append({"jogo_id": jogo_id, "error": "Palpite bloqueado para este jogo."})
                continue

            try:
                gols_a = int(item.get("gols_a"))
                gols_b = int(item.get("gols_b"))
                if gols_a < 0 or gols_b < 0:
                    raise ValueError
            except (TypeError, ValueError):
                errors.append({"jogo_id": jogo_id, "error": "Gols invalidos."})
                continue

            classificado = (item.get("classificado") or "").strip() or None
            palpite = Palpite.query.filter_by(
                competidor_id=competidor.id,
                jogo_id=jogo.id,
                valido=True,
            ).first()
            agora = datetime.now(BR_TZ)

            if palpite:
                db.session.add(HistoricoPalpite(
                    palpite_id=palpite.id,
                    competidor_id=competidor.id,
                    jogo_id=jogo.id,
                    palpite_gols_a_anterior=palpite.palpite_gols_a,
                    palpite_gols_b_anterior=palpite.palpite_gols_b,
                    palpite_classificado_anterior=palpite.palpite_classificado,
                    palpite_gols_a_novo=gols_a,
                    palpite_gols_b_novo=gols_b,
                    palpite_classificado_novo=classificado,
                    data_alteracao=agora,
                ))
                palpite.palpite_gols_a = gols_a
                palpite.palpite_gols_b = gols_b
                palpite.palpite_classificado = classificado
                palpite.data_ultima_alteracao = agora
            else:
                db.session.add(Palpite(
                    competidor_id=competidor.id,
                    jogo_id=jogo.id,
                    palpite_gols_a=gols_a,
                    palpite_gols_b=gols_b,
                    palpite_classificado=classificado,
                    data_envio=agora,
                    data_ultima_alteracao=agora,
                ))
            saved += 1

        db.session.commit()
        return jsonify({"ok": not errors, "saved": saved, "errors": errors})

    jogos = Jogo.query.options(selectinload(Jogo.resultado)).order_by(Jogo.data_jogo, Jogo.hora_brasilia).all()
    jogo_ids = [j.id for j in jogos]
    palpites_map = {
        p.jogo_id: p
        for p in Palpite.query.filter(
            Palpite.competidor_id == competidor.id,
            Palpite.valido == True,
            Palpite.jogo_id.in_(jogo_ids)
        ).all()
    }
    pontuacoes_map = {
        p.jogo_id: p
        for p in Pontuacao.query.filter(
            Pontuacao.competidor_id == competidor.id,
            Pontuacao.jogo_id.in_(jogo_ids)
        ).all()
    }
    return jsonify({
        "ok": True,
        "jogos": [_jogo_payload(j, palpites_map.get(j.id), pontuacoes_map.get(j.id)) for j in jogos],
    })


@app.route("/api/v1/ranking")
@api_login_required
def api_ranking():
    fase = request.args.get("fase", "").strip() or None
    etapa = normalizar_etapa_ranking(request.args.get("etapa"))
    ranking = get_ranking(
        db,
        Competidor,
        Pontuacao,
        Palpite,
        Jogo,
        fase=fase,
        **({} if fase else ranking_kwargs_por_etapa(etapa))
    )
    return jsonify({
        "ok": True,
        "etapa": etapa if not fase else "fase",
        "etapa_label": fase or RANKING_ETAPAS[etapa],
        "ranking": [
            {
                "posicao": item["posicao"],
                "nome": item["competidor"].nome,
                "apelido": item["competidor"].apelido,
                "pontos": item["pontos"],
                "placares_exatos": item["placares_exatos"],
                "vencedores_corretos": item["vencedores_corretos"],
                "saldos_corretos": item["saldos_corretos"],
                "classificados_corretos": item["classificados_corretos"],
                "palpites_enviados": item["palpites_enviados"],
                "palpites_nao_enviados": item["palpites_nao_enviados"],
                "aproveitamento": item["aproveitamento"],
                "ultima_pontuacao": item["ultima_pontuacao"],
            }
            for item in ranking
        ],
    })


# ---------------------------------------------------------------------------
# Helpers de contexto
# ---------------------------------------------------------------------------
@app.context_processor
def inject_globals():
    return dict(
        user=g.user,
        agora_br=agora_br(),
    )


# ---------------------------------------------------------------------------
# AUTENTICAÇÃO
# ---------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user is not None:
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        email = normalize_email(request.form.get("email", ""))
        senha = request.form.get("senha", "")
        try:
            user = find_user_by_email(email)
            password_ok = bool(user and user.check_password(senha))
        except Exception:
            app.logger.exception("Falha ao validar login para %s", normalize_email(email))
            db.session.rollback()
            flash("Não foi possível validar o login agora. Tente novamente em instantes.", "danger")
            return render_template("auth/login.html", email=email)
        
        if user and password_ok and user.ativo:
            session.clear()
            session["user_id"] = user.id
            session.permanent = True
            try:
                ensure_competidor_profile(user)
            except Exception:
                app.logger.exception("Falha ao preparar perfil do usuário %s", user.id)
                db.session.rollback()
                flash("Não foi possível preparar seu acesso agora. Tente novamente em instantes.", "danger")
                return render_template("auth/login.html", email=email)
            flash(f"Bem-vindo, {user.nome}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("E-mail ou senha inválidos, ou usuário inativo.", "danger")
    
    return render_template("auth/login.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if g.user is not None:
        return redirect(url_for("dashboard"))
    
    grupos = grupos_para_cadastro()
    
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = normalize_email(request.form.get("email", ""))
        apelido = request.form.get("apelido", "").strip()
        senha = request.form.get("senha", "")
        grupo_id = request.form.get("grupo_id")
        codigo_grupo = request.form.get("codigo_grupo", "")
        grupo, erro_grupo = validar_grupo_cadastro(grupo_id, codigo_grupo)
        
        if not nome or not email or not apelido or not senha:
            flash("Todos os campos são obrigatórios.", "danger")
            return render_template("auth/registro.html", grupos=grupos)
        
        if erro_grupo:
            flash(erro_grupo, "danger")
            return render_template("auth/registro.html", grupos=grupos)

        if not email_valido(email):
            flash("Informe um e-mail válido.", "danger")
            return render_template("auth/registro.html", grupos=grupos)

        if find_user_by_email(email):
            flash("E-mail já cadastrado.", "danger")
            return render_template("auth/registro.html", grupos=grupos)
        
        user = User(
            nome=nome,
            email=email,
            apelido=apelido,
            grupo_id=grupo.id if grupo else None,
            eh_admin=normalize_email(email) == ADMIN_EMAIL,
            email_confirmado=False,
            receber_relatorios=True,
        )
        user.set_password(senha)
        db.session.add(user)
        db.session.flush()  # Gera o ID do user
        
        # Criar Competidor associado
        competidor = Competidor(
            nome=nome,
            apelido=apelido,
            email=email,
            user_id=user.id,
            ativo=True
        )
        db.session.add(competidor)
        db.session.commit()
        
        flash("Cadastro realizado com sucesso! Faça login.", "success")
        try:
            if send_email_confirmation(user):
                flash("Enviamos um link de confirmação para seu e-mail.", "info")
            else:
                flash("Cadastro criado. A confirmação de e-mail será enviada quando o SMTP estiver configurado.", "warning")
        except Exception:
            app.logger.exception("Falha ao enviar confirmação de e-mail para %s", user.email)
            flash("Cadastro criado, mas não foi possível enviar a confirmação de e-mail agora.", "warning")

        return redirect(url_for("login"))
    
    return render_template("auth/registro.html", grupos=grupos)


@app.route("/esqueci-senha", methods=["GET", "POST"])
def esqueci_senha():
    if g.user is not None:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = normalize_email(request.form.get("email", ""))
        if not email_valido(email):
            flash("Informe um e-mail válido.", "danger")
            return render_template("auth/esqueci_senha.html", email=email)

        user = find_user_by_email(email)
        if user and user.ativo:
            try:
                if not send_password_reset_email(user):
                    flash("SMTP ainda não configurado. Não foi possível enviar a recuperação agora.", "warning")
                    return render_template("auth/esqueci_senha.html", email=email)
            except Exception:
                app.logger.exception("Falha ao enviar recuperação de senha para %s", email)
                flash("Não foi possível enviar a recuperação agora. Tente novamente em instantes.", "danger")
                return render_template("auth/esqueci_senha.html", email=email)

        flash("Se este e-mail estiver cadastrado, enviaremos um link para redefinir a senha.", "success")
        return redirect(url_for("login"))

    return render_template("auth/esqueci_senha.html")


@app.route("/redefinir-senha/<token>", methods=["GET", "POST"])
def redefinir_senha(token):
    if g.user is not None:
        return redirect(url_for("dashboard"))

    try:
        data = password_reset_serializer().loads(token, max_age=60 * 60)
    except SignatureExpired:
        flash("O link para redefinir senha expirou. Solicite um novo link.", "warning")
        return redirect(url_for("esqueci_senha"))
    except BadSignature:
        flash("Link para redefinir senha inválido.", "danger")
        return redirect(url_for("login"))

    user = User.query.get(data.get("id"))
    if (
        not user
        or not user.ativo
        or normalize_email(user.email) != normalize_email(data.get("email"))
        or user.senha_hash != data.get("senha_hash")
    ):
        flash("Não foi possível usar este link. Solicite uma nova redefinição de senha.", "danger")
        return redirect(url_for("esqueci_senha"))

    if request.method == "POST":
        senha = request.form.get("senha", "")
        confirmar_senha = request.form.get("confirmar_senha", "")
        if len(senha) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.", "danger")
            return render_template("auth/redefinir_senha.html", token=token)
        if senha != confirmar_senha:
            flash("As senhas não conferem.", "danger")
            return render_template("auth/redefinir_senha.html", token=token)

        user.set_password(senha)
        db.session.commit()
        flash("Senha redefinida com sucesso. Faça login com sua nova senha.", "success")
        return redirect(url_for("login"))

    return render_template("auth/redefinir_senha.html", token=token)


@app.route("/confirmar-email/<token>")
def confirmar_email(token):
    try:
        data = email_serializer().loads(token, max_age=60 * 60 * 24 * 7)
    except SignatureExpired:
        flash("O link de confirmação expirou. Faça login e solicite um novo link.", "warning")
        return redirect(url_for("login"))
    except BadSignature:
        flash("Link de confirmação inválido.", "danger")
        return redirect(url_for("login"))

    user = User.query.get(data.get("id"))
    if not user or normalize_email(user.email) != normalize_email(data.get("email")):
        flash("Não foi possível confirmar este e-mail.", "danger")
        return redirect(url_for("login"))

    user.email_confirmado = True
    user.email_confirmado_em = datetime.utcnow()
    db.session.commit()
    flash("E-mail confirmado com sucesso. Você receberá os relatórios das rodadas.", "success")
    return redirect(url_for("login"))


@app.route("/reenviar-confirmacao-email", methods=["POST"])
@login_required
def reenviar_confirmacao_email():
    if g.user.email_confirmado:
        flash("Seu e-mail já está confirmado.", "info")
        return redirect(url_for("dashboard"))

    try:
        if send_email_confirmation(g.user):
            flash("Enviamos um novo link de confirmação para seu e-mail.", "success")
        else:
            flash("SMTP ainda não configurado. Não foi possível enviar a confirmação.", "warning")
    except Exception:
        app.logger.exception("Falha ao reenviar confirmação para %s", g.user.email)
        flash("Não foi possível enviar a confirmação agora.", "danger")
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login", logged_out="1"))


# ---------------------------------------------------------------------------
# GRUPOS (admin)
# ---------------------------------------------------------------------------
@app.route("/grupos")
@admin_required
def listar_grupos():
    grupos = Grupo.query.order_by(Grupo.nome).all()
    return render_template("admin/grupos_lista.html", grupos=grupos)


@app.route("/grupos/novo", methods=["GET", "POST"])
@admin_required
def novo_grupo():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        descricao = request.form.get("descricao", "").strip()
        publico = request.form.get("publico") == "on"
        requer_codigo = request.form.get("requer_codigo") == "on"
        codigo_acesso = request.form.get("codigo_acesso", "").strip()
        
        if not nome:
            flash("Nome é obrigatório.", "danger")
            return render_template("admin/grupos_form.html", grupo=None)
        
        if Grupo.query.filter_by(nome=nome).first():
            flash("Grupo já existe.", "danger")
            return render_template("admin/grupos_form.html", grupo=None)
        
        if requer_codigo and not codigo_acesso:
            flash("Informe um codigo para grupos privados.", "danger")
            return render_template("admin/grupos_form.html", grupo=None)

        grupo = Grupo(
            nome=nome,
            descricao=descricao or None,
            publico=publico,
            requer_codigo=requer_codigo,
            criado_por_id=g.user.id
        )
        if requer_codigo:
            grupo.set_codigo_acesso(codigo_acesso)
        db.session.add(grupo)
        db.session.commit()
        flash(f"Grupo '{grupo.nome}' criado!", "success")
        return redirect(url_for("listar_grupos"))
    
    return render_template("admin/grupos_form.html", grupo=None)


@app.route("/grupos/<int:gid>/editar", methods=["GET", "POST"])
@admin_required
def editar_grupo(gid):
    grupo = Grupo.query.get_or_404(gid)
    if request.method == "POST":
        grupo.nome = request.form.get("nome", "").strip()
        grupo.descricao = request.form.get("descricao", "").strip() or None
        grupo.publico = request.form.get("publico") == "on"
        grupo.requer_codigo = request.form.get("requer_codigo") == "on"
        codigo_acesso = request.form.get("codigo_acesso", "").strip()
        if grupo.requer_codigo and codigo_acesso:
            grupo.set_codigo_acesso(codigo_acesso)
        elif grupo.requer_codigo and not grupo.codigo_acesso_hash:
            flash("Informe um codigo para grupos privados.", "danger")
            return render_template("admin/grupos_form.html", grupo=grupo)
        elif not grupo.requer_codigo:
            grupo.codigo_acesso_hash = None
        grupo.updated_at = datetime.utcnow()
        db.session.commit()
        flash("Grupo atualizado.", "success")
        return redirect(url_for("listar_grupos"))
    
    return render_template("admin/grupos_form.html", grupo=grupo)


@app.route("/grupos/<int:gid>/excluir", methods=["POST"])
@admin_required
def excluir_grupo(gid):
    grupo = Grupo.query.get_or_404(gid)
    if User.query.filter_by(grupo_id=gid).count() > 0:
        flash("Não é possível excluir grupo com usuários. Remova os usuários primeiro.", "danger")
        return redirect(url_for("listar_grupos"))
    db.session.delete(grupo)
    db.session.commit()
    flash("Grupo excluído.", "success")
    return redirect(url_for("listar_grupos"))


# ---------------------------------------------------------------------------
# SELEÇÃO DE COMPETIDOR (legacy - será mantido)
# ---------------------------------------------------------------------------
@app.route("/selecionar_competidor/<int:cid>")
def selecionar_competidor(cid):
    session["competidor_id"] = cid
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/logout_competidor")
def logout_competidor():
    session.pop("competidor_id", None)
    return redirect(url_for("dashboard"))


# ---------------------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------------------
@app.route("/")
@login_required
def dashboard():
    # Usar o competidor associado ao usuário logado
    if not g.user:
        return redirect(url_for("login"))

    competidor = ensure_competidor_profile(g.user)
    total_competidores = Competidor.query.count()
    total_jogos = Jogo.query.count()
    jogos_realizados = Jogo.query.filter(Jogo.status.in_(["Encerrado", "Resultado Lançado", "Pontuado"])).count()
    jogos_pendentes = total_jogos - jogos_realizados
    
    # Palpites do usuário logado
    palpites_enviados = Palpite.query.filter_by(competidor_id=competidor.id, valido=True).count()

    # Próximos jogos (não iniciados, próximos 10)
    hoje = date.today()
    proximos = (Jogo.query
                .filter(Jogo.data_jogo >= hoje)
                .filter(Jogo.status.in_(["Agendado", "Aberto para palpites"]))
                .order_by(Jogo.data_jogo, Jogo.hora_et)
                .limit(10).all())

    # Próximo jogo
    proximo_jogo = proximos[0] if proximos else None

    # Próximo prazo
    proximo_prazo = None
    if proximo_jogo:
        proximo_prazo = proximo_jogo.prazo_palpite

    # Pódio atual
    podium_view = request.args.get("podium", "etapa").strip()
    if podium_view not in {"etapa", "geral"}:
        podium_view = "etapa"
    etapa_podium = etapa_atual_ranking()
    ranking_geral = get_ranking(db, Competidor, Pontuacao, Palpite, Jogo)
    ranking_etapa = get_ranking(
        db,
        Competidor,
        Pontuacao,
        Palpite,
        Jogo,
        **ranking_kwargs_por_etapa(etapa_podium),
    )
    podium_geral = ranking_geral[:3]
    podium_etapa = ranking_etapa[:3]
    podium = podium_geral if podium_view == "geral" else podium_etapa
    lider = podium[0] if podium else None

    # Palpites pendentes (jogos abertos sem palpite do competidor logado)
    # Carrega apenas jogos futuros/nao encerrados para evitar query full-scan
    jogos_candidatos = (Jogo.query
                        .filter(Jogo.status.in_(["Agendado", "Aberto para palpites"]))
                        .filter(Jogo.prazo_palpite >= datetime.utcnow())
                        .with_entities(Jogo.id).all())
    jogos_abertos = {row[0] for row in jogos_candidatos}
    palpites_existentes = {p.jogo_id for p in
                           Palpite.query.filter_by(competidor_id=competidor.id, valido=True)
                           .filter(Palpite.jogo_id.in_(jogos_abertos)).all()}
    palpites_pendentes = len(jogos_abertos - palpites_existentes)

    # Status palpite por jogo para o competidor logado
    palpites_map = {}
    for p in Palpite.query.filter_by(competidor_id=competidor.id, valido=True).all():
        palpites_map[p.jogo_id] = p

    proximos_com_status = []
    for j in proximos:
        p = palpites_map.get(j.id)
        proximos_com_status.append({
            "jogo": j,
            "status_palpite": status_palpite_para_jogo(j, p),
            "prazo_aberto": prazo_aberto(j),
            "palpite": p,
        })

    return render_template("dashboard.html",
                           competidor_logado=competidor,
                           total_competidores=total_competidores,
                           total_jogos=total_jogos,
                           jogos_realizados=jogos_realizados,
                           jogos_pendentes=jogos_pendentes,
                           palpites_enviados=palpites_enviados,
                           palpites_pendentes=palpites_pendentes,
                           lider=lider,
                           podium=podium,
                           podium_view=podium_view,
                           podium_etapa_label=RANKING_ETAPAS[etapa_podium],
                           podium_etapa_key=etapa_podium,
                           proximo_jogo=proximo_jogo,
                           proximo_prazo=proximo_prazo,
                           proximos_com_status=proximos_com_status)


# ---------------------------------------------------------------------------
# COMPETIDORES
# ---------------------------------------------------------------------------
@app.route("/competidores")
@admin_required
def listar_competidores():
    competidores = Competidor.query.order_by(Competidor.nome).all()
    return render_template("competidores/lista.html", competidores=competidores)


@app.route("/competidores/novo", methods=["GET", "POST"])
@admin_required
def novo_competidor():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        apelido = request.form.get("apelido", "").strip()
        if not nome:
            flash("Nome é obrigatório.", "danger")
            return render_template("competidores/form.html", competidor=None)
        if not apelido:
            flash("Apelido é obrigatório.", "danger")
            return render_template("competidores/form.html", competidor=None)
        if Competidor.query.filter_by(apelido=apelido).first():
            flash("Apelido já cadastrado. Escolha outro.", "danger")
            return render_template("competidores/form.html", competidor=None)

        c = Competidor(
            nome=nome,
            apelido=apelido,
            email=request.form.get("email", "").strip() or None,
            telefone=request.form.get("telefone", "").strip() or None,
            data_entrada=date.today(),
            ativo=True,
            observacoes=request.form.get("observacoes", "").strip() or None,
        )
        db.session.add(c)
        db.session.commit()
        flash(f"Competidor {c.apelido} cadastrado com sucesso!", "success")
        return redirect(url_for("listar_competidores"))
    return render_template("competidores/form.html", competidor=None)


@app.route("/competidores/<int:cid>/editar", methods=["GET", "POST"])
@admin_required
def editar_competidor(cid):
    c = Competidor.query.get_or_404(cid)
    grupos = Grupo.query.order_by(Grupo.nome).all()
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        apelido = request.form.get("apelido", "").strip()
        if not nome:
            flash("Nome é obrigatório.", "danger")
            return render_template("competidores/form.html", competidor=c, grupos=grupos)
        if not apelido:
            flash("Apelido é obrigatório.", "danger")
            return render_template("competidores/form.html", competidor=c, grupos=grupos)
        dup = Competidor.query.filter_by(apelido=apelido).first()
        if dup and dup.id != c.id:
            flash("Apelido já cadastrado. Escolha outro.", "danger")
            return render_template("competidores/form.html", competidor=c, grupos=grupos)
        c.nome = nome
        c.apelido = apelido
        c.email = request.form.get("email", "").strip() or None
        c.telefone = request.form.get("telefone", "").strip() or None
        c.observacoes = request.form.get("observacoes", "").strip() or None
        c.updated_at = datetime.utcnow()

        grupo_id_raw = request.form.get("grupo_id")
        grupo_id = int(grupo_id_raw) if grupo_id_raw else None

        user_vinculado = User.query.get(c.user_id) if c.user_id else None

        # Em bases antigas pode existir competidor sem user_id; tenta vincular automaticamente.
        if not user_vinculado and c.email:
            user_vinculado = User.query.filter(User.email.ilike(c.email)).first()
        if not user_vinculado and c.apelido:
            user_vinculado = User.query.filter(User.apelido.ilike(c.apelido)).first()

        if user_vinculado:
            c.user_id = user_vinculado.id
            user_vinculado.grupo_id = grupo_id
        elif grupo_id is not None:
            flash("Não foi possível vincular este competidor a um usuário para salvar o grupo.", "warning")

        db.session.commit()
        flash("Competidor atualizado.", "success")
        return redirect(url_for("listar_competidores"))
    return render_template("competidores/form.html", competidor=c, grupos=grupos)


@app.route("/competidores/<int:cid>/inativar", methods=["POST"])
@admin_required
def inativar_competidor(cid):
    c = Competidor.query.get_or_404(cid)
    c.ativo = False
    c.updated_at = datetime.utcnow()
    db.session.commit()
    flash(f"{c.apelido} inativado.", "warning")
    return redirect(url_for("listar_competidores"))


@app.route("/competidores/<int:cid>/reativar", methods=["POST"])
@admin_required
def reativar_competidor(cid):
    c = Competidor.query.get_or_404(cid)
    c.ativo = True
    c.updated_at = datetime.utcnow()
    db.session.commit()
    flash(f"{c.apelido} reativado.", "success")
    return redirect(url_for("listar_competidores"))


@app.route("/competidores/<int:cid>/excluir", methods=["POST"])
@admin_required
def excluir_competidor(cid):
    c = Competidor.query.get_or_404(cid)
    if Palpite.query.filter_by(competidor_id=cid).count() > 0:
        flash("Não é possível excluir competidor com palpites vinculados. Use Inativar.", "danger")
        return redirect(url_for("listar_competidores"))
    db.session.delete(c)
    db.session.commit()
    flash("Competidor excluído.", "success")
    return redirect(url_for("listar_competidores"))


@app.route("/competidores/<int:cid>/historico")
@admin_required
def historico_competidor(cid):
    c = Competidor.query.get_or_404(cid)
    ranking = get_ranking(db, Competidor, Pontuacao, Palpite, Jogo)
    posicao = next((r["posicao"] for r in ranking if r["competidor"].id == cid), None)
    dados_ranking = next((r for r in ranking if r["competidor"].id == cid), None)

    palpites = (Palpite.query.filter_by(competidor_id=cid, valido=True)
                .join(Jogo).order_by(Jogo.data_jogo, Jogo.hora_et).all())

    historico = []
    for p in palpites:
        pont = Pontuacao.query.filter_by(competidor_id=cid, jogo_id=p.jogo_id).first()
        historico.append({
            "palpite": p,
            "jogo": p.jogo,
            "resultado": p.jogo.resultado,
            "pontuacao": pont,
            "alteracoes": HistoricoPalpite.query.filter_by(palpite_id=p.id).order_by(HistoricoPalpite.data_alteracao.desc()).all(),
        })

    return render_template("competidores/historico.html",
                           competidor=c,
                           posicao=posicao,
                           dados_ranking=dados_ranking,
                           historico=historico)


# ---------------------------------------------------------------------------
# JOGOS
# ---------------------------------------------------------------------------
@app.route("/jogos")
def listar_jogos():
    jogos = Jogo.query.options(selectinload(Jogo.resultado)).order_by(Jogo.data_jogo, Jogo.hora_et).all()
    jogos_por_grupo = group_items_by_world_cup_group(jogos, lambda jogo: jogo)
    return render_template("jogos/lista.html",
                           jogos=jogos,
                           jogos_por_grupo=jogos_por_grupo)


@app.route("/jogos/<int:jid>/editar", methods=["GET", "POST"])
def editar_jogo(jid):
    import pytz
    from seed_jogos_copa_2026 import et_to_brasilia, calcular_prazo_palpite
    j = Jogo.query.get_or_404(jid)
    if request.method == "POST":
        try:
            j.data_jogo = datetime.strptime(request.form["data_jogo"], "%Y-%m-%d").date()
            j.hora_et = request.form["hora_et"]
            j.hora_brasilia = et_to_brasilia(j.data_jogo, j.hora_et)
            j.prazo_palpite = calcular_prazo_palpite(j.data_jogo, j.hora_et)
            j.time_a = request.form.get("time_a", j.time_a)
            j.time_b = request.form.get("time_b", j.time_b)
            j.sigla_time_a = request.form.get("sigla_time_a", j.sigla_time_a)
            j.sigla_time_b = request.form.get("sigla_time_b", j.sigla_time_b)
            j.estadio = request.form.get("estadio", j.estadio)
            j.cidade = request.form.get("cidade", j.cidade)
            j.pais = request.form.get("pais", j.pais)
            j.status = request.form.get("status", j.status)
            j.updated_at = datetime.utcnow()
            db.session.commit()
            flash("Jogo atualizado.", "success")
            return redirect(url_for("listar_jogos"))
        except Exception as e:
            flash(f"Erro: {e}", "danger")
    status_list = ["Agendado", "Aberto para palpites", "Bloqueado para palpites",
                   "Em andamento", "Encerrado", "Resultado Lançado", "Pontuado", "Cancelado/Alterado"]
    return render_template("jogos/form.html", jogo=j, status_list=status_list)


# ---------------------------------------------------------------------------
# PALPITES
# ---------------------------------------------------------------------------
@app.route("/palpites", methods=["GET", "POST"])
@login_required
def palpites():
    user = g.user
    
    # POST — salvar palpites (apenas do próprio usuário)
    if request.method == "POST":
        competidor = ensure_competidor_profile(user)
        if not competidor:
            flash("Usuário não tem perfil de competidor.", "danger")
            return redirect(url_for("dashboard"))

        acao_palpite = request.form.get("acao_palpite", "salvar")
        if acao_palpite == "limpar_futuros":
            jogo_ids_para_limpar = {
                int(jid)
                for jid in request.form.getlist("limpar_jogo_id")
                if jid and jid.isdigit()
            }
            palpites_futuros = []
            for palpite in Palpite.query.filter_by(competidor_id=competidor.id, valido=True).all():
                if jogo_ids_para_limpar and palpite.jogo_id not in jogo_ids_para_limpar:
                    continue
                jogo = Jogo.query.get(palpite.jogo_id)
                if jogo and palpite_editavel(jogo) and not jogo.resultado:
                    palpites_futuros.append(palpite)

            for palpite in palpites_futuros:
                HistoricoPalpite.query.filter_by(palpite_id=palpite.id).delete(synchronize_session=False)
                db.session.delete(palpite)

            db.session.commit()
            flash(f"{len(palpites_futuros)} palpite(s) futuro(s) limpo(s).", "success")
            return redirect(url_for("palpites"))

        jogo_ids = request.form.getlist("jogo_id")
        saved = 0
        erros = []
        for jid in jogo_ids:
            jogo = Jogo.query.get(int(jid))
            resultado_existente = Resultado.query.filter_by(jogo_id=int(jid)).first()
            if not jogo or not palpite_editavel(jogo) or resultado_existente:
                erros.append(f"Jogo #{jid} com prazo encerrado.")
                continue
            gols_a = request.form.get(f"gols_a_{jid}", "").strip()
            gols_b = request.form.get(f"gols_b_{jid}", "").strip()
            classificado = request.form.get(f"classificado_{jid}", "").strip() or None

            if gols_a == "" or gols_b == "":
                continue

            try:
                gols_a = int(gols_a)
                gols_b = int(gols_b)
                if gols_a < 0 or gols_b < 0:
                    raise ValueError
            except ValueError:
                erros.append(f"Gols inválidos para o jogo #{jid}.")
                continue

            if jogo.mata_mata and gols_a == gols_b and not classificado:
                erros.append(f"Classificado obrigatório no mata-mata jogo #{jid} (empate).")
                continue

            if classificado and jogo.mata_mata:
                opcoes = [jogo.time_a.lower(), jogo.time_b.lower()]
                if classificado.lower() not in opcoes:
                    erros.append(f"Classificado inválido para jogo #{jid}.")
                    continue

            palpite = Palpite.query.filter_by(competidor_id=competidor.id, jogo_id=jogo.id, valido=True).first()
            agora = datetime.now(BR_TZ)

            if palpite:
                hist = HistoricoPalpite(
                    palpite_id=palpite.id,
                    competidor_id=competidor.id,
                    jogo_id=jogo.id,
                    palpite_gols_a_anterior=palpite.palpite_gols_a,
                    palpite_gols_b_anterior=palpite.palpite_gols_b,
                    palpite_classificado_anterior=palpite.palpite_classificado,
                    palpite_gols_a_novo=gols_a,
                    palpite_gols_b_novo=gols_b,
                    palpite_classificado_novo=classificado,
                    data_alteracao=agora,
                )
                db.session.add(hist)
                palpite.palpite_gols_a = gols_a
                palpite.palpite_gols_b = gols_b
                palpite.palpite_classificado = classificado
                palpite.data_ultima_alteracao = agora
            else:
                palpite = Palpite(
                    competidor_id=competidor.id,
                    jogo_id=jogo.id,
                    palpite_gols_a=gols_a,
                    palpite_gols_b=gols_b,
                    palpite_classificado=classificado,
                    data_envio=agora,
                    data_ultima_alteracao=agora,
                )
                db.session.add(palpite)
            saved += 1

        db.session.commit()
        if saved:
            flash(f"{saved} palpite(s) salvo(s).", "success")
        for e in erros:
            flash(e, "danger")
        return redirect(url_for("palpites"))

    todos_jogos = (Jogo.query
                   .options(selectinload(Jogo.resultado))
                   .order_by(Jogo.data_jogo, Jogo.hora_et)
                   .all())

    competidor = ensure_competidor_profile(user)
    palpites_map = {}

    if competidor:
        palpites_map = {p.jogo_id: p for p in
                        Palpite.query.filter_by(competidor_id=competidor.id, valido=True).all()}

    pontuacoes_map = {}
    if competidor and todos_jogos:
        jogo_ids = [j.id for j in todos_jogos]
        pontuacoes_map = {
            p.jogo_id: p
            for p in Pontuacao.query.filter(
                Pontuacao.competidor_id == competidor.id,
                Pontuacao.jogo_id.in_(jogo_ids)
            ).all()
        }

    jogos_com_status = []
    for j in todos_jogos:
        p = palpites_map.get(j.id)
        aberto = prazo_aberto(j)
        resultado_lancado = j.resultado is not None
        editavel = palpite_editavel(j) and not resultado_lancado
        if j.status == "Pontuado":
            st = "Pontuado"
        elif resultado_lancado:
            st = "Resultado Lançado"
        else:
            st = status_palpite_para_jogo(j, p)
        pont = pontuacoes_map.get(j.id)
        jogos_com_status.append({
            "jogo": j,
            "palpite": p,
            "palpites_todos": {},
            "prazo_aberto": aberto,
            "editavel": editavel,
            "status": st,
            "pontuacao": pont,
        })

    palpites_por_grupo = group_items_by_world_cup_group(jogos_com_status, lambda item: item["jogo"])

    return render_template("palpites/index.html",
                           jogos_com_status=jogos_com_status,
                           palpites_por_grupo=palpites_por_grupo,
                           competidor=competidor,
                           user=user)


# ---------------------------------------------------------------------------
# RESULTADOS (admin)
# ---------------------------------------------------------------------------
@app.route("/resultados")
@admin_required
def listar_resultados():
    fase_filtro = request.args.get("fase", "")
    filtro = request.args.get("filtro", "pendentes")
    query = Jogo.query.order_by(Jogo.data_jogo, Jogo.hora_et)
    if fase_filtro:
        query = query.filter_by(fase=fase_filtro)

    if filtro == "pendentes":
        # Jogos sem resultado lançado mas cujo prazo já encerrou
        todos = query.all()
        jogos = [j for j in todos if not j.resultado and not prazo_aberto(j)]
    elif filtro == "encerrados":
        jogos = query.filter(Jogo.status.in_(["Encerrado", "Resultado Lançado", "Pontuado"])).all()
    else:
        jogos = query.all()

    fases = [r[0] for r in db.session.query(Jogo.fase).distinct().order_by(Jogo.fase).all()]
    return render_template("resultados/lista.html", jogos=jogos, fases=fases,
                           fase_filtro=fase_filtro, filtro=filtro)


@app.route("/resultados/<int:jid>", methods=["GET", "POST"])
@admin_required
def lancar_resultado(jid):
    jogo = Jogo.query.get_or_404(jid)
    resultado = jogo.resultado

    if request.method == "POST":
        try:
            gols_a = int(request.form["gols_a"])
            gols_b = int(request.form["gols_b"])
            if gols_a < 0 or gols_b < 0:
                raise ValueError
        except (ValueError, KeyError):
            flash("Gols inválidos.", "danger")
            return render_template("resultados/form.html", jogo=jogo, resultado=resultado)

        classificado = request.form.get("classificado", "").strip() or None
        if jogo.mata_mata and not classificado:
            flash("Classificado obrigatório em mata-mata.", "danger")
            return render_template("resultados/form.html", jogo=jogo, resultado=resultado)

        if resultado:
            resultado.gols_a = gols_a
            resultado.gols_b = gols_b
            resultado.classificado = classificado
            resultado.data_lancamento = datetime.utcnow()
            resultado.usuario_lancamento = "admin"
            resultado.updated_at = datetime.utcnow()
        else:
            resultado = Resultado(
                jogo_id=jogo.id,
                gols_a=gols_a,
                gols_b=gols_b,
                classificado=classificado,
                resultado_lancado=True,
                data_lancamento=datetime.utcnow(),
                usuario_lancamento="admin",
            )
            db.session.add(resultado)

        jogo.status = "Resultado Lançado"
        db.session.commit()

        # Recalcular pontuação
        calcular_pontuacao_jogo(db, Palpite, Pontuacao, Resultado, jogo)
        report_stats = send_pending_round_reports()
        flash("Resultado lançado e pontuação calculada!", "success")
        if report_stats["sent"] or report_stats["skipped"]:
            flash(
                f"Relatórios de rodada: {report_stats['sent']} enviado(s), {report_stats['skipped']} ignorado(s).",
                "info",
            )
        return redirect(url_for("listar_resultados"))

    return render_template("resultados/form.html", jogo=jogo, resultado=resultado)


@app.route("/resultados/<int:jid>/recalcular", methods=["POST"])
@admin_required
def recalcular_resultado(jid):
    jogo = Jogo.query.get_or_404(jid)
    calcular_pontuacao_jogo(db, Palpite, Pontuacao, Resultado, jogo)
    flash("Pontuação recalculada.", "success")
    return redirect(url_for("listar_resultados"))


def _run_auto_result_sync(launched_by: str):
    api_key = os.environ.get("FOOTBALL_DATA_API_KEY", "").strip()
    if not api_key:
        raise ValueError("FOOTBALL_DATA_API_KEY não configurada.")

    base_url = os.environ.get("FOOTBALL_DATA_BASE_URL", "https://api.football-data.org/v4").strip()
    days_back = int(os.environ.get("RESULT_SYNC_DAYS_BACK", "2"))
    days_forward = int(os.environ.get("RESULT_SYNC_DAYS_FORWARD", "1"))

    return sync_finished_results_football_data(
        db,
        Jogo,
        Resultado,
        Palpite,
        Pontuacao,
        calcular_pontuacao_jogo,
        api_key=api_key,
        base_url=base_url,
        days_back=days_back,
        days_forward=days_forward,
        launched_by=launched_by,
    )


@app.route("/admin/sincronizar-resultados", methods=["POST"])
@admin_required
def sincronizar_resultados_admin():
    try:
        stats = _run_auto_result_sync(launched_by=f"sync-admin:{g.user.email}")
        report_stats = send_pending_round_reports()
    except Exception as exc:
        flash(f"Falha na sincronização automática: {exc}", "danger")
        return redirect(url_for("listar_resultados"))

    flash(
        (
            "Sincronização concluída: "
            f"{stats['fetched']} recebido(s), "
            f"{stats['created']} criado(s), "
            f"{stats['updated']} atualizado(s), "
            f"{stats['unchanged']} sem alteração, "
            f"{stats['recalculated']} recalculado(s)."
        ),
        "success",
    )

    if stats["unmatched"]:
        exemplos = ", ".join(stats["unmatched"][:3])
        flash(
            f"Jogos não mapeados automaticamente ({len(stats['unmatched'])}): {exemplos}",
            "warning",
        )
    if report_stats["sent"] or report_stats["skipped"]:
        flash(
            f"Relatórios de rodada: {report_stats['sent']} enviado(s), {report_stats['skipped']} ignorado(s).",
            "info",
        )

    return redirect(url_for("listar_resultados"))


@app.route("/internal/sync-resultados", methods=["POST"])
def sincronizar_resultados_cron():
    token = request.headers.get("X-Sync-Token", "").strip()
    expected = os.environ.get("RESULT_SYNC_TOKEN", "").strip()

    if not expected or not hmac.compare_digest(token, expected):
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    try:
        stats = _run_auto_result_sync(launched_by="sync-cron")
        report_stats = send_pending_round_reports()
        return jsonify({"ok": True, "stats": stats, "email_reports": report_stats})
    except Exception as exc:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(exc)}), 500


# ---------------------------------------------------------------------------
# RANKING
# ---------------------------------------------------------------------------
@app.route("/ranking")
def ranking_geral():
    etapa = normalizar_etapa_ranking(request.args.get("etapa"))
    ranking = get_ranking(db, Competidor, Pontuacao, Palpite, Jogo, **ranking_kwargs_por_etapa(etapa))
    return render_template("ranking/geral.html",
                           ranking=ranking,
                           etapa=etapa,
                           etapa_label=RANKING_ETAPAS[etapa],
                           ranking_etapas=RANKING_ETAPAS)


@app.route("/ranking/fase")
def ranking_por_fase():
    fase = request.args.get("fase", "")
    fases = [r[0] for r in db.session.query(Jogo.fase).distinct().order_by(Jogo.fase).all()]
    ranking = []
    if fase:
        ranking = get_ranking(db, Competidor, Pontuacao, Palpite, Jogo, fase=fase)
    return render_template("ranking/fase.html", ranking=ranking, fase=fase, fases=fases)


@app.route("/regras")
@login_required
def regras():
    return render_template("regras.html")


@app.route("/solicitar-exclusao-dados", methods=["GET", "POST"])
def solicitar_exclusao_dados():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        motivo = request.form.get("motivo", "").strip()

        if not nome or not email:
            flash("Nome e e-mail sao obrigatorios.", "danger")
            return render_template("solicitar_exclusao_dados.html", nome=nome, email=email, motivo=motivo)

        solicitacao = SolicitacaoExclusaoDados(
            nome=nome,
            email=email,
            motivo=motivo or None,
            status="Pendente",
        )
        db.session.add(solicitacao)
        db.session.commit()

        flash("Solicitacao recebida com sucesso. Nossa equipe analisara o pedido e retornara por e-mail.", "success")
        return redirect(url_for("solicitar_exclusao_dados"))

    return render_template("solicitar_exclusao_dados.html")


# ---------------------------------------------------------------------------
# INIT & RUN
# ---------------------------------------------------------------------------
def create_app():
    with app.app_context():
        db.create_all()
        ensure_group_publication_columns()
        ensure_user_email_columns()
        count = seed_jogos(db, Jogo)
        if count:
            print(f"[seed] {count} jogos carregados.")
        seed_public_groups()
        sync_admin_flags()
        # Cria admin automático via variáveis de ambiente (útil em cloud)
        admin_email = ADMIN_EMAIL
        admin_senha = os.environ.get("ADMIN_PASSWORD")
        admin_nome = os.environ.get("ADMIN_NOME", "Administrador")
        admin_apelido = os.environ.get("ADMIN_APELIDO", "admin")
        if admin_senha:
            existe = find_user_by_email(admin_email)
            if existe:
                existe.nome = admin_nome
                existe.apelido = admin_apelido
                existe.eh_admin = True
                existe.ativo = True
                existe.set_password(admin_senha)
                ensure_competidor_profile(existe)
                db.session.commit()
                print(f"[setup] Admin atualizado: {admin_email}")
            else:
                user = User(
                    nome=admin_nome,
                    email=admin_email,
                    apelido=admin_apelido,
                    eh_admin=True,
                    ativo=True,
                )
                user.set_password(admin_senha)
                db.session.add(user)
                db.session.flush()
                comp = Competidor(
                    nome=admin_nome,
                    apelido=admin_apelido,
                    email=admin_email,
                    user_id=user.id,
                    ativo=True,
                )
                db.session.add(comp)
                db.session.commit()
                print(f"[setup] Admin criado: {admin_email}")
    return app


# ---------------------------------------------------------------------------
# SIMULAÇÃO (admin)
# ---------------------------------------------------------------------------
@app.route("/admin/simulacao", methods=["GET", "POST"])
@admin_required
def simulacao():
    """Permite admin simular data futura para testar funcionalidades"""
    data_simulada = request.args.get("data_simulada", "")
    
    if request.method == "POST":
        acao = request.form.get("acao", "definir_data")
        data_str = request.form.get("data_simulada", "").strip()
        if acao == "limpar_resultados":
            removidos = clear_simulated_results()
            flash(f"{removidos} resultado(s) simulado(s) apagado(s). Ranking recalculado com resultados reais restantes.", "success")
            return redirect(url_for("simulacao"))

        try:
            data_obj = datetime.strptime(data_str, "%Y-%m-%d").date()

            if acao == "gerar_resultados":
                removidos = clear_simulated_results()

                jogos_ate_data = (
                    Jogo.query
                    .filter(Jogo.data_jogo <= data_obj)
                    .order_by(Jogo.data_jogo, Jogo.hora_et)
                    .all()
                )

                jogos_gerados = []
                for jogo in jogos_ate_data:
                    if jogo.resultado and not is_simulated_result(jogo.resultado):
                        continue

                    gols_a = random.randint(0, 4)
                    gols_b = random.randint(0, 4)

                    if jogo.mata_mata:
                        if gols_a == gols_b:
                            classificado = random.choice([jogo.time_a, jogo.time_b])
                        else:
                            classificado = jogo.time_a if gols_a > gols_b else jogo.time_b
                    else:
                        classificado = None

                    resultado = Resultado(
                        jogo_id=jogo.id,
                        gols_a=gols_a,
                        gols_b=gols_b,
                        classificado=classificado,
                        resultado_lancado=True,
                        data_lancamento=datetime.utcnow(),
                        usuario_lancamento=f"simulacao:{g.user.email}",
                    )
                    db.session.add(resultado)
                    jogo.status = "Resultado Lançado"
                    jogos_gerados.append(jogo)

                db.session.commit()

                for jogo in jogos_gerados:
                    calcular_pontuacao_jogo(db, Palpite, Pontuacao, Resultado, jogo)

                flash(f"Simulacao refeita: {removidos} resultado(s) simulado(s) anterior(es) apagado(s), {len(jogos_gerados)} novo(s) resultado(s) gerado(s) ate {data_str}. Resultados reais foram preservados.", "success")

            # Redireciona para GET com data_simulada como query param
            return redirect(url_for("simulacao", data_simulada=data_str))
        except ValueError:
            flash("Formato de data inválido. Use YYYY-MM-DD.", "danger")
    
    # Carregar dados com data simulada
    info_simulacao = {
        "data_simulada": data_simulada,
        "data_real": date.today().isoformat(),
        "resultados_simulados": Resultado.query.filter(
            Resultado.usuario_lancamento.like("simulacao:%")
        ).count(),
        "resultados_reais": sum(
            1 for r in Resultado.query.all() if not is_simulated_result(r)
        ),
    }
    
    if data_simulada:
        try:
            data_obj = datetime.strptime(data_simulada, "%Y-%m-%d").date()
            jogos_ate_data = Jogo.query.filter(Jogo.data_jogo <= data_obj).all()

            info_simulacao["jogos_neste_dia"] = (
                Jogo.query
                .filter_by(data_jogo=data_obj)
                .order_by(Jogo.hora_et)
                .all()
            )
            info_simulacao["total_jogos_ate_data"] = len(jogos_ate_data)
            info_simulacao["jogos_com_resultado_ate_data"] = sum(1 for j in jogos_ate_data if j.resultado)
            info_simulacao["jogos_sem_resultado_ate_data"] = (
                info_simulacao["total_jogos_ate_data"] - info_simulacao["jogos_com_resultado_ate_data"]
            )
            
            # Jogos já realizados até essa data
            info_simulacao["jogos_realizados"] = (
                Jogo.query
                .filter(Jogo.data_jogo < data_obj)
                .count()
            )
            
            # Próximo jogo após essa data
            info_simulacao["proximo_jogo"] = (
                Jogo.query
                .filter(Jogo.data_jogo >= data_obj)
                .order_by(Jogo.data_jogo, Jogo.hora_et)
                .first()
            )
        except ValueError:
            pass
    
    return render_template("admin/simulacao.html", info=info_simulacao)


if __name__ == "__main__":
    create_app()
    config = load_runtime_config()
    host = str(config["bind_host"])
    port = int(config["port"])
    debug = bool(config["debug"])
    app.run(host=host, port=port, debug=debug)
