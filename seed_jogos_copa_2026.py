"""
Carga inicial e sincronizacao dos jogos do Mundial de Futebol 2026.

Dados de partidas baseados no calendario publicado em 2026, com horarios
armazenados em ET (America/New_York) e exibicao em Brasilia.
"""
from datetime import datetime, date, timedelta
import pytz

ET_TZ = pytz.timezone("America/New_York")
BR_TZ = pytz.timezone("America/Sao_Paulo")


def et_to_brasilia(data: date, hora_et_str: str) -> str:
    """Converte horario ET para Brasilia e retorna string HH:MM."""
    h, m = map(int, hora_et_str.split(":"))
    dt_et = ET_TZ.localize(datetime(data.year, data.month, data.day, h, m))
    dt_br = dt_et.astimezone(BR_TZ)
    return dt_br.strftime("%H:%M")


def calcular_prazo_palpite(data_jogo: date, hora_et_str: str) -> datetime:
    """Prazo = 30 minutos antes do jogo, salvo como horario naive em Brasilia."""
    h, m = map(int, hora_et_str.split(":"))
    dt_et = ET_TZ.localize(datetime(data_jogo.year, data_jogo.month, data_jogo.day, h, m))
    dt_br = dt_et.astimezone(BR_TZ)
    prazo_br = dt_br - timedelta(minutes=30)
    return prazo_br.replace(tzinfo=None)


# Dados dos jogos: (numero_partida, fase, grupo, rodada, data_str, hora_et,
#                   time_a, time_b, sigla_a, sigla_b, estadio, cidade, pais, mata_mata)
JOGOS = [
    (1, 'Fase de Grupos', 'A', 1, '2026-06-11', '15:00', 'México', 'África do Sul', 'MEX', 'RSA', 'Estadio Azteca', 'Mexico City', 'México', False),
    (2, 'Fase de Grupos', 'A', 1, '2026-06-11', '22:00', 'Coreia do Sul', 'Tchéquia', 'KOR', 'CZE', 'Estadio Akron', 'Guadalajara', 'México', False),
    (3, 'Fase de Grupos', 'B', 1, '2026-06-12', '15:00', 'Canadá', 'Bósnia e Herzegovina', 'CAN', 'BIH', 'BMO Field', 'Toronto', 'Canadá', False),
    (4, 'Fase de Grupos', 'D', 1, '2026-06-12', '21:00', 'Estados Unidos', 'Paraguai', 'USA', 'PAR', 'SoFi Stadium', 'Los Angeles', 'EUA', False),
    (5, 'Fase de Grupos', 'C', 1, '2026-06-13', '21:00', 'Haiti', 'Escócia', 'HAI', 'SCO', 'Gillette Stadium', 'Boston', 'EUA', False),
    (6, 'Fase de Grupos', 'D', 1, '2026-06-14', '00:00', 'Austrália', 'Turquia', 'AUS', 'TUR', 'BC Place', 'Vancouver', 'Canadá', False),
    (7, 'Fase de Grupos', 'C', 1, '2026-06-13', '18:00', 'Brasil', 'Marrocos', 'BRA', 'MAR', 'MetLife Stadium', 'New York/New Jersey', 'EUA', False),
    (8, 'Fase de Grupos', 'B', 1, '2026-06-13', '15:00', 'Catar', 'Suíça', 'QAT', 'SUI', "Levi's Stadium", 'San Francisco Bay Area', 'EUA', False),
    (9, 'Fase de Grupos', 'E', 1, '2026-06-14', '19:00', 'Costa do Marfim', 'Equador', 'CIV', 'ECU', 'Lincoln Financial Field', 'Philadelphia', 'EUA', False),
    (10, 'Fase de Grupos', 'E', 1, '2026-06-14', '13:00', 'Alemanha', 'Curaçao', 'GER', 'CUW', 'NRG Stadium', 'Houston', 'EUA', False),
    (11, 'Fase de Grupos', 'F', 1, '2026-06-14', '16:00', 'Holanda', 'Japão', 'NED', 'JPN', 'AT&T Stadium', 'Dallas', 'EUA', False),
    (12, 'Fase de Grupos', 'F', 1, '2026-06-14', '22:00', 'Suécia', 'Tunísia', 'SWE', 'TUN', 'Estadio BBVA', 'Monterrey', 'México', False),
    (13, 'Fase de Grupos', 'H', 1, '2026-06-15', '18:00', 'Arábia Saudita', 'Uruguai', 'KSA', 'URU', 'Hard Rock Stadium', 'Miami', 'EUA', False),
    (14, 'Fase de Grupos', 'H', 1, '2026-06-15', '12:00', 'Espanha', 'Cabo Verde', 'ESP', 'CPV', 'Mercedes-Benz Stadium', 'Atlanta', 'EUA', False),
    (15, 'Fase de Grupos', 'G', 1, '2026-06-15', '21:00', 'Irã', 'Nova Zelândia', 'IRN', 'NZL', 'SoFi Stadium', 'Los Angeles', 'EUA', False),
    (16, 'Fase de Grupos', 'G', 1, '2026-06-15', '15:00', 'Bélgica', 'Egito', 'BEL', 'EGY', 'Lumen Field', 'Seattle', 'EUA', False),
    (17, 'Fase de Grupos', 'I', 1, '2026-06-16', '15:00', 'França', 'Senegal', 'FRA', 'SEN', 'MetLife Stadium', 'New York/New Jersey', 'EUA', False),
    (18, 'Fase de Grupos', 'I', 1, '2026-06-16', '18:00', 'Iraque', 'Noruega', 'IRQ', 'NOR', 'Gillette Stadium', 'Boston', 'EUA', False),
    (19, 'Fase de Grupos', 'J', 1, '2026-06-16', '21:00', 'Argentina', 'Argélia', 'ARG', 'ALG', 'Arrowhead Stadium', 'Kansas City', 'EUA', False),
    (20, 'Fase de Grupos', 'J', 1, '2026-06-17', '00:00', 'Áustria', 'Jordânia', 'AUT', 'JOR', "Levi's Stadium", 'San Francisco Bay Area', 'EUA', False),
    (21, 'Fase de Grupos', 'L', 1, '2026-06-17', '19:00', 'Gana', 'Panamá', 'GHA', 'PAN', 'BMO Field', 'Toronto', 'Canadá', False),
    (22, 'Fase de Grupos', 'L', 1, '2026-06-17', '16:00', 'Inglaterra', 'Croácia', 'ENG', 'CRO', 'AT&T Stadium', 'Dallas', 'EUA', False),
    (23, 'Fase de Grupos', 'K', 1, '2026-06-17', '13:00', 'Portugal', 'Congo DR', 'POR', 'COD', 'NRG Stadium', 'Houston', 'EUA', False),
    (24, 'Fase de Grupos', 'K', 1, '2026-06-17', '22:00', 'Uzbequistão', 'Colômbia', 'UZB', 'COL', 'Estadio Azteca', 'Mexico City', 'México', False),
    (25, 'Fase de Grupos', 'A', 2, '2026-06-18', '12:00', 'Tchéquia', 'África do Sul', 'CZE', 'RSA', 'Mercedes-Benz Stadium', 'Atlanta', 'EUA', False),
    (26, 'Fase de Grupos', 'B', 2, '2026-06-18', '15:00', 'Suíça', 'Bósnia e Herzegovina', 'SUI', 'BIH', 'SoFi Stadium', 'Los Angeles', 'EUA', False),
    (27, 'Fase de Grupos', 'B', 2, '2026-06-18', '18:00', 'Canadá', 'Catar', 'CAN', 'QAT', 'BC Place', 'Vancouver', 'Canadá', False),
    (28, 'Fase de Grupos', 'A', 2, '2026-06-18', '21:00', 'México', 'Coreia do Sul', 'MEX', 'KOR', 'Estadio Akron', 'Guadalajara', 'México', False),
    (29, 'Fase de Grupos', 'C', 2, '2026-06-19', '20:30', 'Brasil', 'Haiti', 'BRA', 'HAI', 'Lincoln Financial Field', 'Philadelphia', 'EUA', False),
    (30, 'Fase de Grupos', 'C', 2, '2026-06-19', '18:00', 'Escócia', 'Marrocos', 'SCO', 'MAR', 'Gillette Stadium', 'Boston', 'EUA', False),
    (31, 'Fase de Grupos', 'D', 2, '2026-06-19', '23:00', 'Turquia', 'Paraguai', 'TUR', 'PAR', "Levi's Stadium", 'San Francisco Bay Area', 'EUA', False),
    (32, 'Fase de Grupos', 'D', 2, '2026-06-19', '15:00', 'Estados Unidos', 'Austrália', 'USA', 'AUS', 'Lumen Field', 'Seattle', 'EUA', False),
    (33, 'Fase de Grupos', 'E', 2, '2026-06-20', '16:00', 'Alemanha', 'Costa do Marfim', 'GER', 'CIV', 'BMO Field', 'Toronto', 'Canadá', False),
    (34, 'Fase de Grupos', 'E', 2, '2026-06-20', '20:00', 'Equador', 'Curaçao', 'ECU', 'CUW', 'Arrowhead Stadium', 'Kansas City', 'EUA', False),
    (35, 'Fase de Grupos', 'F', 2, '2026-06-20', '13:00', 'Holanda', 'Suécia', 'NED', 'SWE', 'NRG Stadium', 'Houston', 'EUA', False),
    (36, 'Fase de Grupos', 'F', 2, '2026-06-21', '00:00', 'Tunísia', 'Japão', 'TUN', 'JPN', 'Estadio BBVA', 'Monterrey', 'México', False),
    (37, 'Fase de Grupos', 'H', 2, '2026-06-21', '18:00', 'Uruguai', 'Cabo Verde', 'URU', 'CPV', 'Hard Rock Stadium', 'Miami', 'EUA', False),
    (38, 'Fase de Grupos', 'H', 2, '2026-06-21', '12:00', 'Espanha', 'Arábia Saudita', 'ESP', 'KSA', 'Mercedes-Benz Stadium', 'Atlanta', 'EUA', False),
    (39, 'Fase de Grupos', 'G', 2, '2026-06-21', '15:00', 'Bélgica', 'Irã', 'BEL', 'IRN', 'SoFi Stadium', 'Los Angeles', 'EUA', False),
    (40, 'Fase de Grupos', 'G', 2, '2026-06-21', '21:00', 'Nova Zelândia', 'Egito', 'NZL', 'EGY', 'BC Place', 'Vancouver', 'Canadá', False),
    (41, 'Fase de Grupos', 'I', 2, '2026-06-22', '20:00', 'Noruega', 'Senegal', 'NOR', 'SEN', 'MetLife Stadium', 'New York/New Jersey', 'EUA', False),
    (42, 'Fase de Grupos', 'I', 2, '2026-06-22', '17:00', 'França', 'Iraque', 'FRA', 'IRQ', 'Lincoln Financial Field', 'Philadelphia', 'EUA', False),
    (43, 'Fase de Grupos', 'J', 2, '2026-06-22', '13:00', 'Argentina', 'Áustria', 'ARG', 'AUT', 'AT&T Stadium', 'Dallas', 'EUA', False),
    (44, 'Fase de Grupos', 'J', 2, '2026-06-22', '23:00', 'Jordânia', 'Argélia', 'JOR', 'ALG', "Levi's Stadium", 'San Francisco Bay Area', 'EUA', False),
    (45, 'Fase de Grupos', 'L', 2, '2026-06-23', '16:00', 'Inglaterra', 'Gana', 'ENG', 'GHA', 'Gillette Stadium', 'Boston', 'EUA', False),
    (46, 'Fase de Grupos', 'L', 2, '2026-06-23', '19:00', 'Panamá', 'Croácia', 'PAN', 'CRO', 'BMO Field', 'Toronto', 'Canadá', False),
    (47, 'Fase de Grupos', 'K', 2, '2026-06-23', '13:00', 'Portugal', 'Uzbequistão', 'POR', 'UZB', 'NRG Stadium', 'Houston', 'EUA', False),
    (48, 'Fase de Grupos', 'K', 2, '2026-06-23', '22:00', 'Colômbia', 'Congo DR', 'COL', 'COD', 'Estadio Akron', 'Guadalajara', 'México', False),
    (49, 'Fase de Grupos', 'C', 3, '2026-06-24', '18:00', 'Escócia', 'Brasil', 'SCO', 'BRA', 'Hard Rock Stadium', 'Miami', 'EUA', False),
    (50, 'Fase de Grupos', 'C', 3, '2026-06-24', '18:00', 'Marrocos', 'Haiti', 'MAR', 'HAI', 'Mercedes-Benz Stadium', 'Atlanta', 'EUA', False),
    (51, 'Fase de Grupos', 'B', 3, '2026-06-24', '15:00', 'Suíça', 'Canadá', 'SUI', 'CAN', 'BC Place', 'Vancouver', 'Canadá', False),
    (52, 'Fase de Grupos', 'B', 3, '2026-06-24', '15:00', 'Bósnia e Herzegovina', 'Catar', 'BIH', 'QAT', 'Lumen Field', 'Seattle', 'EUA', False),
    (53, 'Fase de Grupos', 'A', 3, '2026-06-24', '21:00', 'Tchéquia', 'México', 'CZE', 'MEX', 'Estadio Azteca', 'Mexico City', 'México', False),
    (54, 'Fase de Grupos', 'A', 3, '2026-06-24', '21:00', 'África do Sul', 'Coreia do Sul', 'RSA', 'KOR', 'Estadio BBVA', 'Monterrey', 'México', False),
    (55, 'Fase de Grupos', 'E', 3, '2026-06-25', '16:00', 'Curaçao', 'Costa do Marfim', 'CUW', 'CIV', 'Lincoln Financial Field', 'Philadelphia', 'EUA', False),
    (56, 'Fase de Grupos', 'E', 3, '2026-06-25', '16:00', 'Equador', 'Alemanha', 'ECU', 'GER', 'MetLife Stadium', 'New York/New Jersey', 'EUA', False),
    (57, 'Fase de Grupos', 'F', 3, '2026-06-25', '19:00', 'Japão', 'Suécia', 'JPN', 'SWE', 'AT&T Stadium', 'Dallas', 'EUA', False),
    (58, 'Fase de Grupos', 'F', 3, '2026-06-25', '19:00', 'Tunísia', 'Holanda', 'TUN', 'NED', 'Arrowhead Stadium', 'Kansas City', 'EUA', False),
    (59, 'Fase de Grupos', 'D', 3, '2026-06-25', '22:00', 'Turquia', 'Estados Unidos', 'TUR', 'USA', 'SoFi Stadium', 'Los Angeles', 'EUA', False),
    (60, 'Fase de Grupos', 'D', 3, '2026-06-25', '22:00', 'Paraguai', 'Austrália', 'PAR', 'AUS', "Levi's Stadium", 'San Francisco Bay Area', 'EUA', False),
    (61, 'Fase de Grupos', 'I', 3, '2026-06-26', '15:00', 'Noruega', 'França', 'NOR', 'FRA', 'Gillette Stadium', 'Boston', 'EUA', False),
    (62, 'Fase de Grupos', 'I', 3, '2026-06-26', '15:00', 'Senegal', 'Iraque', 'SEN', 'IRQ', 'BMO Field', 'Toronto', 'Canadá', False),
    (63, 'Fase de Grupos', 'G', 3, '2026-06-26', '23:00', 'Egito', 'Irã', 'EGY', 'IRN', 'Lumen Field', 'Seattle', 'EUA', False),
    (64, 'Fase de Grupos', 'G', 3, '2026-06-26', '23:00', 'Nova Zelândia', 'Bélgica', 'NZL', 'BEL', 'BC Place', 'Vancouver', 'Canadá', False),
    (65, 'Fase de Grupos', 'H', 3, '2026-06-26', '20:00', 'Cabo Verde', 'Arábia Saudita', 'CPV', 'KSA', 'NRG Stadium', 'Houston', 'EUA', False),
    (66, 'Fase de Grupos', 'H', 3, '2026-06-26', '20:00', 'Uruguai', 'Espanha', 'URU', 'ESP', 'Estadio Akron', 'Guadalajara', 'México', False),
    (67, 'Fase de Grupos', 'L', 3, '2026-06-27', '17:00', 'Panamá', 'Inglaterra', 'PAN', 'ENG', 'MetLife Stadium', 'New York/New Jersey', 'EUA', False),
    (68, 'Fase de Grupos', 'L', 3, '2026-06-27', '17:00', 'Croácia', 'Gana', 'CRO', 'GHA', 'Lincoln Financial Field', 'Philadelphia', 'EUA', False),
    (69, 'Fase de Grupos', 'J', 3, '2026-06-27', '22:00', 'Argélia', 'Áustria', 'ALG', 'AUT', 'Arrowhead Stadium', 'Kansas City', 'EUA', False),
    (70, 'Fase de Grupos', 'J', 3, '2026-06-27', '22:00', 'Jordânia', 'Argentina', 'JOR', 'ARG', 'AT&T Stadium', 'Dallas', 'EUA', False),
    (71, 'Fase de Grupos', 'K', 3, '2026-06-27', '19:30', 'Colômbia', 'Portugal', 'COL', 'POR', 'Hard Rock Stadium', 'Miami', 'EUA', False),
    (72, 'Fase de Grupos', 'K', 3, '2026-06-27', '19:30', 'Congo DR', 'Uzbequistão', 'COD', 'UZB', 'Mercedes-Benz Stadium', 'Atlanta', 'EUA', False),
    (73, 'Rodada de 32', None, 1, '2026-06-28', '15:00', '2º Grupo A', '2º Grupo B', '2A', '2B', 'SoFi Stadium', 'Los Angeles', 'EUA', True),
    (74, 'Rodada de 32', None, 1, '2026-06-29', '16:30', '1º Grupo E', '3º Grupo A/B/C/D/F', '1E', '3ABCDF', 'Gillette Stadium', 'Boston', 'EUA', True),
    (75, 'Rodada de 32', None, 1, '2026-06-29', '21:00', '1º Grupo F', '2º Grupo C', '1F', '2C', 'Estadio BBVA', 'Monterrey', 'México', True),
    (76, 'Rodada de 32', None, 1, '2026-06-29', '13:00', '1º Grupo C', '2º Grupo F', '1C', '2F', 'NRG Stadium', 'Houston', 'EUA', True),
    (77, 'Rodada de 32', None, 1, '2026-06-30', '17:00', '1º Grupo I', '3º Grupo C/D/F/G/H', '1I', '3CDFGH', 'MetLife Stadium', 'New York/New Jersey', 'EUA', True),
    (78, 'Rodada de 32', None, 1, '2026-06-30', '13:00', '2º Grupo E', '2º Grupo I', '2E', '2I', 'AT&T Stadium', 'Dallas', 'EUA', True),
    (79, 'Rodada de 32', None, 1, '2026-06-30', '21:00', '1º Grupo A', '3º Grupo C/E/F/H/I', '1A', '3CEFHI', 'Estadio Azteca', 'Mexico City', 'México', True),
    (80, 'Rodada de 32', None, 1, '2026-07-01', '12:00', '1º Grupo L', '3º Grupo E/H/I/J/K', '1L', '3EHIJK', 'Mercedes-Benz Stadium', 'Atlanta', 'EUA', True),
    (81, 'Rodada de 32', None, 1, '2026-07-01', '20:00', '1º Grupo D', '3º Grupo B/E/F/I/J', '1D', '3BEFIJ', "Levi's Stadium", 'San Francisco Bay Area', 'EUA', True),
    (82, 'Rodada de 32', None, 1, '2026-07-01', '16:00', '1º Grupo G', '3º Grupo A/E/H/I/J', '1G', '3AEHIJ', 'Lumen Field', 'Seattle', 'EUA', True),
    (83, 'Rodada de 32', None, 1, '2026-07-02', '19:00', '2º Grupo K', '2º Grupo L', '2K', '2L', 'BMO Field', 'Toronto', 'Canadá', True),
    (84, 'Rodada de 32', None, 1, '2026-07-02', '15:00', '1º Grupo H', '2º Grupo J', '1H', '2J', 'SoFi Stadium', 'Los Angeles', 'EUA', True),
    (85, 'Rodada de 32', None, 1, '2026-07-02', '23:00', '1º Grupo B', '3º Grupo E/F/G/I/J', '1B', '3EFGIJ', 'BC Place', 'Vancouver', 'Canadá', True),
    (86, 'Rodada de 32', None, 1, '2026-07-03', '18:00', '1º Grupo J', '2º Grupo H', '1J', '2H', 'Hard Rock Stadium', 'Miami', 'EUA', True),
    (87, 'Rodada de 32', None, 1, '2026-07-03', '21:30', '1º Grupo K', '3º Grupo D/E/I/J/L', '1K', '3DEIJL', 'Arrowhead Stadium', 'Kansas City', 'EUA', True),
    (88, 'Rodada de 32', None, 1, '2026-07-03', '14:00', '2º Grupo D', '2º Grupo G', '2D', '2G', 'AT&T Stadium', 'Dallas', 'EUA', True),
    (89, 'Oitavas de Final', None, 1, '2026-07-04', '17:00', 'Vencedor J74', 'Vencedor J77', 'WJ74', 'WJ77', 'Lincoln Financial Field', 'Philadelphia', 'EUA', True),
    (90, 'Oitavas de Final', None, 1, '2026-07-04', '13:00', 'Vencedor J73', 'Vencedor J75', 'WJ73', 'WJ75', 'NRG Stadium', 'Houston', 'EUA', True),
    (91, 'Oitavas de Final', None, 1, '2026-07-05', '16:00', 'Vencedor J76', 'Vencedor J78', 'WJ76', 'WJ78', 'MetLife Stadium', 'New York/New Jersey', 'EUA', True),
    (92, 'Oitavas de Final', None, 1, '2026-07-05', '20:00', 'Vencedor J79', 'Vencedor J80', 'WJ79', 'WJ80', 'Estadio Azteca', 'Mexico City', 'México', True),
    (93, 'Oitavas de Final', None, 1, '2026-07-06', '15:00', 'Vencedor J83', 'Vencedor J84', 'WJ83', 'WJ84', 'AT&T Stadium', 'Dallas', 'EUA', True),
    (94, 'Oitavas de Final', None, 1, '2026-07-06', '20:00', 'Vencedor J81', 'Vencedor J82', 'WJ81', 'WJ82', 'Lumen Field', 'Seattle', 'EUA', True),
    (95, 'Oitavas de Final', None, 1, '2026-07-07', '12:00', 'Vencedor J86', 'Vencedor J88', 'WJ86', 'WJ88', 'Mercedes-Benz Stadium', 'Atlanta', 'EUA', True),
    (96, 'Oitavas de Final', None, 1, '2026-07-07', '16:00', 'Vencedor J85', 'Vencedor J87', 'WJ85', 'WJ87', 'BC Place', 'Vancouver', 'Canadá', True),
    (97, 'Quartas de Final', None, 1, '2026-07-09', '16:00', 'Vencedor J89', 'Vencedor J90', 'WJ89', 'WJ90', 'Gillette Stadium', 'Boston', 'EUA', True),
    (98, 'Quartas de Final', None, 1, '2026-07-10', '15:00', 'Vencedor J93', 'Vencedor J94', 'WJ93', 'WJ94', 'SoFi Stadium', 'Los Angeles', 'EUA', True),
    (99, 'Quartas de Final', None, 1, '2026-07-11', '17:00', 'Vencedor J91', 'Vencedor J92', 'WJ91', 'WJ92', 'Hard Rock Stadium', 'Miami', 'EUA', True),
    (100, 'Quartas de Final', None, 1, '2026-07-11', '21:00', 'Vencedor J95', 'Vencedor J96', 'WJ95', 'WJ96', 'Arrowhead Stadium', 'Kansas City', 'EUA', True),
    (101, 'Semifinal', None, 1, '2026-07-14', '15:00', 'Vencedor J97', 'Vencedor J98', 'WJ97', 'WJ98', 'AT&T Stadium', 'Dallas', 'EUA', True),
    (102, 'Semifinal', None, 1, '2026-07-15', '15:00', 'Vencedor J99', 'Vencedor J100', 'WJ99', 'WJ100', 'Mercedes-Benz Stadium', 'Atlanta', 'EUA', True),
    (103, 'Terceiro Lugar', None, 1, '2026-07-18', '17:00', 'Perdedor J101', 'Perdedor J102', 'LJ101', 'LJ102', 'Hard Rock Stadium', 'Miami', 'EUA', True),
    (104, 'Final', None, 1, '2026-07-19', '15:00', 'Vencedor J101', 'Vencedor J102', 'WJ101', 'WJ102', 'MetLife Stadium', 'New York/New Jersey', 'EUA', True),
]


def _jogo_kwargs(row):
    (num, fase, grupo, rodada, data_str, hora_et,
     time_a, time_b, sigla_a, sigla_b,
     estadio, cidade, pais, mata_mata) = row

    data_jogo = datetime.strptime(data_str, "%Y-%m-%d").date()
    hora_br = et_to_brasilia(data_jogo, hora_et)
    prazo = calcular_prazo_palpite(data_jogo, hora_et)
    return {
        "numero_partida": num,
        "fase": fase,
        "grupo": grupo,
        "rodada": rodada,
        "data_jogo": data_jogo,
        "hora_et": hora_et,
        "timezone_original": "America/New_York",
        "hora_brasilia": hora_br,
        "timezone_exibicao": "America/Sao_Paulo",
        "time_a": time_a,
        "time_b": time_b,
        "sigla_time_a": sigla_a,
        "sigla_time_b": sigla_b,
        "estadio": estadio,
        "cidade": cidade,
        "pais": pais,
        "mata_mata": mata_mata,
        "prazo_palpite": prazo,
        "status": "Agendado",
    }


def sync_jogos_2026(db, Jogo, remove_obsoletos=False):
    """Insere ou atualiza a tabela de jogos usando numero_partida como chave."""
    existentes = {j.numero_partida: j for j in Jogo.query.all() if j.numero_partida}
    numeros_atuais = set()
    alterados = 0

    for row in JOGOS:
        dados = _jogo_kwargs(row)
        num = dados["numero_partida"]
        numeros_atuais.add(num)
        jogo = existentes.get(num)
        if jogo is None:
            db.session.add(Jogo(**dados))
            alterados += 1
            continue

        for campo, valor in dados.items():
            if getattr(jogo, campo) != valor:
                setattr(jogo, campo, valor)
                alterados += 1

    if remove_obsoletos:
        for jogo in Jogo.query.filter(Jogo.numero_partida.isnot(None)).all():
            if jogo.numero_partida not in numeros_atuais:
                db.session.delete(jogo)
                alterados += 1

    if alterados:
        db.session.commit()
    return alterados


def seed_jogos(db, Jogo):
    """Insere todos os jogos caso a tabela esteja vazia."""
    if Jogo.query.count() > 0:
        return 0
    count = 0
    for row in JOGOS:
        jogo = Jogo(**_jogo_kwargs(row))
        db.session.add(jogo)
        count += 1
    db.session.commit()
    return count
