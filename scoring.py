"""
Lógica de pontuação e ranking do bolão.
"""
from datetime import datetime
import pytz

BR_TZ = pytz.timezone("America/Sao_Paulo")


def jogo_data_passada(jogo):
    """Retorna True quando a data do jogo ja passou em Brasilia."""
    if not jogo or not jogo.data_jogo:
        return True
    agora_br = datetime.now(BR_TZ)
    return jogo.data_jogo < agora_br.date()


def calcular_pontos(palpite_a, palpite_b, palpite_classificado,
                    real_a, real_b, real_classificado, mata_mata):
    """
    Retorna dict com pontos e indicadores detalhados.
    """
    result = {
        "pontos": 0,
        "placar_exato": False,
        "vencedor_correto": False,
        "saldo_correto": False,
        "gols_time_a_correto": False,
        "gols_time_b_correto": False,
        "classificado_correto": False,
    }

    if palpite_a is None or palpite_b is None:
        return result

    # Gols individuais
    result["gols_time_a_correto"] = palpite_a == real_a
    result["gols_time_b_correto"] = palpite_b == real_b

    # Placar exato
    if palpite_a == real_a and palpite_b == real_b:
        result["placar_exato"] = True
        result["pontos"] = 10
    else:
        # Vencedor
        vencedor_real = _vencedor(real_a, real_b)
        vencedor_palpite = _vencedor(palpite_a, palpite_b)
        result["vencedor_correto"] = vencedor_real == vencedor_palpite

        # Saldo
        saldo_real = real_a - real_b
        saldo_palpite = palpite_a - palpite_b
        result["saldo_correto"] = saldo_real == saldo_palpite

        if vencedor_real == vencedor_palpite:
            if vencedor_real == "empate":
                result["pontos"] = 5  # Empate mas placar diferente
            elif saldo_real == saldo_palpite:
                result["pontos"] = 7  # Acertou vencedor + saldo
            else:
                result["pontos"] = 5  # Acertou vencedor
        else:
            # Errou vencedor — checa gols individuais
            if result["gols_time_a_correto"] or result["gols_time_b_correto"]:
                result["pontos"] = 2

    # Classificado (mata-mata) — bônus cumulativo
    if mata_mata and real_classificado and palpite_classificado:
        if palpite_classificado.strip().lower() == real_classificado.strip().lower():
            result["classificado_correto"] = True
            result["pontos"] += 3

    return result


def _vencedor(a, b):
    if a > b:
        return "a"
    elif b > a:
        return "b"
    return "empate"


def calcular_pontuacao_jogo(db, Palpite, Pontuacao, Resultado, jogo):
    """Calcula/recalcula pontuação de todos os palpites de um jogo."""
    resultado = jogo.resultado
    if not resultado:
        return

    palpites = Palpite.query.filter_by(jogo_id=jogo.id, valido=True).all()
    for p in palpites:
        res = calcular_pontos(
            p.palpite_gols_a, p.palpite_gols_b, p.palpite_classificado,
            resultado.gols_a, resultado.gols_b, resultado.classificado,
            jogo.mata_mata
        )
        pont = Pontuacao.query.filter_by(competidor_id=p.competidor_id, jogo_id=jogo.id).first()
        if not pont:
            pont = Pontuacao(competidor_id=p.competidor_id, jogo_id=jogo.id)
            db.session.add(pont)
        pont.pontos = res["pontos"]
        pont.placar_exato = res["placar_exato"]
        pont.vencedor_correto = res["vencedor_correto"]
        pont.saldo_correto = res["saldo_correto"]
        pont.gols_time_a_correto = res["gols_time_a_correto"]
        pont.gols_time_b_correto = res["gols_time_b_correto"]
        pont.classificado_correto = res["classificado_correto"]

    jogo.status = "Pontuado"
    db.session.commit()


def _jogo_ids_por_etapa(Jogo, etapa=None, fase=None, team_code=None):
    if fase:
        return [j.id for j in Jogo.query.filter_by(fase=fase).all()]
    if etapa == "destaque" and team_code:
        team_code = team_code.strip().upper()
        return [
            j.id for j in Jogo.query.filter(
                (Jogo.sigla_time_a == team_code) | (Jogo.sigla_time_b == team_code)
            ).all()
        ]
    if etapa == "grupos":
        return [j.id for j in Jogo.query.filter_by(mata_mata=False).all()]
    if etapa == "mata_mata":
        return [j.id for j in Jogo.query.filter_by(mata_mata=True).all()]
    return None


def get_ranking(db, Competidor, Pontuacao, Palpite, Jogo, fase=None, etapa=None, team_code=None):
    """
    Retorna lista ordenada de dicts com o ranking dos competidores.
    Se fase for informado, filtra por fase.
    """
    return _get_ranking_bulk(db, Competidor, Pontuacao, Palpite, Jogo, fase=fase, etapa=etapa, team_code=team_code)

    competidores = Competidor.query.all()
    ranking = []
    jogo_ids_filtrados = _jogo_ids_por_etapa(Jogo, etapa=etapa, fase=fase, team_code=team_code)

    for c in competidores:
        query = db.session.query(Pontuacao).filter_by(competidor_id=c.id)
        palpite_query = db.session.query(Palpite).filter_by(competidor_id=c.id, valido=True)

        if jogo_ids_filtrados is not None:
            query = query.filter(Pontuacao.jogo_id.in_(jogo_ids_filtrados))
            palpite_query = palpite_query.filter(Palpite.jogo_id.in_(jogo_ids_filtrados))

        pontuacoes = query.all()
        palpites = palpite_query.all()

        total_pts = sum(p.pontos for p in pontuacoes)
        placares_exatos = sum(1 for p in pontuacoes if p.placar_exato)
        vencedores_corretos = sum(1 for p in pontuacoes if p.vencedor_correto)
        saldos_corretos = sum(1 for p in pontuacoes if p.saldo_correto)
        classificados_corretos = sum(1 for p in pontuacoes if p.classificado_correto)
        palpites_enviados = len(palpites)

        # Palpites não enviados = jogos já bloqueados/pontuados sem palpite
        jogos_encerrados = Jogo.query.filter(
            Jogo.status.in_(["Encerrado", "Resultado Lançado", "Pontuado"])
        )
        if jogo_ids_filtrados is not None:
            jogos_encerrados = jogos_encerrados.filter(Jogo.id.in_(jogo_ids_filtrados))
        jogos_ids_enc = {j.id for j in jogos_encerrados.all()}
        palpites_ids = {p.jogo_id for p in palpites}
        palpites_nao_enviados = len(jogos_ids_enc - palpites_ids)

        # Pontos máximos possíveis
        pts_max = 0
        for p in palpites:
            j = Jogo.query.get(p.jogo_id)
            if j:
                pts_max += 13 if j.mata_mata else 10

        aproveitamento = round((total_pts / pts_max * 100), 1) if pts_max > 0 else 0.0

        # Última pontuação (último jogo pontuado)
        ultima_pont = 0
        if pontuacoes:
            ultima = sorted(pontuacoes, key=lambda x: x.updated_at or x.created_at, reverse=True)[0]
            ultima_pont = ultima.pontos

        ranking.append({
            "competidor": c,
            "pontos": total_pts,
            "placares_exatos": placares_exatos,
            "vencedores_corretos": vencedores_corretos,
            "saldos_corretos": saldos_corretos,
            "classificados_corretos": classificados_corretos,
            "palpites_enviados": palpites_enviados,
            "palpites_nao_enviados": palpites_nao_enviados,
            "aproveitamento": aproveitamento,
            "ultima_pontuacao": ultima_pont,
        })

    # Ordenação pelos critérios de desempate
    ranking.sort(key=lambda x: (
        -x["pontos"],
        -x["placares_exatos"],
        -x["vencedores_corretos"],
        -x["saldos_corretos"],
        -x["classificados_corretos"],
        -x["palpites_enviados"],
        x["palpites_nao_enviados"],
        x["competidor"].apelido.lower(),
    ))

    for i, r in enumerate(ranking):
        r["posicao"] = i + 1

    return ranking


def _status_conta_como_encerrado(status):
    status = status or ""
    return status in {"Encerrado", "Pontuado"} or status.startswith("Resultado")


def _novo_resumo_ranking():
    return {
        "pontos": 0,
        "placares_exatos": 0,
        "vencedores_corretos": 0,
        "saldos_corretos": 0,
        "classificados_corretos": 0,
        "palpites_enviados": 0,
        "palpites_ids": set(),
        "pts_max": 0,
        "ultima_pontuacao": 0,
        "ultima_data": None,
    }


def _get_ranking_bulk(db, Competidor, Pontuacao, Palpite, Jogo, fase=None, etapa=None, team_code=None):
    competidores = Competidor.query.all()
    ranking = []
    jogo_ids_filtrados = _jogo_ids_por_etapa(Jogo, etapa=etapa, fase=fase, team_code=team_code)
    jogo_ids_set = set(jogo_ids_filtrados) if jogo_ids_filtrados is not None else None

    jogos_query = Jogo.query.with_entities(Jogo.id, Jogo.mata_mata, Jogo.status)
    if jogo_ids_set is not None:
        jogos_query = jogos_query.filter(Jogo.id.in_(jogo_ids_set))
    jogos_info = {
        row.id: {"mata_mata": row.mata_mata, "status": row.status}
        for row in jogos_query.all()
    }
    jogos_ids_encerrados = {
        jogo_id
        for jogo_id, info in jogos_info.items()
        if _status_conta_como_encerrado(info["status"])
    }

    resumos = {c.id: _novo_resumo_ranking() for c in competidores}

    pontuacoes_query = Pontuacao.query
    if jogo_ids_set is not None:
        pontuacoes_query = pontuacoes_query.filter(Pontuacao.jogo_id.in_(jogo_ids_set))

    for pontuacao in pontuacoes_query.all():
        resumo = resumos.get(pontuacao.competidor_id)
        if resumo is None:
            continue

        resumo["pontos"] += pontuacao.pontos or 0
        resumo["placares_exatos"] += 1 if pontuacao.placar_exato else 0
        resumo["vencedores_corretos"] += 1 if pontuacao.vencedor_correto else 0
        resumo["saldos_corretos"] += 1 if pontuacao.saldo_correto else 0
        resumo["classificados_corretos"] += 1 if pontuacao.classificado_correto else 0

        data_ref = pontuacao.updated_at or pontuacao.created_at
        if resumo["ultima_data"] is None or (data_ref and data_ref > resumo["ultima_data"]):
            resumo["ultima_data"] = data_ref
            resumo["ultima_pontuacao"] = pontuacao.pontos or 0

    palpites_query = Palpite.query.filter_by(valido=True)
    if jogo_ids_set is not None:
        palpites_query = palpites_query.filter(Palpite.jogo_id.in_(jogo_ids_set))

    for palpite in palpites_query.all():
        resumo = resumos.get(palpite.competidor_id)
        if resumo is None:
            continue

        resumo["palpites_enviados"] += 1
        resumo["palpites_ids"].add(palpite.jogo_id)
        jogo_info = jogos_info.get(palpite.jogo_id)
        if jogo_info:
            resumo["pts_max"] += 13 if jogo_info["mata_mata"] else 10

    for c in competidores:
        resumo = resumos[c.id]
        palpites_nao_enviados = len(jogos_ids_encerrados - resumo["palpites_ids"])
        aproveitamento = (
            round((resumo["pontos"] / resumo["pts_max"] * 100), 1)
            if resumo["pts_max"] > 0
            else 0.0
        )

        ranking.append({
            "competidor": c,
            "pontos": resumo["pontos"],
            "placares_exatos": resumo["placares_exatos"],
            "vencedores_corretos": resumo["vencedores_corretos"],
            "saldos_corretos": resumo["saldos_corretos"],
            "classificados_corretos": resumo["classificados_corretos"],
            "palpites_enviados": resumo["palpites_enviados"],
            "palpites_nao_enviados": palpites_nao_enviados,
            "aproveitamento": aproveitamento,
            "ultima_pontuacao": resumo["ultima_pontuacao"],
        })

    ranking.sort(key=lambda x: (
        -x["pontos"],
        -x["placares_exatos"],
        -x["vencedores_corretos"],
        -x["saldos_corretos"],
        -x["classificados_corretos"],
        -x["palpites_enviados"],
        x["palpites_nao_enviados"],
        x["competidor"].apelido.lower(),
    ))

    for i, r in enumerate(ranking):
        r["posicao"] = i + 1

    return ranking


def prazo_aberto(jogo):
    """Retorna True se o prazo de palpite ainda está aberto."""
    if not jogo.prazo_palpite:
        return False
    if jogo_data_passada(jogo):
        return False
    BR_TZ_local = pytz.timezone("America/Sao_Paulo")
    agora_br = datetime.now(BR_TZ_local)
    prazo = jogo.prazo_palpite
    if prazo.tzinfo is None:
        prazo = BR_TZ_local.localize(prazo)
    else:
        prazo = prazo.astimezone(BR_TZ_local)
    return agora_br <= prazo


def palpite_editavel(jogo):
    """Retorna True somente para jogos ainda editaveis."""
    return not jogo_data_passada(jogo) and prazo_aberto(jogo)


def status_palpite_para_jogo(jogo, palpite):
    """Retorna texto de status do palpite de um competidor para um jogo."""
    if jogo.status == "Pontuado":
        return "Pontuado"
    if jogo.status in ("Resultado Lançado",):
        return "Resultado Lançado"
    if not prazo_aberto(jogo):
        if palpite:
            return "Bloqueado"
        return "Bloqueado sem palpite"
    if palpite:
        return "Palpite enviado"
    return "Aberto para palpite"
