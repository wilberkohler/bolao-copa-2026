"""
Carga inicial dos jogos da Copa do Mundo FIFA 2026.
Horários em ET (Eastern Time). Conversão para Brasília: ET + 1h (EDT) ou ET + 2h (EST).
A Copa ocorre de 11/06 a 19/07/2026 — período de horário de verão americano (EDT, UTC-4).
Brasília é UTC-3, portanto Brasília = ET + 1h durante todo o torneio.
"""
from datetime import datetime, date, timedelta
import pytz

ET_TZ = pytz.timezone("America/New_York")
BR_TZ = pytz.timezone("America/Sao_Paulo")


def et_to_brasilia(data: date, hora_et_str: str) -> str:
    """Converte horário ET para Brasília e retorna string HH:MM."""
    h, m = map(int, hora_et_str.split(":"))
    dt_et = ET_TZ.localize(datetime(data.year, data.month, data.day, h, m))
    dt_br = dt_et.astimezone(BR_TZ)
    return dt_br.strftime("%H:%M")


def calcular_prazo_palpite(data_jogo: date, hora_et_str: str) -> datetime:
    """Prazo = 23h59 de Brasília do dia anterior ao jogo."""
    h, m = map(int, hora_et_str.split(":"))
    dt_et = ET_TZ.localize(datetime(data_jogo.year, data_jogo.month, data_jogo.day, h, m))
    dt_br = dt_et.astimezone(BR_TZ)
    dia_anterior = dt_br.date() - timedelta(days=1)
    prazo_br = BR_TZ.localize(datetime(dia_anterior.year, dia_anterior.month, dia_anterior.day, 23, 59))
    return prazo_br


# ---------------------------------------------------------------------------
# Dados dos jogos: (numero_partida, fase, grupo, rodada, data_str, hora_et,
#                   time_a, time_b, sigla_a, sigla_b, estadio, cidade, pais, mata_mata)
# ---------------------------------------------------------------------------
JOGOS = [
    # ===== FASE DE GRUPOS =====
    # Grupo A
    (1, "Fase de Grupos", "A", 1, "2026-06-11", "17:00", "México", "África do Sul", "MEX", "RSA", "SoFi Stadium", "Los Angeles", "EUA", False),
    (2, "Fase de Grupos", "A", 1, "2026-06-11", "20:00", "Argentina", "Argélia", "ARG", "ALG", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", False),
    (3, "Fase de Grupos", "A", 2, "2026-06-15", "17:00", "Argentina", "África do Sul", "ARG", "RSA", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", False),
    (4, "Fase de Grupos", "A", 2, "2026-06-15", "20:00", "México", "Argélia", "MEX", "ALG", "AT&T Stadium", "Dallas", "EUA", False),
    (5, "Fase de Grupos", "A", 3, "2026-06-19", "18:00", "México", "Argentina", "MEX", "ARG", "AT&T Stadium", "Dallas", "EUA", False),
    (6, "Fase de Grupos", "A", 3, "2026-06-19", "18:00", "África do Sul", "Argélia", "RSA", "ALG", "SoFi Stadium", "Los Angeles", "EUA", False),

    # Grupo B
    (7, "Fase de Grupos", "B", 1, "2026-06-12", "14:00", "Espanha", "Cabo Verde", "ESP", "CPV", "Levi's Stadium", "San Francisco/Bay Area", "EUA", False),
    (8, "Fase de Grupos", "B", 1, "2026-06-12", "17:00", "Portugal", "Congo DR", "POR", "COD", "SoFi Stadium", "Los Angeles", "EUA", False),
    (9, "Fase de Grupos", "B", 2, "2026-06-16", "14:00", "Espanha", "Congo DR", "ESP", "COD", "Levi's Stadium", "San Francisco/Bay Area", "EUA", False),
    (10, "Fase de Grupos", "B", 2, "2026-06-16", "17:00", "Portugal", "Cabo Verde", "POR", "CPV", "SoFi Stadium", "Los Angeles", "EUA", False),
    (11, "Fase de Grupos", "B", 3, "2026-06-20", "18:00", "Espanha", "Portugal", "ESP", "POR", "Levi's Stadium", "San Francisco/Bay Area", "EUA", False),
    (12, "Fase de Grupos", "B", 3, "2026-06-20", "18:00", "Cabo Verde", "Congo DR", "CPV", "COD", "SoFi Stadium", "Los Angeles", "EUA", False),

    # Grupo C
    (13, "Fase de Grupos", "C", 1, "2026-06-12", "20:00", "Estados Unidos", "Paraguai", "USA", "PAR", "SoFi Stadium", "Los Angeles", "EUA", False),
    (14, "Fase de Grupos", "C", 1, "2026-06-13", "14:00", "Uruguai", "Angola", "URU", "ANG", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", False),
    (15, "Fase de Grupos", "C", 2, "2026-06-17", "20:00", "Estados Unidos", "Angola", "USA", "ANG", "AT&T Stadium", "Dallas", "EUA", False),
    (16, "Fase de Grupos", "C", 2, "2026-06-17", "17:00", "Uruguai", "Paraguai", "URU", "PAR", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", False),
    (17, "Fase de Grupos", "C", 3, "2026-06-21", "18:00", "Estados Unidos", "Uruguai", "USA", "URU", "SoFi Stadium", "Los Angeles", "EUA", False),
    (18, "Fase de Grupos", "C", 3, "2026-06-21", "18:00", "Paraguai", "Angola", "PAR", "ANG", "AT&T Stadium", "Dallas", "EUA", False),

    # Grupo D
    (19, "Fase de Grupos", "D", 1, "2026-06-13", "17:00", "Brasil", "Marrocos", "BRA", "MAR", "AT&T Stadium", "Dallas", "EUA", False),
    (20, "Fase de Grupos", "D", 1, "2026-06-13", "20:00", "Japão", "Croácia", "JPN", "CRO", "SoFi Stadium", "Los Angeles", "EUA", False),
    (21, "Fase de Grupos", "D", 2, "2026-06-17", "14:00", "Brasil", "Croácia", "BRA", "CRO", "AT&T Stadium", "Dallas", "EUA", False),
    (22, "Fase de Grupos", "D", 2, "2026-06-18", "14:00", "Japão", "Marrocos", "JPN", "MAR", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", False),
    (23, "Fase de Grupos", "D", 3, "2026-06-22", "18:00", "Brasil", "Japão", "BRA", "JPN", "SoFi Stadium", "Los Angeles", "EUA", False),
    (24, "Fase de Grupos", "D", 3, "2026-06-22", "18:00", "Marrocos", "Croácia", "MAR", "CRO", "AT&T Stadium", "Dallas", "EUA", False),

    # Grupo E
    (25, "Fase de Grupos", "E", 1, "2026-06-13", "11:00", "Alemanha", "Curaçao", "GER", "CUW", "Levi's Stadium", "San Francisco/Bay Area", "EUA", False),
    (26, "Fase de Grupos", "E", 1, "2026-06-14", "14:00", "Chile", "Austrália", "CHI", "AUS", "AT&T Stadium", "Dallas", "EUA", False),
    (27, "Fase de Grupos", "E", 2, "2026-06-18", "17:00", "Alemanha", "Austrália", "GER", "AUS", "Levi's Stadium", "San Francisco/Bay Area", "EUA", False),
    (28, "Fase de Grupos", "E", 2, "2026-06-18", "20:00", "Chile", "Curaçao", "CHI", "CUW", "SoFi Stadium", "Los Angeles", "EUA", False),
    (29, "Fase de Grupos", "E", 3, "2026-06-22", "18:00", "Alemanha", "Chile", "GER", "CHI", "AT&T Stadium", "Dallas", "EUA", False),
    (30, "Fase de Grupos", "E", 3, "2026-06-22", "18:00", "Curaçao", "Austrália", "CUW", "AUS", "Levi's Stadium", "San Francisco/Bay Area", "EUA", False),

    # Grupo F
    (31, "Fase de Grupos", "F", 1, "2026-06-14", "11:00", "França", "Senegal", "FRA", "SEN", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", False),
    (32, "Fase de Grupos", "F", 1, "2026-06-14", "20:00", "Bélgica", "Equador", "BEL", "ECU", "AT&T Stadium", "Dallas", "EUA", False),
    (33, "Fase de Grupos", "F", 2, "2026-06-18", "11:00", "França", "Equador", "FRA", "ECU", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", False),
    (34, "Fase de Grupos", "F", 2, "2026-06-19", "14:00", "Bélgica", "Senegal", "BEL", "SEN", "AT&T Stadium", "Dallas", "EUA", False),
    (35, "Fase de Grupos", "F", 3, "2026-06-23", "18:00", "França", "Bélgica", "FRA", "BEL", "SoFi Stadium", "Los Angeles", "EUA", False),
    (36, "Fase de Grupos", "F", 3, "2026-06-23", "18:00", "Senegal", "Equador", "SEN", "ECU", "Levi's Stadium", "San Francisco/Bay Area", "EUA", False),

    # Grupo G
    (37, "Fase de Grupos", "G", 1, "2026-06-14", "17:00", "Inglaterra", "Sérvia", "ENG", "SRB", "AT&T Stadium", "Dallas", "EUA", False),
    (38, "Fase de Grupos", "G", 1, "2026-06-15", "14:00", "Holanda", "Japão", "NED", "JPN", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", False),
    (39, "Fase de Grupos", "G", 2, "2026-06-19", "17:00", "Inglaterra", "Japão", "ENG", "JPN", "AT&T Stadium", "Dallas", "EUA", False),
    (40, "Fase de Grupos", "G", 2, "2026-06-19", "20:00", "Holanda", "Sérvia", "NED", "SRB", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", False),
    (41, "Fase de Grupos", "G", 3, "2026-06-23", "18:00", "Inglaterra", "Holanda", "ENG", "NED", "SoFi Stadium", "Los Angeles", "EUA", False),
    (42, "Fase de Grupos", "G", 3, "2026-06-23", "18:00", "Sérvia", "Japão", "SRB", "JPN", "AT&T Stadium", "Dallas", "EUA", False),

    # Grupo H
    (43, "Fase de Grupos", "H", 1, "2026-06-15", "11:00", "Portugal", "Zimbábue", "POR", "ZIM", "Levi's Stadium", "San Francisco/Bay Area", "EUA", False),
    (44, "Fase de Grupos", "H", 1, "2026-06-15", "20:00", "Colômbia", "Nova Zelândia", "COL", "NZL", "AT&T Stadium", "Dallas", "EUA", False),
    (45, "Fase de Grupos", "H", 2, "2026-06-20", "14:00", "Colômbia", "Zimbábue", "COL", "ZIM", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", False),
    (46, "Fase de Grupos", "H", 2, "2026-06-20", "11:00", "Portugal", "Nova Zelândia", "POR", "NZL", "Levi's Stadium", "San Francisco/Bay Area", "EUA", False),
    (47, "Fase de Grupos", "H", 3, "2026-06-24", "18:00", "Portugal", "Colômbia", "POR", "COL", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", False),
    (48, "Fase de Grupos", "H", 3, "2026-06-24", "18:00", "Zimbábue", "Nova Zelândia", "ZIM", "NZL", "Levi's Stadium", "San Francisco/Bay Area", "EUA", False),

    # Grupo I
    (49, "Fase de Grupos", "I", 1, "2026-06-15", "17:00", "Itália", "Cazaquistão", "ITA", "KAZ", "SoFi Stadium", "Los Angeles", "EUA", False),
    (50, "Fase de Grupos", "I", 1, "2026-06-16", "11:00", "Dinamarca", "Arábia Saudita", "DEN", "KSA", "Levi's Stadium", "San Francisco/Bay Area", "EUA", False),
    (51, "Fase de Grupos", "I", 2, "2026-06-20", "17:00", "Itália", "Arábia Saudita", "ITA", "KSA", "SoFi Stadium", "Los Angeles", "EUA", False),
    (52, "Fase de Grupos", "I", 2, "2026-06-20", "20:00", "Dinamarca", "Cazaquistão", "DEN", "KAZ", "AT&T Stadium", "Dallas", "EUA", False),
    (53, "Fase de Grupos", "I", 3, "2026-06-24", "18:00", "Itália", "Dinamarca", "ITA", "DEN", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", False),
    (54, "Fase de Grupos", "I", 3, "2026-06-24", "18:00", "Cazaquistão", "Arábia Saudita", "KAZ", "KSA", "AT&T Stadium", "Dallas", "EUA", False),

    # Grupo J
    (55, "Fase de Grupos", "J", 1, "2026-06-16", "20:00", "Canadá", "Bósnia e Herzegovina", "CAN", "BIH", "AT&T Stadium", "Dallas", "EUA", False),
    (56, "Fase de Grupos", "J", 1, "2026-06-16", "14:00", "Suíça", "Malaui", "SUI", "MWI", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", False),
    (57, "Fase de Grupos", "J", 2, "2026-06-21", "14:00", "Canadá", "Malaui", "CAN", "MWI", "AT&T Stadium", "Dallas", "EUA", False),
    (58, "Fase de Grupos", "J", 2, "2026-06-21", "11:00", "Suíça", "Bósnia e Herzegovina", "SUI", "BIH", "Levi's Stadium", "San Francisco/Bay Area", "EUA", False),
    (59, "Fase de Grupos", "J", 3, "2026-06-25", "18:00", "Canadá", "Suíça", "CAN", "SUI", "SoFi Stadium", "Los Angeles", "EUA", False),
    (60, "Fase de Grupos", "J", 3, "2026-06-25", "18:00", "Bósnia e Herzegovina", "Malaui", "BIH", "MWI", "AT&T Stadium", "Dallas", "EUA", False),

    # Grupo K
    (61, "Fase de Grupos", "K", 1, "2026-06-17", "11:00", "Coreia do Sul", "Filipinas", "KOR", "PHI", "Levi's Stadium", "San Francisco/Bay Area", "EUA", False),
    (62, "Fase de Grupos", "K", 1, "2026-06-17", "20:00", "México", "Costa Rica", "MEX", "CRC", "AT&T Stadium", "Dallas", "EUA", False),
    (63, "Fase de Grupos", "K", 2, "2026-06-22", "14:00", "Coreia do Sul", "Costa Rica", "KOR", "CRC", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", False),
    (64, "Fase de Grupos", "K", 2, "2026-06-22", "11:00", "México", "Filipinas", "MEX", "PHI", "Levi's Stadium", "San Francisco/Bay Area", "EUA", False),
    (65, "Fase de Grupos", "K", 3, "2026-06-26", "18:00", "Coreia do Sul", "México", "KOR", "MEX", "SoFi Stadium", "Los Angeles", "EUA", False),
    (66, "Fase de Grupos", "K", 3, "2026-06-26", "18:00", "Filipinas", "Costa Rica", "PHI", "CRC", "AT&T Stadium", "Dallas", "EUA", False),

    # Grupo L
    (67, "Fase de Grupos", "L", 1, "2026-06-18", "14:00", "Haiti", "Escócia", "HAI", "SCO", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", False),
    (68, "Fase de Grupos", "L", 1, "2026-06-18", "20:00", "Turquia", "Venezuela", "TUR", "VEN", "SoFi Stadium", "Los Angeles", "EUA", False),
    (69, "Fase de Grupos", "L", 2, "2026-06-23", "14:00", "Haiti", "Venezuela", "HAI", "VEN", "AT&T Stadium", "Dallas", "EUA", False),
    (70, "Fase de Grupos", "L", 2, "2026-06-23", "11:00", "Turquia", "Escócia", "TUR", "SCO", "Levi's Stadium", "San Francisco/Bay Area", "EUA", False),
    (71, "Fase de Grupos", "L", 3, "2026-06-27", "18:00", "Haiti", "Turquia", "HAI", "TUR", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", False),
    (72, "Fase de Grupos", "L", 3, "2026-06-27", "18:00", "Escócia", "Venezuela", "SCO", "VEN", "SoFi Stadium", "Los Angeles", "EUA", False),

    # ===== RODADA DE 32 (mata-mata) =====
    (73, "Rodada de 32", None, 1, "2026-06-29", "14:00", "1º Grupo A", "3º melhor", "1A", "3X", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", True),
    (74, "Rodada de 32", None, 1, "2026-06-29", "18:00", "1º Grupo C", "3º melhor", "1C", "3X", "AT&T Stadium", "Dallas", "EUA", True),
    (75, "Rodada de 32", None, 1, "2026-06-29", "22:00", "2º Grupo A", "2º Grupo B", "2A", "2B", "SoFi Stadium", "Los Angeles", "EUA", True),
    (76, "Rodada de 32", None, 1, "2026-06-30", "14:00", "1º Grupo B", "3º melhor", "1B", "3X", "Levi's Stadium", "San Francisco/Bay Area", "EUA", True),
    (77, "Rodada de 32", None, 1, "2026-06-30", "18:00", "1º Grupo D", "3º melhor", "1D", "3X", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", True),
    (78, "Rodada de 32", None, 1, "2026-06-30", "22:00", "2º Grupo C", "2º Grupo D", "2C", "2D", "AT&T Stadium", "Dallas", "EUA", True),
    (79, "Rodada de 32", None, 1, "2026-07-01", "14:00", "1º Grupo E", "3º melhor", "1E", "3X", "SoFi Stadium", "Los Angeles", "EUA", True),
    (80, "Rodada de 32", None, 1, "2026-07-01", "18:00", "1º Grupo G", "3º melhor", "1G", "3X", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", True),
    (81, "Rodada de 32", None, 1, "2026-07-01", "22:00", "2º Grupo E", "2º Grupo F", "2E", "2F", "Levi's Stadium", "San Francisco/Bay Area", "EUA", True),
    (82, "Rodada de 32", None, 1, "2026-07-02", "14:00", "1º Grupo F", "3º melhor", "1F", "3X", "AT&T Stadium", "Dallas", "EUA", True),
    (83, "Rodada de 32", None, 1, "2026-07-02", "18:00", "1º Grupo H", "3º melhor", "1H", "3X", "SoFi Stadium", "Los Angeles", "EUA", True),
    (84, "Rodada de 32", None, 1, "2026-07-02", "22:00", "2º Grupo G", "2º Grupo H", "2G", "2H", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", True),
    (85, "Rodada de 32", None, 1, "2026-07-03", "14:00", "1º Grupo I", "3º melhor", "1I", "3X", "Levi's Stadium", "San Francisco/Bay Area", "EUA", True),
    (86, "Rodada de 32", None, 1, "2026-07-03", "18:00", "1º Grupo K", "3º melhor", "1K", "3X", "AT&T Stadium", "Dallas", "EUA", True),
    (87, "Rodada de 32", None, 1, "2026-07-03", "22:00", "2º Grupo I", "2º Grupo J", "2I", "2J", "SoFi Stadium", "Los Angeles", "EUA", True),
    (88, "Rodada de 32", None, 1, "2026-07-04", "14:00", "1º Grupo J", "3º melhor", "1J", "3X", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", True),
    (89, "Rodada de 32", None, 1, "2026-07-04", "18:00", "1º Grupo L", "3º melhor", "1L", "3X", "AT&T Stadium", "Dallas", "EUA", True),
    (90, "Rodada de 32", None, 1, "2026-07-04", "22:00", "2º Grupo K", "2º Grupo L", "2K", "2L", "SoFi Stadium", "Los Angeles", "EUA", True),

    # ===== OITAVAS DE FINAL =====
    (91, "Oitavas de Final", None, 1, "2026-07-06", "14:00", "Vencedor J73", "Vencedor J74", "WJ73", "WJ74", "Levi's Stadium", "San Francisco/Bay Area", "EUA", True),
    (92, "Oitavas de Final", None, 1, "2026-07-06", "20:00", "Vencedor J75", "Vencedor J76", "WJ75", "WJ76", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", True),
    (93, "Oitavas de Final", None, 1, "2026-07-07", "14:00", "Vencedor J77", "Vencedor J78", "WJ77", "WJ78", "AT&T Stadium", "Dallas", "EUA", True),
    (94, "Oitavas de Final", None, 1, "2026-07-07", "20:00", "Vencedor J79", "Vencedor J80", "WJ79", "WJ80", "SoFi Stadium", "Los Angeles", "EUA", True),
    (95, "Oitavas de Final", None, 1, "2026-07-08", "14:00", "Vencedor J81", "Vencedor J82", "WJ81", "WJ82", "Levi's Stadium", "San Francisco/Bay Area", "EUA", True),
    (96, "Oitavas de Final", None, 1, "2026-07-08", "20:00", "Vencedor J83", "Vencedor J84", "WJ83", "WJ84", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", True),
    (97, "Oitavas de Final", None, 1, "2026-07-09", "14:00", "Vencedor J85", "Vencedor J86", "WJ85", "WJ86", "AT&T Stadium", "Dallas", "EUA", True),
    (98, "Oitavas de Final", None, 1, "2026-07-09", "20:00", "Vencedor J87", "Vencedor J88", "WJ87", "WJ88", "SoFi Stadium", "Los Angeles", "EUA", True),
    # partida 89-90
    (99,  "Oitavas de Final", None, 1, "2026-07-10", "14:00", "Vencedor J89", "Vencedor J90", "WJ89", "WJ90", "Levi's Stadium", "San Francisco/Bay Area", "EUA", True),

    # ===== QUARTAS DE FINAL =====
    (100, "Quartas de Final", None, 1, "2026-07-12", "14:00", "Vencedor Q1", "Vencedor Q2", "WQ1", "WQ2", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", True),
    (101, "Quartas de Final", None, 1, "2026-07-12", "20:00", "Vencedor Q3", "Vencedor Q4", "WQ3", "WQ4", "AT&T Stadium", "Dallas", "EUA", True),
    (102, "Quartas de Final", None, 1, "2026-07-13", "14:00", "Vencedor Q5", "Vencedor Q6", "WQ5", "WQ6", "SoFi Stadium", "Los Angeles", "EUA", True),
    (103, "Quartas de Final", None, 1, "2026-07-13", "20:00", "Vencedor Q7", "Vencedor Q8", "WQ7", "WQ8", "Levi's Stadium", "San Francisco/Bay Area", "EUA", True),

    # ===== SEMIFINAIS =====
    (104, "Semifinal", None, 1, "2026-07-15", "20:00", "Vencedor QF1", "Vencedor QF2", "WSF1", "WSF2", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", True),
    (105, "Semifinal", None, 1, "2026-07-16", "20:00", "Vencedor QF3", "Vencedor QF4", "WSF3", "WSF4", "AT&T Stadium", "Dallas", "EUA", True),

    # ===== DISPUTA DE TERCEIRO LUGAR =====
    (106, "Terceiro Lugar", None, 1, "2026-07-18", "15:00", "Perdedor SF1", "Perdedor SF2", "LSF1", "LSF2", "SoFi Stadium", "Los Angeles", "EUA", True),

    # ===== FINAL =====
    (107, "Final", None, 1, "2026-07-19", "15:00", "Vencedor SF1", "Vencedor SF2", "WSF1", "WSF2", "MetLife Stadium", "Nova York/Nova Jersey", "EUA", True),
]


def seed_jogos(db, Jogo):
    """Insere todos os jogos caso a tabela esteja vazia."""
    if Jogo.query.count() > 0:
        return 0
    count = 0
    for row in JOGOS:
        (num, fase, grupo, rodada, data_str, hora_et,
         time_a, time_b, sigla_a, sigla_b,
         estadio, cidade, pais, mata_mata) = row

        data_jogo = datetime.strptime(data_str, "%Y-%m-%d").date()
        hora_br = et_to_brasilia(data_jogo, hora_et)
        prazo = calcular_prazo_palpite(data_jogo, hora_et)

        jogo = Jogo(
            numero_partida=num,
            fase=fase,
            grupo=grupo,
            rodada=rodada,
            data_jogo=data_jogo,
            hora_et=hora_et,
            timezone_original="America/New_York",
            hora_brasilia=hora_br,
            timezone_exibicao="America/Sao_Paulo",
            time_a=time_a,
            time_b=time_b,
            sigla_time_a=sigla_a,
            sigla_time_b=sigla_b,
            estadio=estadio,
            cidade=cidade,
            pais=pais,
            mata_mata=mata_mata,
            prazo_palpite=prazo,
            status="Agendado",
        )
        db.session.add(jogo)
        count += 1
    db.session.commit()
    return count
