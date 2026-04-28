import os
import random
import hmac
from datetime import datetime, date, timedelta
from functools import wraps
from pathlib import Path

import pytz
from flask import (Flask, render_template, redirect, url_for,
                   request, flash, session, jsonify, g,
                   send_from_directory, make_response)
from models import db, Competidor, Jogo, Palpite, Resultado, Pontuacao, HistoricoPalpite, User, Grupo
from runtime_config import load_runtime_config
from seed_jogos_copa_2026 import seed_jogos
from result_sync import sync_finished_results_football_data
from scoring import (calcular_pontuacao_jogo, get_ranking,
                     prazo_aberto, status_palpite_para_jogo, palpite_editavel)

BR_TZ = pytz.timezone("America/Sao_Paulo")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "bolao-copa-2026-secret")
database_url = os.environ.get("DATABASE_URL", "sqlite:///bolao.db")
# Alguns provedores ainda expÃµem postgres://; SQLAlchemy requer postgresql://.
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

db.init_app(app)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


@app.before_request
def load_logged_in_user():
    """Carrega usuÃ¡rio logado na sessÃ£o."""
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)


def login_required(f):
    """Decorator para exigir login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            flash("VocÃª precisa fazer login.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator para exigir admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None or not g.user.eh_admin:
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
    """Cria perfil de competidor para o usuÃ¡rio caso nÃ£o exista."""
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
# Helpers de contexto
# ---------------------------------------------------------------------------
@app.context_processor
def inject_globals():
    grupos = Grupo.query.order_by(Grupo.nome).all() if g.user else []
    grupos_dropdown = [g for g in grupos]
    return dict(
        user=g.user,
        grupos_dropdown=grupos_dropdown,
        agora_br=agora_br(),
    )


# ---------------------------------------------------------------------------
# AUTENTICAÃ‡ÃƒO
# ---------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user is not None:
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(senha) and user.ativo:
            session.clear()
            session["user_id"] = user.id
            session.permanent = True
            ensure_competidor_profile(user)
            flash(f"Bem-vindo, {user.nome}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("E-mail ou senha invÃ¡lidos, ou usuÃ¡rio inativo.", "danger")
    
    return render_template("auth/login.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if g.user is not None:
        return redirect(url_for("dashboard"))
    
    grupos = Grupo.query.order_by(Grupo.nome).all()
    
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        apelido = request.form.get("apelido", "").strip()
        senha = request.form.get("senha", "")
        grupo_id = request.form.get("grupo_id")
        
        if not nome or not email or not apelido or not senha:
            flash("Todos os campos sÃ£o obrigatÃ³rios.", "danger")
            return render_template("auth/registro.html", grupos=grupos)
        
        if User.query.filter_by(email=email).first():
            flash("E-mail jÃ¡ cadastrado.", "danger")
            return render_template("auth/registro.html", grupos=grupos)
        
        user = User(
            nome=nome,
            email=email,
            apelido=apelido,
            grupo_id=int(grupo_id) if grupo_id else None,
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
        
        flash("Cadastro realizado com sucesso! FaÃ§a login.", "success")
        return redirect(url_for("login"))
    
    return render_template("auth/registro.html", grupos=grupos)


@app.route("/logout")
def logout():
    session.clear()
    flash("VocÃª saiu.", "info")
    return redirect(url_for("login"))


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
        
        if not nome:
            flash("Nome Ã© obrigatÃ³rio.", "danger")
            return render_template("admin/grupos_form.html", grupo=None)
        
        if Grupo.query.filter_by(nome=nome).first():
            flash("Grupo jÃ¡ existe.", "danger")
            return render_template("admin/grupos_form.html", grupo=None)
        
        grupo = Grupo(
            nome=nome,
            descricao=descricao or None,
            criado_por_id=g.user.id
        )
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
        flash("NÃ£o Ã© possÃ­vel excluir grupo com usuÃ¡rios. Remova os usuÃ¡rios primeiro.", "danger")
        return redirect(url_for("listar_grupos"))
    db.session.delete(grupo)
    db.session.commit()
    flash("Grupo excluÃ­do.", "success")
    return redirect(url_for("listar_grupos"))


# ---------------------------------------------------------------------------
# SELEÃ‡ÃƒO DE COMPETIDOR (legacy - serÃ¡ mantido)
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
    # Usar o competidor associado ao usuÃ¡rio logado
    if not g.user:
        return redirect(url_for("login"))

    competidor = ensure_competidor_profile(g.user)
    total_competidores = Competidor.query.count()
    total_jogos = Jogo.query.count()
    jogos_realizados = Jogo.query.filter(Jogo.status.in_(["Encerrado", "Resultado LanÃ§ado", "Pontuado"])).count()
    jogos_pendentes = total_jogos - jogos_realizados
    
    # Palpites do usuÃ¡rio logado
    palpites_enviados = Palpite.query.filter_by(competidor_id=competidor.id, valido=True).count()

    # PrÃ³ximos jogos (nÃ£o iniciados, prÃ³ximos 10)
    hoje = date.today()
    proximos = (Jogo.query
                .filter(Jogo.data_jogo >= hoje)
                .filter(Jogo.status.in_(["Agendado", "Aberto para palpites"]))
                .order_by(Jogo.data_jogo, Jogo.hora_et)
                .limit(10).all())

    # PrÃ³ximo jogo
    proximo_jogo = proximos[0] if proximos else None

    # PrÃ³ximo prazo
    proximo_prazo = None
    if proximo_jogo:
        proximo_prazo = proximo_jogo.prazo_palpite

    # LÃ­der atual
    ranking = get_ranking(db, Competidor, Pontuacao, Palpite, Jogo)
    lider = ranking[0] if ranking else None

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
                           proximo_jogo=proximo_jogo,
                           proximo_prazo=proximo_prazo,
                           proximos_com_status=proximos_com_status)


# ---------------------------------------------------------------------------
# COMPETIDORES
# ---------------------------------------------------------------------------
@app.route("/competidores")
def listar_competidores():
    competidores = Competidor.query.order_by(Competidor.nome).all()
    return render_template("competidores/lista.html", competidores=competidores)


@app.route("/competidores/novo", methods=["GET", "POST"])
def novo_competidor():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        apelido = request.form.get("apelido", "").strip()
        if not nome:
            flash("Nome Ã© obrigatÃ³rio.", "danger")
            return render_template("competidores/form.html", competidor=None)
        if not apelido:
            flash("Apelido Ã© obrigatÃ³rio.", "danger")
            return render_template("competidores/form.html", competidor=None)
        if Competidor.query.filter_by(apelido=apelido).first():
            flash("Apelido jÃ¡ cadastrado. Escolha outro.", "danger")
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
def editar_competidor(cid):
    c = Competidor.query.get_or_404(cid)
    grupos = Grupo.query.order_by(Grupo.nome).all()
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        apelido = request.form.get("apelido", "").strip()
        if not nome:
            flash("Nome Ã© obrigatÃ³rio.", "danger")
            return render_template("competidores/form.html", competidor=c, grupos=grupos)
        if not apelido:
            flash("Apelido Ã© obrigatÃ³rio.", "danger")
            return render_template("competidores/form.html", competidor=c, grupos=grupos)
        dup = Competidor.query.filter_by(apelido=apelido).first()
        if dup and dup.id != c.id:
            flash("Apelido jÃ¡ cadastrado. Escolha outro.", "danger")
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
def inativar_competidor(cid):
    c = Competidor.query.get_or_404(cid)
    c.ativo = False
    c.updated_at = datetime.utcnow()
    db.session.commit()
    flash(f"{c.apelido} inativado.", "warning")
    return redirect(url_for("listar_competidores"))


@app.route("/competidores/<int:cid>/reativar", methods=["POST"])
def reativar_competidor(cid):
    c = Competidor.query.get_or_404(cid)
    c.ativo = True
    c.updated_at = datetime.utcnow()
    db.session.commit()
    flash(f"{c.apelido} reativado.", "success")
    return redirect(url_for("listar_competidores"))


@app.route("/competidores/<int:cid>/excluir", methods=["POST"])
def excluir_competidor(cid):
    c = Competidor.query.get_or_404(cid)
    if Palpite.query.filter_by(competidor_id=cid).count() > 0:
        flash("NÃ£o Ã© possÃ­vel excluir competidor com palpites vinculados. Use Inativar.", "danger")
        return redirect(url_for("listar_competidores"))
    db.session.delete(c)
    db.session.commit()
    flash("Competidor excluÃ­do.", "success")
    return redirect(url_for("listar_competidores"))


@app.route("/competidores/<int:cid>/historico")
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
    fase_filtro = request.args.get("fase", "")
    status_filtro = request.args.get("status", "")
    q = Jogo.query.order_by(Jogo.data_jogo, Jogo.hora_et)
    if fase_filtro:
        q = q.filter_by(fase=fase_filtro)
    if status_filtro:
        q = q.filter_by(status=status_filtro)
    jogos = q.all()
    fases = [r[0] for r in db.session.query(Jogo.fase).distinct().order_by(Jogo.fase).all()]
    status_list = ["Agendado", "Aberto para palpites", "Bloqueado para palpites",
                   "Em andamento", "Encerrado", "Resultado LanÃ§ado", "Pontuado", "Cancelado/Alterado"]
    return render_template("jogos/lista.html", jogos=jogos, fases=fases,
                           fase_filtro=fase_filtro, status_filtro=status_filtro,
                           status_list=status_list)


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
                   "Em andamento", "Encerrado", "Resultado LanÃ§ado", "Pontuado", "Cancelado/Alterado"]
    return render_template("jogos/form.html", jogo=j, status_list=status_list)


# ---------------------------------------------------------------------------
# PALPITES
# ---------------------------------------------------------------------------
@app.route("/palpites", methods=["GET", "POST"])
@login_required
def palpites():
    user = g.user
    
    # POST â€” salvar palpites (apenas do prÃ³prio usuÃ¡rio)
    if request.method == "POST":
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
                erros.append(f"Gols invÃ¡lidos para o jogo #{jid}.")
                continue

            if jogo.mata_mata and gols_a == gols_b and not classificado:
                erros.append(f"Classificado obrigatÃ³rio no mata-mata jogo #{jid} (empate).")
                continue

            if classificado and jogo.mata_mata:
                opcoes = [jogo.time_a.lower(), jogo.time_b.lower()]
                if classificado.lower() not in opcoes:
                    erros.append(f"Classificado invÃ¡lido para jogo #{jid}.")
                    continue

            # Buscar competidor do usuÃ¡rio logado
            competidor = ensure_competidor_profile(user)
            if not competidor:
                flash("UsuÃ¡rio nÃ£o tem perfil de competidor.", "danger")
                return redirect(url_for("dashboard"))

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

    # GET â€” listar jogos com palpites de todos do grupo
    filtro = request.args.get("filtro", "todos")
    fase_filtro_param = request.args.get("fase", "").strip()
    fase_filtro = fase_filtro_param
    grupo_filtro = request.args.get("grupo", "")
    selecao_filtro = request.args.get("selecao", "").strip()
    data_filtro = request.args.get("data", "")

    # Detectar fase automÃ¡tica se nÃ£o foi especificada
    if not fase_filtro:
        # Encontrar fase com jogos dentro do prazo
        fases_disponiveis = db.session.query(Jogo.fase).distinct().order_by(Jogo.fase).all()
        for (f,) in fases_disponiveis:
            jogos_fase = Jogo.query.filter_by(fase=f).all()
            jogos_abertos = [j for j in jogos_fase if prazo_aberto(j)]
            if jogos_abertos:
                fase_filtro = f  # Usa primeira fase com jogos abertos
                break
        else:
            # Se nenhuma fase tem jogo aberto, use a Ãºltima
            if fases_disponiveis:
                fase_filtro = fases_disponiveis[-1][0]

    query = Jogo.query.order_by(Jogo.data_jogo, Jogo.hora_et)
    if fase_filtro:
        query = query.filter_by(fase=fase_filtro)
    if grupo_filtro:
        query = query.filter_by(grupo=grupo_filtro)
    if selecao_filtro:
        query = query.filter(
            (Jogo.time_a.ilike(f"%{selecao_filtro}%")) |
            (Jogo.time_b.ilike(f"%{selecao_filtro}%"))
        )
    if data_filtro:
        try:
            data_obj = datetime.strptime(data_filtro, "%Y-%m-%d").date()
            query = query.filter_by(data_jogo=data_obj)
        except ValueError:
            pass

    todos_jogos = query.all()

    # Palpites do usuÃ¡rio logado
    competidor = ensure_competidor_profile(user)
    palpites_map = {}
    palpites_todos_usuarios = {}  # {jogo_id: {competidor_id: palpite}}
    
    if competidor:
        palpites_map = {p.jogo_id: p for p in
                        Palpite.query.filter_by(competidor_id=competidor.id, valido=True).all()}
    
    # Palpites de todos os usuÃ¡rios do grupo
    if user.grupo_id:
        usuarios_grupo = User.query.filter_by(grupo_id=user.grupo_id, ativo=True).all()
        competidores_grupo = [ensure_competidor_profile(u) for u in usuarios_grupo]
        competidores_grupo = [c for c in competidores_grupo if c]
        competidor_ids = [c.id for c in competidores_grupo]
        
        palpites_grupo = Palpite.query.filter(Palpite.competidor_id.in_(competidor_ids), Palpite.valido == True).all()
        for p in palpites_grupo:
            if p.jogo_id not in palpites_todos_usuarios:
                palpites_todos_usuarios[p.jogo_id] = {}
            palpites_todos_usuarios[p.jogo_id][p.competidor_id] = p

    # Carrega pontuacoes do competidor de uma vez para evitar N+1
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
        palpites_todos = palpites_todos_usuarios.get(j.id, {})
        jogos_com_status.append({
            "jogo": j,
            "palpite": p,
            "palpites_todos": palpites_todos,  # todos os palpites do grupo
            "prazo_aberto": aberto,
            "editavel": editavel,
            "status": st,
            "pontuacao": pont,
        })

    # Filtros de visualizaÃ§Ã£o
    if filtro == "abertos":
        jogos_com_status = [x for x in jogos_com_status if x["editavel"]]
    elif filtro == "enviados":
        jogos_com_status = [x for x in jogos_com_status if x["palpite"]]
    elif filtro == "sem_palpite":
        jogos_com_status = [x for x in jogos_com_status if not x["palpite"]]
    elif filtro == "bloqueados":
        jogos_com_status = [x for x in jogos_com_status if not x["editavel"]]

    fases = [r[0] for r in db.session.query(Jogo.fase).distinct().order_by(Jogo.fase).all()]
    grupos = [r[0] for r in db.session.query(Jogo.grupo).distinct().filter(Jogo.grupo.isnot(None)).order_by(Jogo.grupo).all()]

    return render_template("palpites/index.html",
                           jogos_com_status=jogos_com_status,
                           competidor=competidor,
                           user=user,
                           filtro=filtro,
                           fase_filtro=fase_filtro,
                           grupo_filtro=grupo_filtro,
                           selecao_filtro=selecao_filtro,
                           data_filtro=data_filtro,
                           fases=fases,
                           grupos=grupos)


# ---------------------------------------------------------------------------
# RESULTADOS (admin)
# ---------------------------------------------------------------------------
@app.route("/resultados")
def listar_resultados():
    fase_filtro = request.args.get("fase", "")
    filtro = request.args.get("filtro", "pendentes")
    query = Jogo.query.order_by(Jogo.data_jogo, Jogo.hora_et)
    if fase_filtro:
        query = query.filter_by(fase=fase_filtro)

    if filtro == "pendentes":
        # Jogos sem resultado lanÃ§ado mas cujo prazo jÃ¡ encerrou
        todos = query.all()
        jogos = [j for j in todos if not j.resultado and not prazo_aberto(j)]
    elif filtro == "encerrados":
        jogos = query.filter(Jogo.status.in_(["Encerrado", "Resultado LanÃ§ado", "Pontuado"])).all()
    else:
        jogos = query.all()

    fases = [r[0] for r in db.session.query(Jogo.fase).distinct().order_by(Jogo.fase).all()]
    return render_template("resultados/lista.html", jogos=jogos, fases=fases,
                           fase_filtro=fase_filtro, filtro=filtro)


@app.route("/resultados/<int:jid>", methods=["GET", "POST"])
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
            flash("Gols invÃ¡lidos.", "danger")
            return render_template("resultados/form.html", jogo=jogo, resultado=resultado)

        classificado = request.form.get("classificado", "").strip() or None
        if jogo.mata_mata and not classificado:
            flash("Classificado obrigatÃ³rio em mata-mata.", "danger")
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

        jogo.status = "Resultado LanÃ§ado"
        db.session.commit()

        # Recalcular pontuaÃ§Ã£o
        calcular_pontuacao_jogo(db, Palpite, Pontuacao, Resultado, jogo)
        flash("Resultado lanÃ§ado e pontuaÃ§Ã£o calculada!", "success")
        return redirect(url_for("listar_resultados"))

    return render_template("resultados/form.html", jogo=jogo, resultado=resultado)


@app.route("/resultados/<int:jid>/recalcular", methods=["POST"])
def recalcular_resultado(jid):
    jogo = Jogo.query.get_or_404(jid)
    calcular_pontuacao_jogo(db, Palpite, Pontuacao, Resultado, jogo)
    flash("PontuaÃ§Ã£o recalculada.", "success")
    return redirect(url_for("listar_resultados"))


def _run_auto_result_sync(launched_by: str):
    api_key = os.environ.get("FOOTBALL_DATA_API_KEY", "").strip()
    if not api_key:
        raise ValueError("FOOTBALL_DATA_API_KEY nÃ£o configurada.")

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
    except Exception as exc:
        flash(f"Falha na sincronizaÃ§Ã£o automÃ¡tica: {exc}", "danger")
        return redirect(url_for("listar_resultados"))

    flash(
        (
            "SincronizaÃ§Ã£o concluÃ­da: "
            f"{stats['fetched']} recebido(s), "
            f"{stats['created']} criado(s), "
            f"{stats['updated']} atualizado(s), "
            f"{stats['unchanged']} sem alteraÃ§Ã£o, "
            f"{stats['recalculated']} recalculado(s)."
        ),
        "success",
    )

    if stats["unmatched"]:
        exemplos = ", ".join(stats["unmatched"][:3])
        flash(
            f"Jogos nÃ£o mapeados automaticamente ({len(stats['unmatched'])}): {exemplos}",
            "warning",
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
        return jsonify({"ok": True, "stats": stats})
    except Exception as exc:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(exc)}), 500


# ---------------------------------------------------------------------------
# RANKING
# ---------------------------------------------------------------------------
@app.route("/ranking")
def ranking_geral():
    ranking = get_ranking(db, Competidor, Pontuacao, Palpite, Jogo)
    return render_template("ranking/geral.html", ranking=ranking)


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


# ---------------------------------------------------------------------------
# INIT & RUN
# ---------------------------------------------------------------------------
def create_app():
    with app.app_context():
        db.create_all()
        count = seed_jogos(db, Jogo)
        if count:
            print(f"[seed] {count} jogos carregados.")
        # Cria admin automÃ¡tico via variÃ¡veis de ambiente (Ãºtil em cloud)
        admin_email = os.environ.get("ADMIN_EMAIL")
        admin_senha = os.environ.get("ADMIN_PASSWORD")
        admin_nome = os.environ.get("ADMIN_NOME", "Administrador")
        admin_apelido = os.environ.get("ADMIN_APELIDO", "admin")
        if admin_email and admin_senha:
            existe = User.query.filter_by(eh_admin=True).first()
            if not existe:
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
# SIMULAÃ‡ÃƒO (admin)
# ---------------------------------------------------------------------------
@app.route("/admin/simulacao", methods=["GET", "POST"])
@admin_required
def simulacao():
    """Permite admin simular data futura para testar funcionalidades"""
    data_simulada = request.args.get("data_simulada", "")
    
    if request.method == "POST":
        acao = request.form.get("acao", "definir_data")
        data_str = request.form.get("data_simulada", "").strip()
        try:
            data_obj = datetime.strptime(data_str, "%Y-%m-%d").date()

            if acao == "gerar_resultados":
                # Cada simulacao comeca de um estado limpo para evitar ranking contaminado.
                Pontuacao.query.delete(synchronize_session=False)
                Resultado.query.delete(synchronize_session=False)

                for jogo in Jogo.query.all():
                    if jogo.data_jogo < data_obj:
                        jogo.status = "Encerrado"
                    else:
                        jogo.status = "Agendado"

                db.session.commit()

                jogos_ate_data = (
                    Jogo.query
                    .filter(Jogo.data_jogo <= data_obj)
                    .order_by(Jogo.data_jogo, Jogo.hora_et)
                    .all()
                )

                jogos_gerados = []
                for jogo in jogos_ate_data:
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
                    jogo.status = "Resultado LanÃ§ado"
                    jogos_gerados.append(jogo)

                db.session.commit()

                for jogo in jogos_gerados:
                    calcular_pontuacao_jogo(db, Palpite, Pontuacao, Resultado, jogo)

                flash(f"Simulacao refeita do zero: {len(jogos_gerados)} resultado(s) aleatorio(s) gerado(s) ate {data_str} e ranking recalculado.", "success")

            # Redireciona para GET com data_simulada como query param
            return redirect(url_for("simulacao", data_simulada=data_str))
        except ValueError:
            flash("Formato de data invÃ¡lido. Use YYYY-MM-DD.", "danger")
    
    # Carregar dados com data simulada
    info_simulacao = {
        "data_simulada": data_simulada,
        "data_real": date.today().isoformat(),
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
            
            # Jogos jÃ¡ realizados atÃ© essa data
            info_simulacao["jogos_realizados"] = (
                Jogo.query
                .filter(Jogo.data_jogo < data_obj)
                .count()
            )
            
            # PrÃ³ximo jogo apÃ³s essa data
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


