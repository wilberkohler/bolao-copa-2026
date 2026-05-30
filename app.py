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
SUPPORTED_LANGUAGES = {
    "pt-BR": "Português",
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "it": "Italiano",
    "ar": "العربية",
    "zh": "中文",
    "ru": "Русский",
}
DEFAULT_LANGUAGE = "pt-BR"
DEFAULT_HIGHLIGHT_TEAM_BY_LANGUAGE = {
    "pt-BR": "BRA",
    "en": "USA",
    "es": "ESP",
    "fr": "FRA",
    "de": "GER",
    "it": "ITA",
    "ar": "KSA",
    "zh": "KOR",
    "ru": "KAZ",
}
LANGUAGE_BADGES = {
    "pt-BR": "BR",
    "en": "EN",
    "es": "ES",
    "fr": "FR",
    "de": "DE",
    "it": "IT",
    "ar": "AR",
    "zh": "中文",
    "ru": "RU",
}
TEAM_TRANSLATIONS = {
    "en": {
        "México": "Mexico",
        "África do Sul": "South Africa",
        "Argentina": "Argentina",
        "Argélia": "Algeria",
        "Espanha": "Spain",
        "Cabo Verde": "Cape Verde",
        "Portugal": "Portugal",
        "Congo DR": "DR Congo",
        "Estados Unidos": "United States",
        "Paraguai": "Paraguay",
        "Uruguai": "Uruguay",
        "Angola": "Angola",
        "Brasil": "Brazil",
        "Marrocos": "Morocco",
        "Japão": "Japan",
        "Croácia": "Croatia",
        "Alemanha": "Germany",
        "Curaçao": "Curacao",
        "Chile": "Chile",
        "Austrália": "Australia",
        "França": "France",
        "Senegal": "Senegal",
        "Bélgica": "Belgium",
        "Equador": "Ecuador",
        "Inglaterra": "England",
        "Sérvia": "Serbia",
        "Holanda": "Netherlands",
        "Zimbábue": "Zimbabwe",
        "Colômbia": "Colombia",
        "Nova Zelândia": "New Zealand",
        "Itália": "Italy",
        "Cazaquistão": "Kazakhstan",
        "Dinamarca": "Denmark",
        "Arábia Saudita": "Saudi Arabia",
        "Canadá": "Canada",
        "Bósnia e Herzegovina": "Bosnia and Herzegovina",
        "Suíça": "Switzerland",
        "Malaui": "Malawi",
        "Coreia do Sul": "South Korea",
        "Filipinas": "Philippines",
        "Costa Rica": "Costa Rica",
        "Haiti": "Haiti",
        "Escócia": "Scotland",
        "Turquia": "Turkey",
        "Venezuela": "Venezuela",
    },
    "es": {
        "México": "México",
        "África do Sul": "Sudáfrica",
        "Argentina": "Argentina",
        "Argélia": "Argelia",
        "Espanha": "España",
        "Cabo Verde": "Cabo Verde",
        "Portugal": "Portugal",
        "Congo DR": "RD Congo",
        "Estados Unidos": "Estados Unidos",
        "Paraguai": "Paraguay",
        "Uruguai": "Uruguay",
        "Angola": "Angola",
        "Brasil": "Brasil",
        "Marrocos": "Marruecos",
        "Japão": "Japón",
        "Croácia": "Croacia",
        "Alemanha": "Alemania",
        "Curaçao": "Curazao",
        "Chile": "Chile",
        "Austrália": "Australia",
        "França": "Francia",
        "Senegal": "Senegal",
        "Bélgica": "Bélgica",
        "Equador": "Ecuador",
        "Inglaterra": "Inglaterra",
        "Sérvia": "Serbia",
        "Holanda": "Países Bajos",
        "Zimbábue": "Zimbabue",
        "Colômbia": "Colombia",
        "Nova Zelândia": "Nueva Zelanda",
        "Itália": "Italia",
        "Cazaquistão": "Kazajistán",
        "Dinamarca": "Dinamarca",
        "Arábia Saudita": "Arabia Saudita",
        "Canadá": "Canadá",
        "Bósnia e Herzegovina": "Bosnia y Herzegovina",
        "Suíça": "Suiza",
        "Malaui": "Malaui",
        "Coreia do Sul": "Corea del Sur",
        "Filipinas": "Filipinas",
        "Costa Rica": "Costa Rica",
        "Haiti": "Haití",
        "Escócia": "Escocia",
        "Turquia": "Turquía",
        "Venezuela": "Venezuela",
    },
    "fr": {
        "México": "Mexique",
        "África do Sul": "Afrique du Sud",
        "Argentina": "Argentine",
        "Argélia": "Algérie",
        "Espanha": "Espagne",
        "Cabo Verde": "Cap-Vert",
        "Portugal": "Portugal",
        "Congo DR": "RD Congo",
        "Estados Unidos": "États-Unis",
        "Paraguai": "Paraguay",
        "Uruguai": "Uruguay",
        "Angola": "Angola",
        "Brasil": "Brésil",
        "Marrocos": "Maroc",
        "Japão": "Japon",
        "Croácia": "Croatie",
        "Alemanha": "Allemagne",
        "Curaçao": "Curaçao",
        "Chile": "Chili",
        "Austrália": "Australie",
        "França": "France",
        "Senegal": "Sénégal",
        "Bélgica": "Belgique",
        "Equador": "Équateur",
        "Inglaterra": "Angleterre",
        "Sérvia": "Serbie",
        "Holanda": "Pays-Bas",
        "Zimbábue": "Zimbabwe",
        "Colômbia": "Colombie",
        "Nova Zelândia": "Nouvelle-Zélande",
        "Itália": "Italie",
        "Cazaquistão": "Kazakhstan",
        "Dinamarca": "Danemark",
        "Arábia Saudita": "Arabie saoudite",
        "Canadá": "Canada",
        "Bósnia e Herzegovina": "Bosnie-Herzégovine",
        "Suíça": "Suisse",
        "Malaui": "Malawi",
        "Coreia do Sul": "Corée du Sud",
        "Filipinas": "Philippines",
        "Costa Rica": "Costa Rica",
        "Haiti": "Haïti",
        "Escócia": "Écosse",
        "Turquia": "Turquie",
        "Venezuela": "Venezuela",
    },
    "de": {
        "México": "Mexiko",
        "África do Sul": "Südafrika",
        "Argentina": "Argentinien",
        "Argélia": "Algerien",
        "Espanha": "Spanien",
        "Cabo Verde": "Kap Verde",
        "Portugal": "Portugal",
        "Congo DR": "DR Kongo",
        "Estados Unidos": "Vereinigte Staaten",
        "Paraguai": "Paraguay",
        "Uruguai": "Uruguay",
        "Angola": "Angola",
        "Brasil": "Brasilien",
        "Marrocos": "Marokko",
        "Japão": "Japan",
        "Croácia": "Kroatien",
        "Alemanha": "Deutschland",
        "Curaçao": "Curaçao",
        "Chile": "Chile",
        "Austrália": "Australien",
        "França": "Frankreich",
        "Senegal": "Senegal",
        "Bélgica": "Belgien",
        "Equador": "Ecuador",
        "Inglaterra": "England",
        "Sérvia": "Serbien",
        "Holanda": "Niederlande",
        "Zimbábue": "Simbabwe",
        "Colômbia": "Kolumbien",
        "Nova Zelândia": "Neuseeland",
        "Itália": "Italien",
        "Cazaquistão": "Kasachstan",
        "Dinamarca": "Dänemark",
        "Arábia Saudita": "Saudi-Arabien",
        "Canadá": "Kanada",
        "Bósnia e Herzegovina": "Bosnien und Herzegowina",
        "Suíça": "Schweiz",
        "Malaui": "Malawi",
        "Coreia do Sul": "Südkorea",
        "Filipinas": "Philippinen",
        "Costa Rica": "Costa Rica",
        "Haiti": "Haiti",
        "Escócia": "Schottland",
        "Turquia": "Türkei",
        "Venezuela": "Venezuela",
    },
    "it": {
        "México": "Messico", "África do Sul": "Sudafrica", "Argentina": "Argentina", "Argélia": "Algeria",
        "Espanha": "Spagna", "Cabo Verde": "Capo Verde", "Portugal": "Portogallo", "Congo DR": "RD Congo",
        "Estados Unidos": "Stati Uniti", "Paraguai": "Paraguay", "Uruguai": "Uruguay", "Angola": "Angola",
        "Brasil": "Brasile", "Marrocos": "Marocco", "Japão": "Giappone", "Croácia": "Croazia",
        "Alemanha": "Germania", "Curaçao": "Curaçao", "Chile": "Cile", "Austrália": "Australia",
        "França": "Francia", "Senegal": "Senegal", "Bélgica": "Belgio", "Equador": "Ecuador",
        "Inglaterra": "Inghilterra", "Sérvia": "Serbia", "Holanda": "Paesi Bassi", "Zimbábue": "Zimbabwe",
        "Colômbia": "Colombia", "Nova Zelândia": "Nuova Zelanda", "Itália": "Italia", "Cazaquistão": "Kazakistan",
        "Dinamarca": "Danimarca", "Arábia Saudita": "Arabia Saudita", "Canadá": "Canada",
        "Bósnia e Herzegovina": "Bosnia ed Erzegovina", "Suíça": "Svizzera", "Malaui": "Malawi",
        "Coreia do Sul": "Corea del Sud", "Filipinas": "Filippine", "Costa Rica": "Costa Rica",
        "Haiti": "Haiti", "Escócia": "Scozia", "Turquia": "Turchia", "Venezuela": "Venezuela",
    },
    "ar": {
        "México": "المكسيك", "África do Sul": "جنوب أفريقيا", "Argentina": "الأرجنتين", "Argélia": "الجزائر",
        "Espanha": "إسبانيا", "Cabo Verde": "الرأس الأخضر", "Portugal": "البرتغال", "Congo DR": "الكونغو الديمقراطية",
        "Estados Unidos": "الولايات المتحدة", "Paraguai": "باراغواي", "Uruguai": "أوروغواي", "Angola": "أنغولا",
        "Brasil": "البرازيل", "Marrocos": "المغرب", "Japão": "اليابان", "Croácia": "كرواتيا",
        "Alemanha": "ألمانيا", "Curaçao": "كوراساو", "Chile": "تشيلي", "Austrália": "أستراليا",
        "França": "فرنسا", "Senegal": "السنغال", "Bélgica": "بلجيكا", "Equador": "الإكوادور",
        "Inglaterra": "إنجلترا", "Sérvia": "صربيا", "Holanda": "هولندا", "Zimbábue": "زيمبابوي",
        "Colômbia": "كولومبيا", "Nova Zelândia": "نيوزيلندا", "Itália": "إيطاليا", "Cazaquistão": "كازاخستان",
        "Dinamarca": "الدنمارك", "Arábia Saudita": "السعودية", "Canadá": "كندا",
        "Bósnia e Herzegovina": "البوسنة والهرسك", "Suíça": "سويسرا", "Malaui": "مالاوي",
        "Coreia do Sul": "كوريا الجنوبية", "Filipinas": "الفلبين", "Costa Rica": "كوستاريكا",
        "Haiti": "هايتي", "Escócia": "اسكتلندا", "Turquia": "تركيا", "Venezuela": "فنزويلا",
    },
    "zh": {
        "México": "墨西哥", "África do Sul": "南非", "Argentina": "阿根廷", "Argélia": "阿尔及利亚",
        "Espanha": "西班牙", "Cabo Verde": "佛得角", "Portugal": "葡萄牙", "Congo DR": "刚果民主共和国",
        "Estados Unidos": "美国", "Paraguai": "巴拉圭", "Uruguai": "乌拉圭", "Angola": "安哥拉",
        "Brasil": "巴西", "Marrocos": "摩洛哥", "Japão": "日本", "Croácia": "克罗地亚",
        "Alemanha": "德国", "Curaçao": "库拉索", "Chile": "智利", "Austrália": "澳大利亚",
        "França": "法国", "Senegal": "塞内加尔", "Bélgica": "比利时", "Equador": "厄瓜多尔",
        "Inglaterra": "英格兰", "Sérvia": "塞尔维亚", "Holanda": "荷兰", "Zimbábue": "津巴布韦",
        "Colômbia": "哥伦比亚", "Nova Zelândia": "新西兰", "Itália": "意大利", "Cazaquistão": "哈萨克斯坦",
        "Dinamarca": "丹麦", "Arábia Saudita": "沙特阿拉伯", "Canadá": "加拿大",
        "Bósnia e Herzegovina": "波黑", "Suíça": "瑞士", "Malaui": "马拉维",
        "Coreia do Sul": "韩国", "Filipinas": "菲律宾", "Costa Rica": "哥斯达黎加",
        "Haiti": "海地", "Escócia": "苏格兰", "Turquia": "土耳其", "Venezuela": "委内瑞拉",
    },
    "ru": {
        "México": "Мексика", "África do Sul": "Южная Африка", "Argentina": "Аргентина", "Argélia": "Алжир",
        "Espanha": "Испания", "Cabo Verde": "Кабо-Верде", "Portugal": "Португалия", "Congo DR": "ДР Конго",
        "Estados Unidos": "США", "Paraguai": "Парагвай", "Uruguai": "Уругвай", "Angola": "Ангола",
        "Brasil": "Бразилия", "Marrocos": "Марокко", "Japão": "Япония", "Croácia": "Хорватия",
        "Alemanha": "Германия", "Curaçao": "Кюрасао", "Chile": "Чили", "Austrália": "Австралия",
        "França": "Франция", "Senegal": "Сенегал", "Bélgica": "Бельгия", "Equador": "Эквадор",
        "Inglaterra": "Англия", "Sérvia": "Сербия", "Holanda": "Нидерланды", "Zimbábue": "Зимбабве",
        "Colômbia": "Колумбия", "Nova Zelândia": "Новая Зеландия", "Itália": "Италия", "Cazaquistão": "Казахстан",
        "Dinamarca": "Дания", "Arábia Saudita": "Саудовская Аравия", "Canadá": "Канада",
        "Bósnia e Herzegovina": "Босния и Герцеговина", "Suíça": "Швейцария", "Malaui": "Малави",
        "Coreia do Sul": "Южная Корея", "Filipinas": "Филиппины", "Costa Rica": "Коста-Рика",
        "Haiti": "Гаити", "Escócia": "Шотландия", "Turquia": "Турция", "Venezuela": "Венесуэла",
    },
}

TRANSLATIONS = {
    "pt-BR": {
        "language_label": "Idioma",
        "login_title": "Login - Bolão Copa 2026",
        "app_name": "Bolão Copa 2026",
        "system_subtitle": "Sistema de Palpites",
        "email": "E-mail",
        "password": "Senha",
        "sign_in": "Entrar",
        "signing_in": "Entrando...",
        "forgot_password": "Esqueci minha senha",
        "no_account": "Ainda não tem conta?",
        "register_here": "Cadastre-se aqui",
        "logged_out": "Você saiu.",
        "register_title": "Cadastro - Bolão Copa 2026",
        "register_heading": "Cadastro - Bolão Copa 2026",
        "name": "Nome",
        "nickname": "Apelido",
        "required": "*",
        "nickname_placeholder": "Como você quer ser chamado?",
        "group": "Grupo",
        "optional": "(opcional)",
        "no_group": "-- Sem grupo --",
        "private": "privado",
        "group_help": "Escolha um grupo aberto. Grupos privados exigem código.",
        "private_group_code": "Código do grupo privado",
        "private_group_code_placeholder": "Necessário apenas para grupos privados",
        "register": "Cadastrar",
        "registering": "Cadastrando...",
        "has_account": "Já tem conta?",
        "sign_in_here": "Entre aqui",
        "recover_password_title": "Recuperar senha - Bolão Copa 2026",
        "recover_password": "Recuperar senha",
        "recover_password_subtitle": "Informe seu e-mail de cadastro",
        "send_link": "Enviar link",
        "sending": "Enviando...",
        "remembered_password": "Lembrou a senha?",
        "new_password_title": "Nova senha - Bolão Copa 2026",
        "new_password_heading": "Criar nova senha",
        "new_password": "Nova senha",
        "confirm_new_password": "Confirmar nova senha",
        "save_password": "Salvar senha",
        "saving": "Salvando...",
        "back_to_login": "Voltar ao login",
        "nav_home": "Início",
        "nav_games": "Jogos",
        "nav_predictions": "Palpites",
        "nav_ranking": "Ranking",
        "nav_rules": "Regras",
        "nav_competitors": "Competidores",
        "nav_admin": "Admin",
        "nav_results": "Resultados",
        "nav_groups": "Grupos",
        "nav_simulation": "Simulação",
        "my_predictions": "Meus palpites",
        "group_label": "Grupo",
        "highlight_team": "Seleção em destaque",
        "highlight_team_auto": "Automático pelo idioma ({team})",
        "save_highlight_team": "Aplicar selección",
        "logout": "Sair",
        "account_deletion": "Solicitar exclusão de conta e dados",
        "footer_note": "Bolão Copa do Mundo FIFA 2026 — Todos os horários em Brasília (BRT/UTC-3)",
        "dashboard": "Dashboard",
        "invite_friend": "Convidar amigo",
        "copy_invite": "Copiar convite",
        "copied": "Copiado",
        "confirm_email_title": "Confirme seu e-mail.",
        "confirm_email_needed": "A confirmação é necessária para receber os relatórios automáticos das rodadas (verifique spam).",
        "resend_confirmation": "Reenviar confirmação",
        "competitors": "Competidores",
        "games": "Jogos",
        "completed": "Realizados",
        "pending": "Pendentes",
        "predictions_sent": "Palpites Enviados",
        "predictions_pending": "Palpites Pendentes",
        "current_podium": "Pódio Atual",
        "overall_ranking": "Ranking geral",
        "stage": "Etapa",
        "overall": "Geral",
        "points": "pontos",
        "no_results_yet": "Nenhum resultado lançado ainda.",
        "next_game": "Próximo Jogo",
        "no_scheduled_game": "Nenhum jogo agendado.",
        "next_deadline": "Próximo Prazo",
        "deadline_for": "Prazo para:",
        "no_upcoming_deadline": "Sem prazo iminente.",
        "upcoming_games": "Próximos Jogos",
        "date": "Data",
        "time_brt": "Hora (BRT)",
        "phase": "Fase",
        "team_a": "Time A",
        "team_b": "Time B",
        "location": "Local",
        "stadium": "Estádio",
        "city": "Cidade",
        "knockout_short": "M-M",
        "knockout": "Mata-mata",
        "yes": "Sim",
        "no": "Não",
        "prediction_deadline_short": "Prazo Palpite",
        "action": "Ação",
        "total_games": "Total: {count} jogo(s)",
        "game_status": "Status Jogo",
        "my_prediction": "Meu Palpite",
        "prediction_deadline": "Prazo Palpite",
        "scored": "Pontuado",
        "result": "Resultado",
        "in_progress": "Em andamento",
        "locked": "Bloqueado",
        "scheduled": "Agendado",
        "open_for_predictions": "Aberto para palpites",
        "cancelled_changed": "Cancelado/Alterado",
        "no_prediction": "Sem palpite",
        "no_upcoming_games": "Nenhum jogo próximo encontrado.",
        "stage_groups": "Fase de Grupos",
        "stage_knockout": "Mata-mata ate a Final",
        "phase_round_32": "Rodada de 32",
        "phase_round_16": "Oitavas de Final",
        "phase_quarterfinals": "Quartas de Final",
        "phase_semifinal": "Semifinal",
        "phase_third_place": "Terceiro Lugar",
        "phase_final": "Final",
        "world_cup_group": "Grupo {group}",
        "other_group": "Outros",
        "round_report_subject": "Relatório da {round_label} - Bolão Copa 2026",
        "hello_name": "Olá, {name}!",
        "round_report_heading": "Relatório da {round_label}:",
        "your_round_points": "Seus pontos na rodada: {points}",
        "exact_scores_round": "Placares exatos na rodada: {count}",
        "your_stage_position": "Sua posição na etapa ({stage_label}): {position}",
        "your_overall_position": "Sua posição no ranking geral: {position}",
        "round_games": "Jogos da rodada:",
        "top5_stage": "Top 5 da etapa - {stage_label}:",
        "top5_overall": "Top 5 geral:",
        "access_app_details": "Acesse o app para ver todos os detalhes.",
        "invite_friend_line": "Convide um amigo para participar:",
        "predictions_title": "Palpites",
        "goals_a": "Gols A",
        "goals_b": "Gols B",
        "qualified_knockout": "Clasf. (mata-mata)",
        "comparison": "Comparação",
        "deadline": "Prazo",
        "status": "Status",
        "exact_score": "Placar exato",
        "winner_plus_margin": "Vencedor + saldo",
        "winner_correct": "Vencedor correto",
        "winner": "Vencedor",
        "loser": "Perdedor",
        "goals_correct": "Acertou gols",
        "missed": "Não acertou",
        "qualified_correct": "Classificado correto",
        "waiting": "Aguardando",
        "sent": "Enviado",
        "open": "Aberto",
        "exact": "Exato",
        "fill_empty_tab": "Preencher vazios desta aba",
        "clear_future_tab": "Limpar futuros desta aba",
        "no_games_found": "Nenhum jogo encontrado.",
        "save_predictions": "Salvar Palpites",
        "editable_note": "Apenas jogos futuros e dentro do prazo permanecem editáveis.",
        "unsaved_changes": "Alterações não salvas",
        "unsaved_body": "Você fez alterações nos palpites. Deseja salvar antes de sair desta página?",
        "save": "Salvar",
        "leave_without_saving": "Sair sem salvar",
        "stay_on_page": "Permanecer na página",
        "clear_confirm": "Limpar os palpites ainda editáveis apenas desta aba? Esta ação será salva agora.",
        "rules_title": "Regras do Bolão",
        "rules_heading": "Regras e Informações Úteis",
        "rules_subtitle": "Resumo rápido de pontuação, prazos, critérios de desempate e funcionamento geral do bolão.",
        "scoring_rules": "Regras de Pontuação",
        "situation": "Situação",
        "exact_score_rule": "Placar exato",
        "winner_margin_rule": "Vencedor correto + saldo correto",
        "winner_rule": "Vencedor correto",
        "draw_rule": "Empate correto com placar diferente",
        "one_team_goals_rule": "Acerto de gols de um dos times",
        "no_relevant_hits": "Sem acertos relevantes",
        "knockout_bonus_rule": "Bônus por classificado correto no mata-mata",
        "tie_breakers": "Critérios de Desempate",
        "tie_1": "Maior pontuação total.",
        "tie_2": "Maior quantidade de placares exatos.",
        "tie_3": "Maior quantidade de vencedores corretos.",
        "tie_4": "Maior quantidade de saldos corretos.",
        "tie_5": "Maior quantidade de classificados corretos.",
        "tie_6": "Maior quantidade de palpites enviados.",
        "tie_7": "Menor quantidade de palpites não enviados.",
        "tie_8": "Ordem alfabética do apelido.",
        "deadlines_times": "Prazos e Horários",
        "deadline_1": "Todos os horários exibidos no sistema estão em Brasília.",
        "deadline_2": "O prazo do palpite encerra às 23:59 do dia anterior ao jogo.",
        "deadline_3": "Depois do prazo, o palpite fica bloqueado para edição.",
        "deadline_4": "Jogos sem palpite dentro do prazo contam como não enviados.",
        "deadline_5": "Resultados aparecem na tela de palpites para comparação imediata.",
        "ranking_stages": "Ranking por Etapas",
        "ranking_stage_overall": "soma todos os jogos da Copa.",
        "ranking_stage_groups": "considera apenas os jogos da fase de grupos.",
        "ranking_stage_knockout": "recomeça do zero na etapa eliminatória e segue até a final.",
        "ranking_stage_ties": "Os critérios de desempate são os mesmos em todas as etapas.",
        "how_to_read_predictions": "Como Ler a Tela de Palpites",
        "read_1": "Status Aberto: ainda dá tempo de editar.",
        "read_2": "Status Enviado: palpite salvo dentro do prazo.",
        "read_3": "Status Resultado: resultado oficial já lançado.",
        "read_4": "Status Pontuado: pontos calculados para o jogo.",
        "read_5": "Coluna Resultado: mostra o placar oficial.",
        "read_6": "Coluna Comparação: mostra se você acertou placar, vencedor, saldo ou classificado.",
        "auto_results": "Atualização de Resultados (Automática)",
        "auto_1": "Os resultados podem ser sincronizados automaticamente por API externa confiável.",
        "auto_2": "A sincronização considera apenas jogos finalizados na fonte oficial.",
        "auto_3": "Se o resultado recebido for igual ao atual, nada é alterado (processo idempotente).",
        "auto_4": "Quando houver alteração de placar/classificado, o sistema recalcula automaticamente a pontuação do jogo.",
        "auto_5": "Se algum jogo não puder ser mapeado com segurança, ele não é alterado automaticamente.",
        "auto_6": "Administradores podem executar a sincronização manual pelo botão Sincronizar API na tela de Resultados.",
        "auto_7": "A manutenção manual de resultados continua disponível para ajustes pontuais.",
        "useful_info": "Informações Úteis",
        "groups_info": "Usuários veem os palpites dos participantes do mesmo grupo, mas podem editar apenas os próprios palpites.",
        "ranking_info": "O ranking geral soma todos os jogos pontuados. O ranking por fase considera apenas os jogos da fase selecionada.",
        "simulation_info": "Administradores podem usar a simulação para adiantar datas e gerar resultados aleatórios para validar o funcionamento do sistema.",
        "data_deletion": "Exclusão de Dados",
        "data_deletion_info": "Usuários podem solicitar a exclusão de conta e dados pelo link",
        "confirm_email_subject": "Confirme seu e-mail - Bolão Copa 2026",
        "confirm_email_text": "Olá, {name}!\n\nConfirme seu e-mail para receber os relatórios das rodadas do Bolão Copa 2026:\n{url}\n\nSe você não fez este cadastro, ignore esta mensagem.",
        "confirm_email_html": "<p>Olá, {name}!</p><p>Confirme seu e-mail para receber os relatórios das rodadas do Bolão Copa 2026.</p><p><a href=\"{url}\">Confirmar e-mail</a></p><p>Se você não fez este cadastro, ignore esta mensagem.</p>",
        "reset_password_subject": "Redefina sua senha - Bolão Copa 2026",
        "reset_password_text": "Olá, {name}!\n\nRecebemos uma solicitação para redefinir sua senha no Bolão Copa 2026.\nAcesse este link em até 1 hora para criar uma nova senha:\n{url}\n\nSe você não solicitou esta alteração, ignore esta mensagem.",
        "reset_password_html": "<p>Olá, {name}!</p><p>Recebemos uma solicitação para redefinir sua senha no Bolão Copa 2026.</p><p><a href=\"{url}\">Criar nova senha</a></p><p>Este link expira em 1 hora. Se você não solicitou esta alteração, ignore esta mensagem.</p>",
    },
    "en": {
        "language_label": "Language",
        "login_title": "Sign in - World Cup Pool 2026",
        "app_name": "World Cup Pool 2026",
        "system_subtitle": "Prediction System",
        "email": "Email",
        "password": "Password",
        "sign_in": "Sign in",
        "signing_in": "Signing in...",
        "forgot_password": "Forgot password?",
        "no_account": "Don't have an account?",
        "register_here": "Register here",
        "logged_out": "You have signed out.",
        "register_title": "Register - World Cup Pool 2026",
        "register_heading": "Register - World Cup Pool 2026",
        "name": "Name",
        "nickname": "Nickname",
        "required": "*",
        "nickname_placeholder": "What should we call you?",
        "group": "Group",
        "optional": "(optional)",
        "no_group": "-- No group --",
        "private": "private",
        "group_help": "Choose an open group. Private groups require a code.",
        "private_group_code": "Private group code",
        "private_group_code_placeholder": "Required only for private groups",
        "register": "Register",
        "registering": "Registering...",
        "has_account": "Already have an account?",
        "sign_in_here": "Sign in here",
        "recover_password_title": "Recover password - World Cup Pool 2026",
        "recover_password": "Recover password",
        "recover_password_subtitle": "Enter your account email",
        "send_link": "Send link",
        "sending": "Sending...",
        "remembered_password": "Remembered your password?",
        "new_password_title": "New password - World Cup Pool 2026",
        "new_password_heading": "Create a new password",
        "new_password": "New password",
        "confirm_new_password": "Confirm new password",
        "save_password": "Save password",
        "saving": "Saving...",
        "back_to_login": "Back to sign in",
        "nav_home": "Home",
        "nav_games": "Games",
        "nav_predictions": "Predictions",
        "nav_ranking": "Ranking",
        "nav_rules": "Rules",
        "nav_competitors": "Competitors",
        "nav_admin": "Admin",
        "nav_results": "Results",
        "nav_groups": "Groups",
        "nav_simulation": "Simulation",
        "my_predictions": "My predictions",
        "group_label": "Group",
        "highlight_team": "Highlighted team",
        "highlight_team_auto": "Automatic by language ({team})",
        "save_highlight_team": "Apply highlight",
        "logout": "Sign out",
        "account_deletion": "Request account and data deletion",
        "footer_note": "FIFA World Cup Pool 2026 — All times in Brasília (BRT/UTC-3)",
        "dashboard": "Dashboard",
        "invite_friend": "Invite a friend",
        "copy_invite": "Copy invite",
        "copied": "Copied",
        "confirm_email_title": "Confirm your email.",
        "confirm_email_needed": "Confirmation is required to receive automatic round reports (check spam).",
        "resend_confirmation": "Resend confirmation",
        "competitors": "Competitors",
        "games": "Games",
        "completed": "Completed",
        "pending": "Pending",
        "predictions_sent": "Predictions Sent",
        "predictions_pending": "Pending Predictions",
        "current_podium": "Current Podium",
        "overall_ranking": "Overall ranking",
        "stage": "Stage",
        "overall": "Overall",
        "points": "points",
        "no_results_yet": "No results entered yet.",
        "next_game": "Next Game",
        "no_scheduled_game": "No scheduled game.",
        "next_deadline": "Next Deadline",
        "deadline_for": "Deadline for:",
        "no_upcoming_deadline": "No upcoming deadline.",
        "upcoming_games": "Upcoming Games",
        "date": "Date",
        "time_brt": "Time (BRT)",
        "phase": "Stage",
        "team_a": "Team A",
        "team_b": "Team B",
        "location": "Location",
        "stadium": "Stadium",
        "city": "City",
        "knockout_short": "KO",
        "knockout": "Knockout",
        "yes": "Yes",
        "no": "No",
        "prediction_deadline_short": "Prediction Deadline",
        "action": "Action",
        "total_games": "Total: {count} game(s)",
        "game_status": "Game Status",
        "my_prediction": "My Prediction",
        "prediction_deadline": "Prediction Deadline",
        "scored": "Scored",
        "result": "Result",
        "in_progress": "In progress",
        "locked": "Locked",
        "scheduled": "Scheduled",
        "open_for_predictions": "Open for predictions",
        "cancelled_changed": "Cancelled/Changed",
        "no_prediction": "No prediction",
        "no_upcoming_games": "No upcoming games found.",
        "stage_groups": "Group Stage",
        "stage_knockout": "Knockout Stage through the Final",
        "phase_round_32": "Round of 32",
        "phase_round_16": "Round of 16",
        "phase_quarterfinals": "Quarterfinals",
        "phase_semifinal": "Semifinal",
        "phase_third_place": "Third Place",
        "phase_final": "Final",
        "world_cup_group": "Group {group}",
        "other_group": "Other",
        "round_report_subject": "Report for {round_label} - World Cup Pool 2026",
        "hello_name": "Hello, {name}!",
        "round_report_heading": "Report for {round_label}:",
        "your_round_points": "Your points this round: {points}",
        "exact_scores_round": "Exact scores this round: {count}",
        "your_stage_position": "Your position in this stage ({stage_label}): {position}",
        "your_overall_position": "Your overall ranking position: {position}",
        "round_games": "Round games:",
        "top5_stage": "Top 5 for this stage - {stage_label}:",
        "top5_overall": "Overall Top 5:",
        "access_app_details": "Open the app to see all details.",
        "invite_friend_line": "Invite a friend to join:",
        "predictions_title": "Predictions",
        "goals_a": "Goals A",
        "goals_b": "Goals B",
        "qualified_knockout": "Qualified (knockout)",
        "comparison": "Comparison",
        "deadline": "Deadline",
        "status": "Status",
        "exact_score": "Exact score",
        "winner_plus_margin": "Winner + margin",
        "winner_correct": "Correct winner",
        "winner": "Winner",
        "loser": "Loser",
        "goals_correct": "Correct goals",
        "missed": "No hit",
        "qualified_correct": "Correct qualifier",
        "waiting": "Waiting",
        "sent": "Sent",
        "open": "Open",
        "exact": "Exact",
        "fill_empty_tab": "Fill empty predictions in this tab",
        "clear_future_tab": "Clear future predictions in this tab",
        "no_games_found": "No games found.",
        "save_predictions": "Save Predictions",
        "editable_note": "Only future games within the deadline remain editable.",
        "unsaved_changes": "Unsaved changes",
        "unsaved_body": "You changed your predictions. Do you want to save before leaving this page?",
        "save": "Save",
        "leave_without_saving": "Leave without saving",
        "stay_on_page": "Stay on this page",
        "clear_confirm": "Clear only editable predictions in this tab? This action will be saved now.",
        "rules_title": "Pool Rules",
        "rules_heading": "Rules and Useful Information",
        "rules_subtitle": "Quick summary of scoring, deadlines, tie-breakers, and how the pool works.",
        "scoring_rules": "Scoring Rules",
        "situation": "Situation",
        "exact_score_rule": "Exact score",
        "winner_margin_rule": "Correct winner + correct margin",
        "winner_rule": "Correct winner",
        "draw_rule": "Correct draw with different score",
        "one_team_goals_rule": "Correct goals for one team",
        "no_relevant_hits": "No relevant hits",
        "knockout_bonus_rule": "Bonus for correct qualifier in knockout games",
        "tie_breakers": "Tie-Breakers",
        "tie_1": "Highest total points.",
        "tie_2": "Most exact scores.",
        "tie_3": "Most correct winners.",
        "tie_4": "Most correct margins.",
        "tie_5": "Most correct qualifiers.",
        "tie_6": "Most submitted predictions.",
        "tie_7": "Fewest missed predictions.",
        "tie_8": "Alphabetical order by nickname.",
        "deadlines_times": "Deadlines and Times",
        "deadline_1": "All times shown in the system are Brasília time.",
        "deadline_2": "Prediction deadline is 23:59 on the day before the match.",
        "deadline_3": "After the deadline, the prediction is locked for editing.",
        "deadline_4": "Games without a prediction before the deadline count as missed.",
        "deadline_5": "Results appear on the predictions screen for immediate comparison.",
        "ranking_stages": "Ranking by Stage",
        "ranking_stage_overall": "adds all World Cup games.",
        "ranking_stage_groups": "counts only group stage games.",
        "ranking_stage_knockout": "starts from zero in the knockout stage and runs through the final.",
        "ranking_stage_ties": "Tie-breaker criteria are the same in every stage.",
        "how_to_read_predictions": "How to Read the Predictions Screen",
        "read_1": "Open status: there is still time to edit.",
        "read_2": "Sent status: prediction saved before the deadline.",
        "read_3": "Result status: official result already entered.",
        "read_4": "Scored status: points calculated for the game.",
        "read_5": "Result column: shows the official score.",
        "read_6": "Comparison column: shows whether you got the score, winner, margin, or qualifier right.",
        "auto_results": "Result Updates (Automatic)",
        "auto_1": "Results may be synchronized automatically from a reliable external API.",
        "auto_2": "Synchronization considers only finished games in the official source.",
        "auto_3": "If the received result is the same as the current one, nothing changes.",
        "auto_4": "When score/qualifier changes, the system automatically recalculates game points.",
        "auto_5": "If a game cannot be safely mapped, it is not changed automatically.",
        "auto_6": "Admins can run manual synchronization from the Sync API button on the Results screen.",
        "auto_7": "Manual result maintenance remains available for occasional adjustments.",
        "useful_info": "Useful Information",
        "groups_info": "Users see predictions from participants in the same group, but can edit only their own predictions.",
        "ranking_info": "The overall ranking adds all scored games. Stage ranking considers only games from the selected stage.",
        "simulation_info": "Admins can use simulation to move dates forward and generate random results to validate the system.",
        "data_deletion": "Data Deletion",
        "data_deletion_info": "Users can request account and data deletion through the link",
        "confirm_email_subject": "Confirm your email - World Cup Pool 2026",
        "confirm_email_text": "Hello, {name}!\n\nConfirm your email to receive round reports from World Cup Pool 2026:\n{url}\n\nIf you did not create this account, ignore this message.",
        "confirm_email_html": "<p>Hello, {name}!</p><p>Confirm your email to receive round reports from World Cup Pool 2026.</p><p><a href=\"{url}\">Confirm email</a></p><p>If you did not create this account, ignore this message.</p>",
        "reset_password_subject": "Reset your password - World Cup Pool 2026",
        "reset_password_text": "Hello, {name}!\n\nWe received a request to reset your World Cup Pool 2026 password.\nUse this link within 1 hour to create a new password:\n{url}\n\nIf you did not request this change, ignore this message.",
        "reset_password_html": "<p>Hello, {name}!</p><p>We received a request to reset your World Cup Pool 2026 password.</p><p><a href=\"{url}\">Create new password</a></p><p>This link expires in 1 hour. If you did not request this change, ignore this message.</p>",
    },
    "es": {
        "language_label": "Idioma",
        "login_title": "Iniciar sesión - Quiniela Mundial 2026",
        "app_name": "Quiniela Mundial 2026",
        "system_subtitle": "Sistema de Pronósticos",
        "email": "Correo electrónico",
        "password": "Contraseña",
        "sign_in": "Iniciar sesión",
        "signing_in": "Ingresando...",
        "forgot_password": "Olvidé mi contraseña",
        "no_account": "¿Aún no tienes cuenta?",
        "register_here": "Regístrate aquí",
        "logged_out": "Has cerrado sesión.",
        "register_title": "Registro - Quiniela Mundial 2026",
        "register_heading": "Registro - Quiniela Mundial 2026",
        "name": "Nombre",
        "nickname": "Apodo",
        "required": "*",
        "nickname_placeholder": "¿Cómo quieres que te llamemos?",
        "group": "Grupo",
        "optional": "(opcional)",
        "no_group": "-- Sin grupo --",
        "private": "privado",
        "group_help": "Elige un grupo abierto. Los grupos privados requieren código.",
        "private_group_code": "Código del grupo privado",
        "private_group_code_placeholder": "Necesario solo para grupos privados",
        "register": "Registrarse",
        "registering": "Registrando...",
        "has_account": "¿Ya tienes cuenta?",
        "sign_in_here": "Entra aquí",
        "recover_password_title": "Recuperar contraseña - Quiniela Mundial 2026",
        "recover_password": "Recuperar contraseña",
        "recover_password_subtitle": "Ingresa el correo de tu cuenta",
        "send_link": "Enviar enlace",
        "sending": "Enviando...",
        "remembered_password": "¿Recordaste tu contraseña?",
        "new_password_title": "Nueva contraseña - Quiniela Mundial 2026",
        "new_password_heading": "Crear nueva contraseña",
        "new_password": "Nueva contraseña",
        "confirm_new_password": "Confirmar nueva contraseña",
        "save_password": "Guardar contraseña",
        "saving": "Guardando...",
        "back_to_login": "Volver al inicio de sesión",
        "nav_home": "Inicio",
        "nav_games": "Partidos",
        "nav_predictions": "Pronósticos",
        "nav_ranking": "Ranking",
        "nav_rules": "Reglas",
        "nav_competitors": "Competidores",
        "nav_admin": "Admin",
        "nav_results": "Resultados",
        "nav_groups": "Grupos",
        "nav_simulation": "Simulación",
        "my_predictions": "Mis pronósticos",
        "group_label": "Grupo",
        "highlight_team": "Selección destacada",
        "highlight_team_auto": "Automático por idioma ({team})",
        "save_highlight_team": "Aplicar destaque",
        "logout": "Salir",
        "account_deletion": "Solicitar eliminación de cuenta y datos",
        "footer_note": "Quiniela Mundial FIFA 2026 — Todos los horarios en Brasilia (BRT/UTC-3)",
        "dashboard": "Panel",
        "invite_friend": "Invitar a un amigo",
        "copy_invite": "Copiar invitación",
        "copied": "Copiado",
        "confirm_email_title": "Confirma tu correo.",
        "confirm_email_needed": "La confirmación es necesaria para recibir los informes automáticos de las rondas (revisa spam).",
        "resend_confirmation": "Reenviar confirmación",
        "competitors": "Competidores",
        "games": "Partidos",
        "completed": "Finalizados",
        "pending": "Pendientes",
        "predictions_sent": "Pronósticos Enviados",
        "predictions_pending": "Pronósticos Pendientes",
        "current_podium": "Podio Actual",
        "overall_ranking": "Ranking general",
        "stage": "Etapa",
        "overall": "General",
        "points": "puntos",
        "no_results_yet": "Aún no hay resultados cargados.",
        "next_game": "Próximo Partido",
        "no_scheduled_game": "No hay partidos programados.",
        "next_deadline": "Próximo Plazo",
        "deadline_for": "Plazo para:",
        "no_upcoming_deadline": "Sin plazo próximo.",
        "upcoming_games": "Próximos Partidos",
        "date": "Fecha",
        "time_brt": "Hora (BRT)",
        "phase": "Fase",
        "team_a": "Equipo A",
        "team_b": "Equipo B",
        "location": "Lugar",
        "stadium": "Estadio",
        "city": "Ciudad",
        "knockout_short": "Elim.",
        "knockout": "Eliminatoria",
        "yes": "Sí",
        "no": "No",
        "prediction_deadline_short": "Plazo del Pronóstico",
        "action": "Acción",
        "total_games": "Total: {count} partido(s)",
        "game_status": "Estado del Partido",
        "my_prediction": "Mi Pronóstico",
        "prediction_deadline": "Plazo del Pronóstico",
        "scored": "Puntuado",
        "result": "Resultado",
        "in_progress": "En curso",
        "locked": "Bloqueado",
        "scheduled": "Programado",
        "open_for_predictions": "Abierto para pronósticos",
        "cancelled_changed": "Cancelado/Modificado",
        "no_prediction": "Sin pronóstico",
        "no_upcoming_games": "No se encontraron próximos partidos.",
        "stage_groups": "Fase de Grupos",
        "stage_knockout": "Eliminatorias hasta la Final",
        "phase_round_32": "Ronda de 32",
        "phase_round_16": "Octavos de Final",
        "phase_quarterfinals": "Cuartos de Final",
        "phase_semifinal": "Semifinal",
        "phase_third_place": "Tercer Puesto",
        "phase_final": "Final",
        "world_cup_group": "Grupo {group}",
        "other_group": "Otros",
        "round_report_subject": "Informe de {round_label} - Quiniela Mundial 2026",
        "hello_name": "Hola, {name}!",
        "round_report_heading": "Informe de {round_label}:",
        "your_round_points": "Tus puntos en la ronda: {points}",
        "exact_scores_round": "Marcadores exactos en la ronda: {count}",
        "your_stage_position": "Tu posición en la etapa ({stage_label}): {position}",
        "your_overall_position": "Tu posición en el ranking general: {position}",
        "round_games": "Partidos de la ronda:",
        "top5_stage": "Top 5 de la etapa - {stage_label}:",
        "top5_overall": "Top 5 general:",
        "access_app_details": "Abre la app para ver todos los detalles.",
        "invite_friend_line": "Invita a un amigo a participar:",
        "predictions_title": "Pronósticos",
        "goals_a": "Goles A",
        "goals_b": "Goles B",
        "qualified_knockout": "Clasif. (eliminatoria)",
        "comparison": "Comparación",
        "deadline": "Plazo",
        "status": "Estado",
        "exact_score": "Marcador exacto",
        "winner_plus_margin": "Ganador + diferencia",
        "winner_correct": "Ganador correcto",
        "winner": "Ganador",
        "loser": "Perdedor",
        "goals_correct": "Goles correctos",
        "missed": "No acertó",
        "qualified_correct": "Clasificado correcto",
        "waiting": "Esperando",
        "sent": "Enviado",
        "open": "Abierto",
        "exact": "Exacto",
        "fill_empty_tab": "Completar vacíos de esta pestaña",
        "clear_future_tab": "Limpiar futuros de esta pestaña",
        "no_games_found": "No se encontraron partidos.",
        "save_predictions": "Guardar Pronósticos",
        "editable_note": "Solo los partidos futuros dentro del plazo permanecen editables.",
        "unsaved_changes": "Cambios no guardados",
        "unsaved_body": "Hiciste cambios en tus pronósticos. ¿Quieres guardar antes de salir de esta página?",
        "save": "Guardar",
        "leave_without_saving": "Salir sin guardar",
        "stay_on_page": "Permanecer en la página",
        "clear_confirm": "¿Limpiar solo los pronósticos editables de esta pestaña? Esta acción se guardará ahora.",
        "rules_title": "Reglas de la Quiniela",
        "rules_heading": "Reglas e Información Útil",
        "rules_subtitle": "Resumen rápido de puntuación, plazos, criterios de desempate y funcionamiento general de la quiniela.",
        "scoring_rules": "Reglas de Puntuación",
        "situation": "Situación",
        "exact_score_rule": "Marcador exacto",
        "winner_margin_rule": "Ganador correcto + diferencia correcta",
        "winner_rule": "Ganador correcto",
        "draw_rule": "Empate correcto con marcador diferente",
        "one_team_goals_rule": "Acierto de goles de uno de los equipos",
        "no_relevant_hits": "Sin aciertos relevantes",
        "knockout_bonus_rule": "Bono por clasificado correcto en eliminatorias",
        "tie_breakers": "Criterios de Desempate",
        "tie_1": "Mayor puntuación total.",
        "tie_2": "Mayor cantidad de marcadores exactos.",
        "tie_3": "Mayor cantidad de ganadores correctos.",
        "tie_4": "Mayor cantidad de diferencias correctas.",
        "tie_5": "Mayor cantidad de clasificados correctos.",
        "tie_6": "Mayor cantidad de pronósticos enviados.",
        "tie_7": "Menor cantidad de pronósticos no enviados.",
        "tie_8": "Orden alfabético del apodo.",
        "deadlines_times": "Plazos y Horarios",
        "deadline_1": "Todos los horarios mostrados en el sistema están en Brasilia.",
        "deadline_2": "El plazo del pronóstico termina a las 23:59 del día anterior al partido.",
        "deadline_3": "Después del plazo, el pronóstico queda bloqueado para edición.",
        "deadline_4": "Partidos sin pronóstico dentro del plazo cuentan como no enviados.",
        "deadline_5": "Los resultados aparecen en la pantalla de pronósticos para comparación inmediata.",
        "ranking_stages": "Ranking por Etapas",
        "ranking_stage_overall": "suma todos los partidos del Mundial.",
        "ranking_stage_groups": "considera solo los partidos de la fase de grupos.",
        "ranking_stage_knockout": "recomienza desde cero en la etapa eliminatoria y sigue hasta la final.",
        "ranking_stage_ties": "Los criterios de desempate son los mismos en todas las etapas.",
        "how_to_read_predictions": "Cómo Leer la Pantalla de Pronósticos",
        "read_1": "Estado Abierto: aún hay tiempo para editar.",
        "read_2": "Estado Enviado: pronóstico guardado dentro del plazo.",
        "read_3": "Estado Resultado: resultado oficial ya cargado.",
        "read_4": "Estado Puntuado: puntos calculados para el partido.",
        "read_5": "Columna Resultado: muestra el marcador oficial.",
        "read_6": "Columna Comparación: muestra si acertaste marcador, ganador, diferencia o clasificado.",
        "auto_results": "Actualización de Resultados (Automática)",
        "auto_1": "Los resultados pueden sincronizarse automáticamente desde una API externa confiable.",
        "auto_2": "La sincronización considera solo partidos finalizados en la fuente oficial.",
        "auto_3": "Si el resultado recibido es igual al actual, no se modifica nada.",
        "auto_4": "Cuando cambia el marcador/clasificado, el sistema recalcula automáticamente la puntuación del partido.",
        "auto_5": "Si un partido no puede mapearse con seguridad, no se modifica automáticamente.",
        "auto_6": "Los administradores pueden ejecutar la sincronización manual desde el botón Sincronizar API en Resultados.",
        "auto_7": "El mantenimiento manual de resultados sigue disponible para ajustes puntuales.",
        "useful_info": "Información Útil",
        "groups_info": "Los usuarios ven los pronósticos de participantes del mismo grupo, pero solo pueden editar sus propios pronósticos.",
        "ranking_info": "El ranking general suma todos los partidos puntuados. El ranking por fase considera solo los partidos de la fase seleccionada.",
        "simulation_info": "Los administradores pueden usar la simulación para adelantar fechas y generar resultados aleatorios para validar el sistema.",
        "data_deletion": "Eliminación de Datos",
        "data_deletion_info": "Los usuarios pueden solicitar la eliminación de cuenta y datos mediante el enlace",
        "confirm_email_subject": "Confirma tu correo - Quiniela Mundial 2026",
        "confirm_email_text": "Hola, {name}!\n\nConfirma tu correo para recibir los informes de las rondas de la Quiniela Mundial 2026:\n{url}\n\nSi no creaste esta cuenta, ignora este mensaje.",
        "confirm_email_html": "<p>Hola, {name}!</p><p>Confirma tu correo para recibir los informes de las rondas de la Quiniela Mundial 2026.</p><p><a href=\"{url}\">Confirmar correo</a></p><p>Si no creaste esta cuenta, ignora este mensaje.</p>",
        "reset_password_subject": "Restablece tu contraseña - Quiniela Mundial 2026",
        "reset_password_text": "Hola, {name}!\n\nRecibimos una solicitud para restablecer tu contraseña de la Quiniela Mundial 2026.\nUsa este enlace dentro de 1 hora para crear una nueva contraseña:\n{url}\n\nSi no solicitaste este cambio, ignora este mensaje.",
        "reset_password_html": "<p>Hola, {name}!</p><p>Recibimos una solicitud para restablecer tu contraseña de la Quiniela Mundial 2026.</p><p><a href=\"{url}\">Crear nueva contraseña</a></p><p>Este enlace expira en 1 hora. Si no solicitaste este cambio, ignora este mensaje.</p>",
    },
}

TRANSLATIONS["fr"] = {**TRANSLATIONS["en"], **{
    "language_label": "Langue",
    "login_title": "Connexion - Pool Coupe du Monde 2026",
    "app_name": "Pool Coupe du Monde 2026",
    "system_subtitle": "SystÃ¨me de pronostics",
    "email": "E-mail",
    "password": "Mot de passe",
    "sign_in": "Se connecter",
    "signing_in": "Connexion...",
    "forgot_password": "Mot de passe oubliÃ© ?",
    "no_account": "Pas encore de compte ?",
    "register_here": "Inscrivez-vous ici",
    "logged_out": "Vous Ãªtes dÃ©connectÃ©.",
    "register_title": "Inscription - Pool Coupe du Monde 2026",
    "register_heading": "Inscription - Pool Coupe du Monde 2026",
    "name": "Nom",
    "nickname": "Pseudo",
    "nickname_placeholder": "Comment souhaitez-vous Ãªtre appelÃ© ?",
    "group": "Groupe",
    "optional": "(optionnel)",
    "no_group": "-- Sans groupe --",
    "private": "privÃ©",
    "group_help": "Choisissez un groupe ouvert. Les groupes privÃ©s exigent un code.",
    "private_group_code": "Code du groupe privÃ©",
    "private_group_code_placeholder": "NÃ©cessaire uniquement pour les groupes privÃ©s",
    "register": "S'inscrire",
    "registering": "Inscription...",
    "has_account": "Vous avez dÃ©jÃ  un compte ?",
    "sign_in_here": "Connectez-vous ici",
    "recover_password_title": "RÃ©cupÃ©rer le mot de passe - Pool Coupe du Monde 2026",
    "recover_password": "RÃ©cupÃ©rer le mot de passe",
    "recover_password_subtitle": "Indiquez l'e-mail de votre compte",
    "send_link": "Envoyer le lien",
    "sending": "Envoi...",
    "remembered_password": "Mot de passe retrouvÃ© ?",
    "new_password_title": "Nouveau mot de passe - Pool Coupe du Monde 2026",
    "new_password_heading": "CrÃ©er un nouveau mot de passe",
    "new_password": "Nouveau mot de passe",
    "confirm_new_password": "Confirmer le nouveau mot de passe",
    "save_password": "Enregistrer le mot de passe",
    "saving": "Enregistrement...",
    "back_to_login": "Retour Ã  la connexion",
    "nav_home": "Accueil",
    "nav_games": "Matchs",
    "nav_predictions": "Pronostics",
    "nav_ranking": "Classement",
    "nav_rules": "RÃ¨gles",
    "nav_competitors": "Participants",
    "nav_results": "RÃ©sultats",
    "nav_groups": "Groupes",
    "nav_simulation": "Simulation",
    "my_predictions": "Mes pronostics",
    "group_label": "Groupe",
    "highlight_team": "Sélection mise en avant",
    "highlight_team_auto": "Automatique selon la langue ({team})",
    "save_highlight_team": "Appliquer",
    "logout": "Se dÃ©connecter",
    "account_deletion": "Demander la suppression du compte et des donnÃ©es",
    "footer_note": "Pool Coupe du Monde FIFA 2026 - Tous les horaires sont Ã  Brasilia (BRT/UTC-3)",
    "dashboard": "Tableau de bord",
    "invite_friend": "Inviter un ami",
    "copy_invite": "Copier l'invitation",
    "copied": "CopiÃ©",
    "confirm_email_title": "Confirmez votre e-mail.",
    "confirm_email_needed": "La confirmation est nÃ©cessaire pour recevoir les rapports automatiques des journÃ©es (vÃ©rifiez les spams).",
    "resend_confirmation": "Renvoyer la confirmation",
    "competitors": "Participants",
    "games": "Matchs",
    "completed": "TerminÃ©s",
    "pending": "En attente",
    "predictions_sent": "Pronostics envoyÃ©s",
    "predictions_pending": "Pronostics en attente",
    "current_podium": "Podium actuel",
    "overall_ranking": "Classement gÃ©nÃ©ral",
    "stage": "Phase",
    "overall": "GÃ©nÃ©ral",
    "points": "points",
    "no_results_yet": "Aucun rÃ©sultat saisi pour le moment.",
    "next_game": "Prochain match",
    "no_scheduled_game": "Aucun match programmÃ©.",
    "next_deadline": "Prochaine limite",
    "deadline_for": "Date limite pour :",
    "no_upcoming_deadline": "Aucune limite proche.",
    "upcoming_games": "Prochains matchs",
    "date": "Date",
    "time_brt": "Heure (BRT)",
    "phase": "Phase",
    "team_a": "Ã‰quipe A",
    "team_b": "Ã‰quipe B",
    "location": "Lieu",
    "stadium": "Stade",
    "city": "Ville",
    "knockout_short": "Ã‰lim.",
    "knockout": "Phase Ã  Ã©limination",
    "yes": "Oui",
    "no": "Non",
    "prediction_deadline_short": "Limite pronostic",
    "action": "Action",
    "total_games": "Total : {count} match(s)",
    "game_status": "Statut du match",
    "my_prediction": "Mon pronostic",
    "prediction_deadline": "Limite du pronostic",
    "scored": "ComptabilisÃ©",
    "result": "RÃ©sultat",
    "in_progress": "En cours",
    "locked": "BloquÃ©",
    "scheduled": "ProgrammÃ©",
    "open_for_predictions": "Ouvert aux pronostics",
    "cancelled_changed": "AnnulÃ©/ModifiÃ©",
    "no_prediction": "Sans pronostic",
    "no_upcoming_games": "Aucun prochain match trouvÃ©.",
    "stage_groups": "Phase de groupes",
    "stage_knockout": "Phase Ã  Ã©limination jusqu'Ã  la finale",
    "phase_round_32": "SeiziÃ¨mes de finale",
    "phase_round_16": "HuitiÃ¨mes de finale",
    "phase_quarterfinals": "Quarts de finale",
    "phase_semifinal": "Demi-finale",
    "phase_third_place": "TroisiÃ¨me place",
    "phase_final": "Finale",
    "world_cup_group": "Groupe {group}",
    "other_group": "Autres",
    "predictions_title": "Pronostics",
    "goals_a": "Buts A",
    "goals_b": "Buts B",
    "qualified_knockout": "QualifiÃ© (Ã©lim.)",
    "comparison": "Comparaison",
    "deadline": "Limite",
    "status": "Statut",
    "exact_score": "Score exact",
    "winner_plus_margin": "Vainqueur + Ã©cart",
    "winner_correct": "Bon vainqueur",
    "winner": "Vainqueur",
    "loser": "Perdant",
    "goals_correct": "Buts corrects",
    "missed": "RatÃ©",
    "qualified_correct": "QualifiÃ© correct",
    "waiting": "En attente",
    "sent": "EnvoyÃ©",
    "open": "Ouvert",
    "exact": "Exact",
    "fill_empty_tab": "Remplir les vides de cet onglet",
    "clear_future_tab": "Effacer les futurs de cet onglet",
    "no_games_found": "Aucun match trouvÃ©.",
    "save_predictions": "Enregistrer les pronostics",
    "editable_note": "Seuls les matchs futurs encore dans le dÃ©lai restent modifiables.",
    "unsaved_changes": "Modifications non enregistrÃ©es",
    "unsaved_body": "Vous avez modifiÃ© vos pronostics. Voulez-vous enregistrer avant de quitter cette page ?",
    "save": "Enregistrer",
    "leave_without_saving": "Quitter sans enregistrer",
    "stay_on_page": "Rester sur la page",
    "clear_confirm": "Effacer uniquement les pronostics modifiables de cet onglet ? Cette action sera enregistrÃ©e maintenant.",
    "rules_title": "RÃ¨gles du pool",
    "rules_heading": "RÃ¨gles et informations utiles",
    "rules_subtitle": "RÃ©sumÃ© rapide du barÃ¨me, des dÃ©lais, des critÃ¨res de dÃ©partage et du fonctionnement.",
    "scoring_rules": "RÃ¨gles de score",
    "situation": "Situation",
    "exact_score_rule": "Score exact",
    "winner_margin_rule": "Bon vainqueur + bon Ã©cart",
    "winner_rule": "Bon vainqueur",
    "draw_rule": "Match nul correct avec score diffÃ©rent",
    "one_team_goals_rule": "Buts corrects pour une Ã©quipe",
    "no_relevant_hits": "Aucun bon Ã©lÃ©ment",
    "knockout_bonus_rule": "Bonus pour qualifiÃ© correct en phase Ã  Ã©limination",
    "tie_breakers": "CritÃ¨res de dÃ©partage",
    "tie_1": "Plus grand total de points.",
    "tie_2": "Plus grand nombre de scores exacts.",
    "tie_3": "Plus grand nombre de vainqueurs corrects.",
    "tie_4": "Plus grand nombre d'Ã©carts corrects.",
    "tie_5": "Plus grand nombre de qualifiÃ©s corrects.",
    "tie_6": "Plus grand nombre de pronostics envoyÃ©s.",
    "tie_7": "Moins de pronostics non envoyÃ©s.",
    "tie_8": "Ordre alphabÃ©tique du pseudo.",
    "deadlines_times": "DÃ©lais et horaires",
    "deadline_1": "Tous les horaires affichÃ©s sont Ã  l'heure de Brasilia.",
    "deadline_2": "La limite de pronostic est 23:59 la veille du match.",
    "deadline_3": "AprÃ¨s la limite, le pronostic est bloquÃ©.",
    "deadline_4": "Les matchs sans pronostic dans le dÃ©lai comptent comme non envoyÃ©s.",
    "deadline_5": "Les rÃ©sultats apparaissent dans l'Ã©cran des pronostics pour comparaison.",
    "ranking_stages": "Classement par phase",
    "ranking_stage_overall": "additionne tous les matchs de la Coupe.",
    "ranking_stage_groups": "ne compte que les matchs de la phase de groupes.",
    "ranking_stage_knockout": "repart de zÃ©ro en phase Ã  Ã©limination et va jusqu'Ã  la finale.",
    "ranking_stage_ties": "Les critÃ¨res de dÃ©partage sont les mÃªmes dans toutes les phases.",
    "how_to_read_predictions": "Comment lire l'Ã©cran des pronostics",
    "read_1": "Statut Ouvert : il est encore temps de modifier.",
    "read_2": "Statut EnvoyÃ© : pronostic enregistrÃ© dans le dÃ©lai.",
    "read_3": "Statut RÃ©sultat : rÃ©sultat officiel dÃ©jÃ  saisi.",
    "read_4": "Statut ComptabilisÃ© : points calculÃ©s pour le match.",
    "read_5": "Colonne RÃ©sultat : affiche le score officiel.",
    "read_6": "Colonne Comparaison : indique si le score, le vainqueur, l'Ã©cart ou le qualifiÃ© est correct.",
    "auto_results": "Mise Ã  jour des rÃ©sultats (automatique)",
    "auto_1": "Les rÃ©sultats peuvent Ãªtre synchronisÃ©s automatiquement depuis une API externe fiable.",
    "auto_2": "La synchronisation ne prend en compte que les matchs terminÃ©s dans la source officielle.",
    "auto_3": "Si le rÃ©sultat reÃ§u est identique, rien n'est modifiÃ©.",
    "auto_4": "En cas de changement de score/qualifiÃ©, le systÃ¨me recalcule automatiquement les points.",
    "auto_5": "Si un match ne peut pas Ãªtre associÃ© avec sÃ©curitÃ©, il n'est pas modifiÃ© automatiquement.",
    "auto_6": "Les administrateurs peuvent lancer la synchronisation manuelle via le bouton Sync API.",
    "auto_7": "La maintenance manuelle des rÃ©sultats reste disponible pour des ajustements ponctuels.",
    "useful_info": "Informations utiles",
    "groups_info": "Les utilisateurs voient les pronostics des participants du mÃªme groupe, mais ne modifient que les leurs.",
    "ranking_info": "Le classement gÃ©nÃ©ral additionne tous les matchs comptabilisÃ©s. Le classement par phase ne prend que la phase sÃ©lectionnÃ©e.",
    "simulation_info": "Les administrateurs peuvent utiliser la simulation pour avancer les dates et valider le fonctionnement.",
    "data_deletion": "Suppression des donnÃ©es",
    "data_deletion_info": "Les utilisateurs peuvent demander la suppression du compte et des donnÃ©es via le lien",
    "round_report_subject": "Rapport de {round_label} - Pool Coupe du Monde 2026",
    "hello_name": "Bonjour, {name} !",
    "round_report_heading": "Rapport de {round_label} :",
    "your_round_points": "Vos points sur cette journÃ©e : {points}",
    "exact_scores_round": "Scores exacts sur cette journÃ©e : {count}",
    "your_stage_position": "Votre position dans la phase ({stage_label}) : {position}",
    "your_overall_position": "Votre position au classement gÃ©nÃ©ral : {position}",
    "round_games": "Matchs de la journÃ©e :",
    "top5_stage": "Top 5 de la phase - {stage_label} :",
    "top5_overall": "Top 5 gÃ©nÃ©ral :",
    "access_app_details": "Ouvrez l'app pour voir tous les dÃ©tails.",
    "invite_friend_line": "Invitez un ami Ã  participer :",
    "confirm_email_subject": "Confirmez votre e-mail - Pool Coupe du Monde 2026",
    "confirm_email_text": "Bonjour, {name} !\n\nConfirmez votre e-mail pour recevoir les rapports du Pool Coupe du Monde 2026 :\n{url}\n\nSi vous n'avez pas crÃ©Ã© ce compte, ignorez ce message.",
    "confirm_email_html": "<p>Bonjour, {name} !</p><p>Confirmez votre e-mail pour recevoir les rapports du Pool Coupe du Monde 2026.</p><p><a href=\"{url}\">Confirmer l'e-mail</a></p><p>Si vous n'avez pas crÃ©Ã© ce compte, ignorez ce message.</p>",
    "reset_password_subject": "RÃ©initialisez votre mot de passe - Pool Coupe du Monde 2026",
    "reset_password_text": "Bonjour, {name} !\n\nNous avons reÃ§u une demande de rÃ©initialisation de votre mot de passe.\nUtilisez ce lien dans l'heure pour crÃ©er un nouveau mot de passe :\n{url}\n\nSi vous n'avez pas demandÃ© ce changement, ignorez ce message.",
    "reset_password_html": "<p>Bonjour, {name} !</p><p>Nous avons reÃ§u une demande de rÃ©initialisation de votre mot de passe.</p><p><a href=\"{url}\">CrÃ©er un nouveau mot de passe</a></p><p>Ce lien expire dans 1 heure. Si vous n'avez pas demandÃ© ce changement, ignorez ce message.</p>",
}}

TRANSLATIONS["de"] = {**TRANSLATIONS["en"], **{
    "language_label": "Sprache",
    "login_title": "Anmelden - WM-Tippspiel 2026",
    "app_name": "WM-Tippspiel 2026",
    "system_subtitle": "Tippsystem",
    "email": "E-Mail",
    "password": "Passwort",
    "sign_in": "Anmelden",
    "signing_in": "Anmeldung...",
    "forgot_password": "Passwort vergessen?",
    "no_account": "Noch kein Konto?",
    "register_here": "Hier registrieren",
    "logged_out": "Sie wurden abgemeldet.",
    "register_title": "Registrierung - WM-Tippspiel 2026",
    "register_heading": "Registrierung - WM-Tippspiel 2026",
    "name": "Name",
    "nickname": "Spitzname",
    "nickname_placeholder": "Wie sollen wir Sie nennen?",
    "group": "Gruppe",
    "optional": "(optional)",
    "no_group": "-- Keine Gruppe --",
    "private": "privat",
    "group_help": "WÃ¤hlen Sie eine offene Gruppe. Private Gruppen benÃ¶tigen einen Code.",
    "private_group_code": "Code der privaten Gruppe",
    "private_group_code_placeholder": "Nur fÃ¼r private Gruppen erforderlich",
    "register": "Registrieren",
    "registering": "Registrierung...",
    "has_account": "Sie haben bereits ein Konto?",
    "sign_in_here": "Hier anmelden",
    "recover_password_title": "Passwort wiederherstellen - WM-Tippspiel 2026",
    "recover_password": "Passwort wiederherstellen",
    "recover_password_subtitle": "Geben Sie Ihre Konto-E-Mail ein",
    "send_link": "Link senden",
    "sending": "Senden...",
    "remembered_password": "Passwort wieder eingefallen?",
    "new_password_title": "Neues Passwort - WM-Tippspiel 2026",
    "new_password_heading": "Neues Passwort erstellen",
    "new_password": "Neues Passwort",
    "confirm_new_password": "Neues Passwort bestÃ¤tigen",
    "save_password": "Passwort speichern",
    "saving": "Speichern...",
    "back_to_login": "ZurÃ¼ck zur Anmeldung",
    "nav_home": "Start",
    "nav_games": "Spiele",
    "nav_predictions": "Tipps",
    "nav_ranking": "Rangliste",
    "nav_rules": "Regeln",
    "nav_competitors": "Teilnehmer",
    "nav_results": "Ergebnisse",
    "nav_groups": "Gruppen",
    "nav_simulation": "Simulation",
    "my_predictions": "Meine Tipps",
    "group_label": "Gruppe",
    "highlight_team": "Hervorgehobene Auswahl",
    "highlight_team_auto": "Automatisch nach Sprache ({team})",
    "save_highlight_team": "Anwenden",
    "logout": "Abmelden",
    "account_deletion": "Konto- und DatenlÃ¶schung beantragen",
    "footer_note": "FIFA WM-Tippspiel 2026 - Alle Zeiten in Brasilia (BRT/UTC-3)",
    "dashboard": "Dashboard",
    "invite_friend": "Freund einladen",
    "copy_invite": "Einladung kopieren",
    "copied": "Kopiert",
    "confirm_email_title": "BestÃ¤tigen Sie Ihre E-Mail.",
    "confirm_email_needed": "Die BestÃ¤tigung ist erforderlich, um automatische Rundenberichte zu erhalten (Spam prÃ¼fen).",
    "resend_confirmation": "BestÃ¤tigung erneut senden",
    "competitors": "Teilnehmer",
    "games": "Spiele",
    "completed": "Abgeschlossen",
    "pending": "Ausstehend",
    "predictions_sent": "Tipps gesendet",
    "predictions_pending": "Ausstehende Tipps",
    "current_podium": "Aktuelles Podium",
    "overall_ranking": "Gesamtrangliste",
    "stage": "Phase",
    "overall": "Gesamt",
    "points": "Punkte",
    "no_results_yet": "Noch keine Ergebnisse eingetragen.",
    "next_game": "NÃ¤chstes Spiel",
    "no_scheduled_game": "Kein Spiel geplant.",
    "next_deadline": "NÃ¤chste Frist",
    "deadline_for": "Frist fÃ¼r:",
    "no_upcoming_deadline": "Keine bevorstehende Frist.",
    "upcoming_games": "NÃ¤chste Spiele",
    "date": "Datum",
    "time_brt": "Zeit (BRT)",
    "phase": "Phase",
    "team_a": "Team A",
    "team_b": "Team B",
    "location": "Ort",
    "stadium": "Stadion",
    "city": "Stadt",
    "knockout_short": "KO",
    "knockout": "K.-o.-Runde",
    "yes": "Ja",
    "no": "Nein",
    "prediction_deadline_short": "Tippfrist",
    "action": "Aktion",
    "total_games": "Gesamt: {count} Spiel(e)",
    "game_status": "Spielstatus",
    "my_prediction": "Mein Tipp",
    "prediction_deadline": "Tippfrist",
    "scored": "Gewertet",
    "result": "Ergebnis",
    "in_progress": "LÃ¤uft",
    "locked": "Gesperrt",
    "scheduled": "Geplant",
    "open_for_predictions": "Offen fÃ¼r Tipps",
    "cancelled_changed": "Abgesagt/GeÃ¤ndert",
    "no_prediction": "Kein Tipp",
    "no_upcoming_games": "Keine nÃ¤chsten Spiele gefunden.",
    "stage_groups": "Gruppenphase",
    "stage_knockout": "K.-o.-Phase bis zum Finale",
    "phase_round_32": "Runde der letzten 32",
    "phase_round_16": "Achtelfinale",
    "phase_quarterfinals": "Viertelfinale",
    "phase_semifinal": "Halbfinale",
    "phase_third_place": "Spiel um Platz drei",
    "phase_final": "Finale",
    "world_cup_group": "Gruppe {group}",
    "other_group": "Andere",
    "predictions_title": "Tipps",
    "goals_a": "Tore A",
    "goals_b": "Tore B",
    "qualified_knockout": "Qualifiziert (KO)",
    "comparison": "Vergleich",
    "deadline": "Frist",
    "status": "Status",
    "exact_score": "Exaktes Ergebnis",
    "winner_plus_margin": "Sieger + Differenz",
    "winner_correct": "Richtiger Sieger",
    "winner": "Sieger",
    "loser": "Verlierer",
    "goals_correct": "Richtige Tore",
    "missed": "Verfehlt",
    "qualified_correct": "Richtig qualifiziert",
    "waiting": "Warten",
    "sent": "Gesendet",
    "open": "Offen",
    "exact": "Exakt",
    "fill_empty_tab": "Leere Tipps in diesem Tab ausfÃ¼llen",
    "clear_future_tab": "ZukÃ¼nftige Tipps in diesem Tab lÃ¶schen",
    "no_games_found": "Keine Spiele gefunden.",
    "save_predictions": "Tipps speichern",
    "editable_note": "Nur zukÃ¼nftige Spiele innerhalb der Frist bleiben bearbeitbar.",
    "unsaved_changes": "Nicht gespeicherte Ã„nderungen",
    "unsaved_body": "Sie haben Ihre Tipps geÃ¤ndert. Vor dem Verlassen speichern?",
    "save": "Speichern",
    "leave_without_saving": "Ohne Speichern verlassen",
    "stay_on_page": "Auf der Seite bleiben",
    "clear_confirm": "Nur bearbeitbare Tipps in diesem Tab lÃ¶schen? Diese Aktion wird jetzt gespeichert.",
    "rules_title": "Tippspiel-Regeln",
    "rules_heading": "Regeln und nÃ¼tzliche Informationen",
    "rules_subtitle": "Kurze Zusammenfassung von Wertung, Fristen, Tie-Breakern und Ablauf.",
    "scoring_rules": "Wertungsregeln",
    "situation": "Situation",
    "exact_score_rule": "Exaktes Ergebnis",
    "winner_margin_rule": "Richtiger Sieger + richtige Differenz",
    "winner_rule": "Richtiger Sieger",
    "draw_rule": "Richtiges Unentschieden mit anderem Ergebnis",
    "one_team_goals_rule": "Richtige Tore eines Teams",
    "no_relevant_hits": "Keine relevanten Treffer",
    "knockout_bonus_rule": "Bonus fÃ¼r richtig qualifiziertes Team in KO-Spielen",
    "tie_breakers": "Tie-Breaker",
    "tie_1": "HÃ¶chste Gesamtpunktzahl.",
    "tie_2": "Meiste exakte Ergebnisse.",
    "tie_3": "Meiste richtige Sieger.",
    "tie_4": "Meiste richtige Tordifferenzen.",
    "tie_5": "Meiste richtige Qualifizierte.",
    "tie_6": "Meiste abgegebene Tipps.",
    "tie_7": "Wenigste nicht abgegebene Tipps.",
    "tie_8": "Alphabetische Reihenfolge des Spitznamens.",
    "deadlines_times": "Fristen und Zeiten",
    "deadline_1": "Alle angezeigten Zeiten sind Brasilia-Zeit.",
    "deadline_2": "Die Tippfrist endet um 23:59 Uhr am Tag vor dem Spiel.",
    "deadline_3": "Nach Ablauf der Frist ist der Tipp gesperrt.",
    "deadline_4": "Spiele ohne rechtzeitigen Tipp zÃ¤hlen als nicht abgegeben.",
    "deadline_5": "Ergebnisse erscheinen zur direkten Kontrolle auf der Tippseite.",
    "ranking_stages": "Rangliste nach Phasen",
    "ranking_stage_overall": "summiert alle WM-Spiele.",
    "ranking_stage_groups": "berÃ¼cksichtigt nur Spiele der Gruppenphase.",
    "ranking_stage_knockout": "beginnt in der K.-o.-Phase bei null und lÃ¤uft bis zum Finale.",
    "ranking_stage_ties": "Die Tie-Breaker sind in allen Phasen gleich.",
    "how_to_read_predictions": "So liest man die Tippseite",
    "read_1": "Status Offen: Bearbeitung ist noch mÃ¶glich.",
    "read_2": "Status Gesendet: Tipp vor der Frist gespeichert.",
    "read_3": "Status Ergebnis: offizielles Ergebnis bereits eingetragen.",
    "read_4": "Status Gewertet: Punkte fÃ¼r das Spiel berechnet.",
    "read_5": "Spalte Ergebnis: zeigt das offizielle Ergebnis.",
    "read_6": "Spalte Vergleich: zeigt Treffer bei Ergebnis, Sieger, Differenz oder Qualifiziertem.",
    "auto_results": "Ergebnisaktualisierung (automatisch)",
    "auto_1": "Ergebnisse kÃ¶nnen automatisch aus einer zuverlÃ¤ssigen externen API synchronisiert werden.",
    "auto_2": "Die Synchronisierung berÃ¼cksichtigt nur abgeschlossene Spiele der offiziellen Quelle.",
    "auto_3": "Ist das empfangene Ergebnis identisch, wird nichts geÃ¤ndert.",
    "auto_4": "Bei Ã„nderung von Ergebnis/Qualifiziertem berechnet das System die Punkte automatisch neu.",
    "auto_5": "Wenn ein Spiel nicht sicher zugeordnet werden kann, wird es nicht automatisch geÃ¤ndert.",
    "auto_6": "Administratoren kÃ¶nnen die Synchronisierung Ã¼ber den Sync-API-Button ausfÃ¼hren.",
    "auto_7": "Die manuelle Pflege von Ergebnissen bleibt fÃ¼r punktuelle Anpassungen verfÃ¼gbar.",
    "useful_info": "NÃ¼tzliche Informationen",
    "groups_info": "Benutzer sehen Tipps von Teilnehmern derselben Gruppe, kÃ¶nnen aber nur eigene Tipps bearbeiten.",
    "ranking_info": "Die Gesamtrangliste summiert alle gewerteten Spiele. Die Phasenrangliste berÃ¼cksichtigt nur die gewÃ¤hlte Phase.",
    "simulation_info": "Administratoren kÃ¶nnen Simulationen nutzen, um Daten vorzuziehen und das System zu prÃ¼fen.",
    "data_deletion": "DatenlÃ¶schung",
    "data_deletion_info": "Benutzer kÃ¶nnen die LÃ¶schung von Konto und Daten Ã¼ber den Link beantragen",
    "round_report_subject": "Bericht fÃ¼r {round_label} - WM-Tippspiel 2026",
    "hello_name": "Hallo, {name}!",
    "round_report_heading": "Bericht fÃ¼r {round_label}:",
    "your_round_points": "Ihre Punkte in dieser Runde: {points}",
    "exact_scores_round": "Exakte Ergebnisse in dieser Runde: {count}",
    "your_stage_position": "Ihre Position in dieser Phase ({stage_label}): {position}",
    "your_overall_position": "Ihre Position in der Gesamtrangliste: {position}",
    "round_games": "Spiele der Runde:",
    "top5_stage": "Top 5 der Phase - {stage_label}:",
    "top5_overall": "Gesamt Top 5:",
    "access_app_details": "Ã–ffnen Sie die App, um alle Details zu sehen.",
    "invite_friend_line": "Laden Sie einen Freund ein:",
    "confirm_email_subject": "BestÃ¤tigen Sie Ihre E-Mail - WM-Tippspiel 2026",
    "confirm_email_text": "Hallo, {name}!\n\nBestÃ¤tigen Sie Ihre E-Mail, um Rundenberichte vom WM-Tippspiel 2026 zu erhalten:\n{url}\n\nWenn Sie dieses Konto nicht erstellt haben, ignorieren Sie diese Nachricht.",
    "confirm_email_html": "<p>Hallo, {name}!</p><p>BestÃ¤tigen Sie Ihre E-Mail, um Rundenberichte vom WM-Tippspiel 2026 zu erhalten.</p><p><a href=\"{url}\">E-Mail bestÃ¤tigen</a></p><p>Wenn Sie dieses Konto nicht erstellt haben, ignorieren Sie diese Nachricht.</p>",
    "reset_password_subject": "Passwort zurÃ¼cksetzen - WM-Tippspiel 2026",
    "reset_password_text": "Hallo, {name}!\n\nWir haben eine Anfrage zum ZurÃ¼cksetzen Ihres Passworts erhalten.\nNutzen Sie diesen Link innerhalb von 1 Stunde, um ein neues Passwort zu erstellen:\n{url}\n\nWenn Sie diese Ã„nderung nicht angefordert haben, ignorieren Sie diese Nachricht.",
    "reset_password_html": "<p>Hallo, {name}!</p><p>Wir haben eine Anfrage zum ZurÃ¼cksetzen Ihres Passworts erhalten.</p><p><a href=\"{url}\">Neues Passwort erstellen</a></p><p>Dieser Link lÃ¤uft in 1 Stunde ab. Wenn Sie diese Ã„nderung nicht angefordert haben, ignorieren Sie diese Nachricht.</p>",
}}

TRANSLATIONS["it"] = {**TRANSLATIONS["en"], **{
    "language_label": "Lingua",
    "app_name": "Pronostici Mondiali 2026",
    "system_subtitle": "Sistema di pronostici",
    "sign_in": "Accedi",
    "forgot_password": "Password dimenticata?",
    "register": "Registrati",
    "nav_home": "Home",
    "nav_games": "Partite",
    "nav_predictions": "Pronostici",
    "nav_ranking": "Classifica",
    "nav_rules": "Regole",
    "nav_results": "Risultati",
    "nav_groups": "Gruppi",
    "my_predictions": "I miei pronostici",
    "logout": "Esci",
    "dashboard": "Dashboard",
    "highlight_team": "Selezione in evidenza",
    "highlight_team_auto": "Automatico per lingua ({team})",
    "save_highlight_team": "Applica",
    "games": "Partite",
    "completed": "Completate",
    "pending": "In sospeso",
    "stage": "Fase",
    "overall": "Generale",
    "points": "punti",
    "date": "Data",
    "time_brt": "Ora (BRT)",
    "phase": "Fase",
    "team_a": "Squadra A",
    "team_b": "Squadra B",
    "stadium": "Stadio",
    "city": "Città",
    "yes": "Sì",
    "no": "No",
    "status": "Stato",
    "scheduled": "Programmata",
    "open_for_predictions": "Aperta ai pronostici",
    "scored": "Punteggiata",
    "result": "Risultato",
    "predictions_title": "Pronostici",
    "save_predictions": "Salva pronostici",
    "stage_groups": "Fase a gironi",
    "stage_knockout": "Fase a eliminazione fino alla finale",
    "world_cup_group": "Gruppo {group}",
    "rules_title": "Regole",
    "rules_heading": "Regole e informazioni utili",
    "rules_subtitle": "Riepilogo rapido di punteggi, scadenze e criteri di spareggio.",
    "winner": "Vincitore",
    "loser": "Perdente",
    "confirm_email_subject": "Conferma la tua e-mail - Pronostici Mondiali 2026",
    "reset_password_subject": "Reimposta la password - Pronostici Mondiali 2026",
}}

TRANSLATIONS["ar"] = {**TRANSLATIONS["en"], **{
    "language_label": "اللغة",
    "app_name": "توقعات كأس العالم 2026",
    "system_subtitle": "نظام التوقعات",
    "sign_in": "تسجيل الدخول",
    "forgot_password": "نسيت كلمة المرور؟",
    "register": "تسجيل",
    "nav_home": "الرئيسية",
    "nav_games": "المباريات",
    "nav_predictions": "التوقعات",
    "nav_ranking": "الترتيب",
    "nav_rules": "القواعد",
    "nav_results": "النتائج",
    "nav_groups": "المجموعات",
    "my_predictions": "توقعاتي",
    "logout": "خروج",
    "dashboard": "لوحة التحكم",
    "highlight_team": "المنتخب المميز",
    "highlight_team_auto": "تلقائي حسب اللغة ({team})",
    "save_highlight_team": "تطبيق",
    "games": "المباريات",
    "completed": "مكتملة",
    "pending": "معلقة",
    "stage": "المرحلة",
    "overall": "عام",
    "points": "نقاط",
    "date": "التاريخ",
    "time_brt": "الوقت (BRT)",
    "phase": "المرحلة",
    "team_a": "الفريق أ",
    "team_b": "الفريق ب",
    "stadium": "الملعب",
    "city": "المدينة",
    "yes": "نعم",
    "no": "لا",
    "status": "الحالة",
    "scheduled": "مجدولة",
    "open_for_predictions": "مفتوحة للتوقعات",
    "scored": "تم احتسابها",
    "result": "النتيجة",
    "predictions_title": "التوقعات",
    "save_predictions": "حفظ التوقعات",
    "stage_groups": "دور المجموعات",
    "stage_knockout": "الأدوار الإقصائية حتى النهائي",
    "world_cup_group": "المجموعة {group}",
    "rules_title": "القواعد",
    "rules_heading": "القواعد والمعلومات المفيدة",
    "rules_subtitle": "ملخص سريع للنقاط والمواعيد ومعايير كسر التعادل.",
    "winner": "الفائز",
    "loser": "الخاسر",
    "confirm_email_subject": "أكد بريدك الإلكتروني - توقعات كأس العالم 2026",
    "reset_password_subject": "إعادة تعيين كلمة المرور - توقعات كأس العالم 2026",
}}

TRANSLATIONS["zh"] = {**TRANSLATIONS["en"], **{
    "language_label": "语言",
    "app_name": "2026世界杯竞猜",
    "system_subtitle": "竞猜系统",
    "sign_in": "登录",
    "forgot_password": "忘记密码？",
    "register": "注册",
    "nav_home": "首页",
    "nav_games": "比赛",
    "nav_predictions": "预测",
    "nav_ranking": "排名",
    "nav_rules": "规则",
    "nav_results": "结果",
    "nav_groups": "小组",
    "my_predictions": "我的预测",
    "logout": "退出",
    "dashboard": "控制面板",
    "highlight_team": "高亮球队",
    "highlight_team_auto": "按语言自动选择（{team}）",
    "save_highlight_team": "应用",
    "games": "比赛",
    "completed": "已完成",
    "pending": "待处理",
    "stage": "阶段",
    "overall": "总计",
    "points": "分",
    "date": "日期",
    "time_brt": "时间 (BRT)",
    "phase": "阶段",
    "team_a": "球队 A",
    "team_b": "球队 B",
    "stadium": "体育场",
    "city": "城市",
    "yes": "是",
    "no": "否",
    "status": "状态",
    "scheduled": "已安排",
    "open_for_predictions": "可预测",
    "scored": "已计分",
    "result": "结果",
    "predictions_title": "预测",
    "save_predictions": "保存预测",
    "stage_groups": "小组赛",
    "stage_knockout": "淘汰赛至决赛",
    "world_cup_group": "{group}组",
    "rules_title": "规则",
    "rules_heading": "规则和实用信息",
    "rules_subtitle": "积分、截止时间和排名规则的快速摘要。",
    "winner": "胜者",
    "loser": "负者",
    "confirm_email_subject": "确认您的邮箱 - 2026世界杯竞猜",
    "reset_password_subject": "重置密码 - 2026世界杯竞猜",
}}

TRANSLATIONS["ru"] = {**TRANSLATIONS["en"], **{
    "language_label": "Язык",
    "app_name": "Прогнозы ЧМ-2026",
    "system_subtitle": "Система прогнозов",
    "sign_in": "Войти",
    "forgot_password": "Забыли пароль?",
    "register": "Регистрация",
    "nav_home": "Главная",
    "nav_games": "Матчи",
    "nav_predictions": "Прогнозы",
    "nav_ranking": "Рейтинг",
    "nav_rules": "Правила",
    "nav_results": "Результаты",
    "nav_groups": "Группы",
    "my_predictions": "Мои прогнозы",
    "logout": "Выйти",
    "dashboard": "Панель",
    "highlight_team": "Выделенная сборная",
    "highlight_team_auto": "Автоматически по языку ({team})",
    "save_highlight_team": "Применить",
    "games": "Матчи",
    "completed": "Завершено",
    "pending": "Ожидает",
    "stage": "Этап",
    "overall": "Общий",
    "points": "очки",
    "date": "Дата",
    "time_brt": "Время (BRT)",
    "phase": "Этап",
    "team_a": "Команда A",
    "team_b": "Команда B",
    "stadium": "Стадион",
    "city": "Город",
    "yes": "Да",
    "no": "Нет",
    "status": "Статус",
    "scheduled": "Запланировано",
    "open_for_predictions": "Открыто для прогнозов",
    "scored": "Начислено",
    "result": "Результат",
    "predictions_title": "Прогнозы",
    "save_predictions": "Сохранить прогнозы",
    "stage_groups": "Групповой этап",
    "stage_knockout": "Плей-офф до финала",
    "world_cup_group": "Группа {group}",
    "rules_title": "Правила",
    "rules_heading": "Правила и полезная информация",
    "rules_subtitle": "Краткое описание очков, сроков и правил тай-брейка.",
    "winner": "Победитель",
    "loser": "Проигравший",
    "confirm_email_subject": "Подтвердите e-mail - Прогнозы ЧМ-2026",
    "reset_password_subject": "Сброс пароля - Прогнозы ЧМ-2026",
}}


def _repair_mojibake(value):
    if not isinstance(value, str):
        return value
    try:
        return value.encode("latin1").decode("utf-8")
    except UnicodeError:
        return value


for _lang in ("fr", "de", "it", "ar", "zh", "ru"):
    TRANSLATIONS[_lang] = {key: _repair_mojibake(value) for key, value in TRANSLATIONS[_lang].items()}


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


def normalizar_idioma(idioma):
    idioma = (idioma or "").strip().replace("_", "-")
    if not idioma:
        return None
    idioma_lower = idioma.lower()
    if idioma_lower in {"pt", "pt-br", "pt-pt"}:
        return "pt-BR"
    if idioma_lower.startswith("en"):
        return "en"
    if idioma_lower.startswith("es"):
        return "es"
    if idioma_lower.startswith("fr"):
        return "fr"
    if idioma_lower.startswith("de"):
        return "de"
    if idioma_lower.startswith("it"):
        return "it"
    if idioma_lower.startswith("ar"):
        return "ar"
    if idioma_lower.startswith("zh") or idioma_lower.startswith("cn"):
        return "zh"
    if idioma_lower.startswith("ru"):
        return "ru"
    return idioma if idioma in SUPPORTED_LANGUAGES else None


def detectar_idioma_navegador():
    matches = ["pt-BR", "pt", "en", "es", "fr", "de", "it", "ar", "zh", "ru"]
    match = request.accept_languages.best_match(matches)
    return normalizar_idioma(match) or DEFAULT_LANGUAGE


def idioma_atual():
    session_lang = normalizar_idioma(session.get("idioma"))
    if session_lang:
        return session_lang
    if getattr(g, "user", None) and normalizar_idioma(g.user.idioma):
        return normalizar_idioma(g.user.idioma)
    return detectar_idioma_navegador()


def tr(key, idioma=None, **kwargs):
    idioma = normalizar_idioma(idioma) or getattr(g, "idioma", None) or DEFAULT_LANGUAGE
    text = TRANSLATIONS.get(idioma, {}).get(key) or TRANSLATIONS[DEFAULT_LANGUAGE].get(key) or key
    return text.format(**kwargs) if kwargs else text


def etapa_label_traduzida(etapa_key, idioma=None):
    if etapa_key == "grupos":
        return tr("stage_groups", idioma)
    if etapa_key == "mata_mata":
        return tr("stage_knockout", idioma)
    return tr("overall", idioma)


def fase_label_traduzida(fase, idioma=None):
    fase_original = (fase or "").strip()
    normalizada = fase_original.lower()
    mapa = {
        "fase de grupos": "stage_groups",
        "rodada de 32": "phase_round_32",
        "oitavas de final": "phase_round_16",
        "quartas de final": "phase_quarterfinals",
        "semifinal": "phase_semifinal",
        "terceiro lugar": "phase_third_place",
        "final": "phase_final",
    }
    key = mapa.get(normalizada)
    return tr(key, idioma) if key else fase_original


def grupo_label_traduzido(grupo, idioma=None):
    grupo = (grupo or "").strip()
    if not grupo or grupo == "Outros":
        return tr("other_group", idioma)
    return tr("world_cup_group", idioma, group=grupo)


def status_jogo_traduzido(status, idioma=None):
    status_original = (status or "").strip()
    normalizado = status_original.lower()
    mapa = {
        "pontuado": "scored",
        "resultado lançado": "result",
        "em andamento": "in_progress",
        "bloqueado para palpites": "locked",
        "aberto para palpites": "open_for_predictions",
        "aberto para palpite": "open",
        "agendado": "scheduled",
        "cancelado/alterado": "cancelled_changed",
    }
    key = mapa.get(normalizado)
    return tr(key, idioma) if key else status_original


def time_nome_traduzido(nome, idioma=None):
    nome_original = (nome or "").strip()
    idioma = normalizar_idioma(idioma) or getattr(g, "idioma", None) or DEFAULT_LANGUAGE
    if not nome_original or idioma == DEFAULT_LANGUAGE:
        return nome_original

    if nome_original.startswith("Vencedor "):
        return tr("winner", idioma) + nome_original[len("Vencedor"):]
    if nome_original.startswith("Perdedor "):
        return tr("loser", idioma) + nome_original[len("Perdedor"):]

    return TEAM_TRANSLATIONS.get(idioma, {}).get(nome_original, nome_original)


def codigo_time_destaque_padrao(idioma=None):
    idioma = normalizar_idioma(idioma) or getattr(g, "idioma", None) or DEFAULT_LANGUAGE
    return DEFAULT_HIGHLIGHT_TEAM_BY_LANGUAGE.get(idioma, "BRA")


def codigo_time_destacado(user=None):
    user = user if user is not None else getattr(g, "user", None)
    codigo = (getattr(user, "time_destaque", "") or "").strip().upper() if user else ""
    return codigo or codigo_time_destaque_padrao()


def is_time_destacado(sigla, user=None):
    return (sigla or "").strip().upper() == codigo_time_destacado(user)


def opcoes_time_destaque():
    try:
        jogos = Jogo.query.with_entities(
            Jogo.time_a, Jogo.sigla_time_a, Jogo.time_b, Jogo.sigla_time_b
        ).all()
    except Exception:
        return []

    codigo_real_re = re.compile(r"^[A-Z]{3}$")
    opcoes = {}
    for time_a, sigla_a, time_b, sigla_b in jogos:
        sigla_a = (sigla_a or "").strip().upper()
        sigla_b = (sigla_b or "").strip().upper()
        if sigla_a and codigo_real_re.match(sigla_a):
            opcoes[sigla_a.strip().upper()] = time_a
        if sigla_b and codigo_real_re.match(sigla_b):
            opcoes[sigla_b.strip().upper()] = time_b

    return [
        {"code": code, "name": time_nome_traduzido(nome), "raw_name": nome}
        for code, nome in sorted(opcoes.items(), key=lambda item: time_nome_traduzido(item[1]).lower())
    ]


def nome_time_por_sigla(sigla):
    sigla = (sigla or "").strip().upper()
    for opcao in opcoes_time_destaque():
        if opcao["code"] == sigla:
            return opcao["name"]
    return sigla


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
    message.set_content(text_body, charset="utf-8")
    if html_body:
        message.add_alternative(html_body, subtype="html", charset="utf-8")

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
    subject = tr("confirm_email_subject", user.idioma)
    text = tr("confirm_email_text", user.idioma, name=user.nome, url=confirm_url)
    html = tr("confirm_email_html", user.idioma, name=escape(user.nome), url=confirm_url)
    return send_email_message(user.email, subject, text, html)


def send_password_reset_email(user):
    token = make_password_reset_token(user)
    reset_url = url_for("redefinir_senha", token=token, _external=True)
    subject = tr("reset_password_subject", user.idioma)
    text = tr("reset_password_text", user.idioma, name=user.nome, url=reset_url)
    html = tr("reset_password_html", user.idioma, name=escape(user.nome), url=reset_url)
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
    if "idioma" not in existing:
        statements.append(f"ALTER TABLE users ADD COLUMN idioma VARCHAR(10) DEFAULT '{DEFAULT_LANGUAGE}'")
    if "time_destaque" not in existing:
        statements.append("ALTER TABLE users ADD COLUMN time_destaque VARCHAR(5)")

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


def convite_url(user=None):
    params = {"_external": True}
    if user and user.grupo_id:
        grupo = Grupo.query.get(user.grupo_id)
        if grupo and grupo.publico:
            params["grupo_id"] = user.grupo_id
    try:
        return url_for("registro", **params)
    except RuntimeError:
        base_url = os.environ.get("APP_PUBLIC_URL", "https://bolao2026-9jgh.onrender.com").rstrip("/")
        if "grupo_id" in params:
            return f"{base_url}/registro?grupo_id={params['grupo_id']}"
        return f"{base_url}/registro"


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
            "label": grupo_label_traduzido(grupo),
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


def etapa_ranking_para_rodada(rodada):
    if any(jogo.mata_mata for jogo in rodada["jogos"]):
        return "mata_mata"
    return "grupos"


def montar_relatorio_rodada(user, competidor, rodada):
    jogo_ids = [j.id for j in rodada["jogos"]]
    pontuacoes = Pontuacao.query.filter(
        Pontuacao.competidor_id == competidor.id,
        Pontuacao.jogo_id.in_(jogo_ids),
    ).all()
    pontos_rodada = sum(p.pontos for p in pontuacoes)
    placares = sum(1 for p in pontuacoes if p.placar_exato)
    etapa_key = etapa_ranking_para_rodada(rodada)
    etapa_label = etapa_label_traduzida(etapa_key, user.idioma)
    ranking_etapa = get_ranking(db, Competidor, Pontuacao, Palpite, Jogo, etapa=etapa_key)
    ranking_geral = get_ranking(db, Competidor, Pontuacao, Palpite, Jogo)
    posicao_etapa = next((item["posicao"] for item in ranking_etapa if item["competidor"].id == competidor.id), None)
    posicao_geral = next((item["posicao"] for item in ranking_geral if item["competidor"].id == competidor.id), None)
    top5_etapa = ranking_etapa[:5]
    top5_geral = ranking_geral[:5]
    jogos_linhas = []

    for jogo in rodada["jogos"]:
        resultado = jogo.resultado
        pont = next((p for p in pontuacoes if p.jogo_id == jogo.id), None)
        jogos_linhas.append(
            f"- {time_nome_traduzido(jogo.time_a, user.idioma)} "
            f"{resultado.gols_a} x {resultado.gols_b} "
            f"{time_nome_traduzido(jogo.time_b, user.idioma)}: "
            f"{pont.pontos if pont else 0} ponto(s)"
        )

    top_etapa_linhas = [
        f"{item['posicao']}. {item['competidor'].apelido} - {item['pontos']} pts"
        for item in top5_etapa
    ]
    top_geral_linhas = [
        f"{item['posicao']}. {item['competidor'].apelido} - {item['pontos']} pts"
        for item in top5_geral
    ]
    invite_url = convite_url(user)
    subject = tr("round_report_subject", user.idioma, round_label=rodada["label"])
    text = (
        tr("hello_name", user.idioma, name=user.nome)
        + "\n\n"
        + tr("round_report_heading", user.idioma, round_label=rodada["label"])
        + "\n"
        + tr("your_round_points", user.idioma, points=pontos_rodada)
        + "\n"
        + tr("exact_scores_round", user.idioma, count=placares)
        + "\n"
        + tr("your_stage_position", user.idioma, stage_label=etapa_label, position=posicao_etapa or "-")
        + "\n"
        + tr("your_overall_position", user.idioma, position=posicao_geral or "-")
        + "\n\n"
        + tr("round_games", user.idioma)
        + "\n"
        + "\n".join(jogos_linhas)
        + "\n\n"
        + tr("top5_stage", user.idioma, stage_label=etapa_label)
        + "\n"
        + "\n".join(top_etapa_linhas)
        + "\n\n"
        + tr("top5_overall", user.idioma)
        + "\n"
        + "\n".join(top_geral_linhas)
        + "\n\n"
        + tr("access_app_details", user.idioma)
        + "\n\n"
        + tr("invite_friend_line", user.idioma)
        + f"\n{invite_url}"
    )
    html = (
        f"<p>{escape(tr('hello_name', user.idioma, name=user.nome))}</p>"
        f"<h2>{escape(rodada['label'])}</h2>"
        f"<p>{escape(tr('your_round_points', user.idioma, points=pontos_rodada))}</p>"
        f"<p>{escape(tr('exact_scores_round', user.idioma, count=placares))}</p>"
        f"<p>{escape(tr('your_stage_position', user.idioma, stage_label=etapa_label, position=posicao_etapa or '-'))}</p>"
        f"<p>{escape(tr('your_overall_position', user.idioma, position=posicao_geral or '-'))}</p>"
        f"<h3>{escape(tr('round_games', user.idioma))}</h3><ul>"
        + "".join(f"<li>{escape(linha[2:])}</li>" for linha in jogos_linhas)
        + f"</ul><h3>{escape(tr('top5_stage', user.idioma, stage_label=etapa_label))}</h3><ol>"
        + "".join(f"<li>{escape(item['competidor'].apelido)} - {item['pontos']} pts</li>" for item in top5_etapa)
        + f"</ol><h3>{escape(tr('top5_overall', user.idioma))}</h3><ol>"
        + "".join(f"<li>{escape(item['competidor'].apelido)} - {item['pontos']} pts</li>" for item in top5_geral)
        + f"</ol><p>{escape(tr('access_app_details', user.idioma))}</p>"
        + f"<p>{escape(tr('invite_friend_line', user.idioma))}<br><a href=\"{invite_url}\">{invite_url}</a></p>"
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


@app.before_request
def load_current_language():
    idioma = idioma_atual()
    session["idioma"] = idioma
    g.idioma = idioma


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
        "idioma": user.idioma or DEFAULT_LANGUAGE,
        "time_destaque": codigo_time_destacado(user),
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
        idioma=idioma_atual(),
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
    idioma = session.get("idioma")
    session.clear()
    if idioma:
        session["idioma"] = idioma
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
        "podium_etapa_label": etapa_label_traduzida(etapa_podium),
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
        "etapa_label": fase or etapa_label_traduzida(etapa),
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
        current_language=getattr(g, "idioma", DEFAULT_LANGUAGE),
        supported_languages=SUPPORTED_LANGUAGES,
        language_badges=LANGUAGE_BADGES,
        tr=tr,
        fase_label_traduzida=fase_label_traduzida,
        grupo_label_traduzido=grupo_label_traduzido,
        status_jogo_traduzido=status_jogo_traduzido,
        time_nome_traduzido=time_nome_traduzido,
        is_time_destacado=is_time_destacado,
        codigo_time_destacado=codigo_time_destacado,
        codigo_time_destaque_padrao=codigo_time_destaque_padrao,
        opcoes_time_destaque=opcoes_time_destaque,
        nome_time_por_sigla=nome_time_por_sigla,
    )


@app.route("/idioma/<idioma>", methods=["POST"])
def alterar_idioma(idioma):
    idioma_normalizado = normalizar_idioma(idioma)
    if not idioma_normalizado:
        flash("Idioma indisponível.", "warning")
        idioma_normalizado = DEFAULT_LANGUAGE

    session["idioma"] = idioma_normalizado
    if g.user:
        g.user.idioma = idioma_normalizado
        db.session.commit()

    next_url = request.form.get("next") or request.referrer or url_for("dashboard" if g.user else "login")
    if not ((next_url.startswith("/") and not next_url.startswith("//")) or next_url.startswith(request.host_url)):
        next_url = url_for("dashboard" if g.user else "login")
    return redirect(next_url)


@app.route("/time-destaque", methods=["POST"])
@login_required
def alterar_time_destaque():
    codigo = (request.form.get("time_destaque") or "").strip().upper()
    codigos_validos = {opcao["code"] for opcao in opcoes_time_destaque()}
    if codigo == "AUTO":
        g.user.time_destaque = None
    elif codigo in codigos_validos:
        g.user.time_destaque = codigo
    else:
        flash("Seleção indisponível para destaque.", "warning")
        codigo = None

    if codigo:
        db.session.commit()

    next_url = request.form.get("next") or request.referrer or url_for("dashboard")
    if not ((next_url.startswith("/") and not next_url.startswith("//")) or next_url.startswith(request.host_url)):
        next_url = url_for("dashboard")
    return redirect(next_url)


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
            if not normalizar_idioma(user.idioma):
                user.idioma = idioma_atual()
                db.session.commit()
            session["idioma"] = user.idioma or DEFAULT_LANGUAGE
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
            idioma=idioma_atual(),
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
                flash("Enviamos um link de confirmação para seu e-mail (verifique spam).", "info")
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
            flash("Enviamos um novo link de confirmação para seu e-mail (verifique spam).", "success")
        else:
            flash("SMTP ainda não configurado. Não foi possível enviar a confirmação.", "warning")
    except Exception:
        app.logger.exception("Falha ao reenviar confirmação para %s", g.user.email)
        flash("Não foi possível enviar a confirmação agora.", "danger")
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    idioma = session.get("idioma")
    session.clear()
    if idioma:
        session["idioma"] = idioma
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

    invite_url = convite_url(g.user)
    invite_text = f"Convide um amigo para participar: {invite_url}"

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
                           podium_etapa_label=etapa_label_traduzida(etapa_podium),
                           podium_etapa_key=etapa_podium,
                           proximo_jogo=proximo_jogo,
                           proximo_prazo=proximo_prazo,
                           proximos_com_status=proximos_com_status,
                           invite_url=invite_url,
                           invite_text=invite_text)


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
                           etapa_label=etapa_label_traduzida(etapa),
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
