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
            if saldo_real == saldo_palpite:
                result["pontos"] = 7  # Acertou vencedor + saldo
            else:
                if vencedor_real == "empate":
                    result["pontos"] = 5  # Empate mas placar diferente
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


def get_ranking(db, Competidor, Pontuacao, Palpite, Jogo, fase=None):
    """
    Retorna lista ordenada de dicts com o ranking dos competidores.
    Se fase for informado, filtra por fase.
    """
    competidores = Competidor.query.all()
    ranking = []

    for c in competidores:
        query = db.session.query(Pontuacao).filter_by(competidor_id=c.id)
        palpite_query = db.session.query(Palpite).filter_by(competidor_id=c.id, valido=True)

        if fase:
            jogo_ids = [j.id for j in Jogo.query.filter_by(fase=fase).all()]
            query = query.filter(Pontuacao.jogo_id.in_(jogo_ids))
            palpite_query = palpite_query.filter(Palpite.jogo_id.in_(jogo_ids))

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
        if fase:
            jogos_encerrados = jogos_encerrados.filter_by(fase=fase)
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
