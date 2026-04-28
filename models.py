from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Grupo(db.Model):
    __tablename__ = "grupos"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    criado_por_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    criado_por = db.relationship("User", backref="grupos_criados", foreign_keys=[criado_por_id])
    usuarios = db.relationship("User", backref="grupo", foreign_keys="User.grupo_id")


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    apelido = db.Column(db.String(50))
    senha_hash = db.Column(db.String(255), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey("grupos.id"))
    eh_admin = db.Column(db.Boolean, default=False)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.senha_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.senha_hash, password)


class Competidor(db.Model):
    __tablename__ = "competidores"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    apelido = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100))
    telefone = db.Column(db.String(30))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    data_entrada = db.Column(db.Date, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("competidor_profile", uselist=False))
    palpites = db.relationship("Palpite", backref="competidor", lazy=True)
    pontuacoes = db.relationship("Pontuacao", backref="competidor", lazy=True)


class Jogo(db.Model):
    __tablename__ = "jogos"
    id = db.Column(db.Integer, primary_key=True)
    numero_partida = db.Column(db.Integer)
    fase = db.Column(db.String(50), nullable=False)
    grupo = db.Column(db.String(10))
    rodada = db.Column(db.Integer)
    data_jogo = db.Column(db.Date, nullable=False)
    hora_et = db.Column(db.String(10))
    timezone_original = db.Column(db.String(50), default="America/New_York")
    hora_brasilia = db.Column(db.String(10))
    timezone_exibicao = db.Column(db.String(50), default="America/Sao_Paulo")
    time_a = db.Column(db.String(60))
    time_b = db.Column(db.String(60))
    sigla_time_a = db.Column(db.String(5))
    sigla_time_b = db.Column(db.String(5))
    estadio = db.Column(db.String(100))
    cidade = db.Column(db.String(60))
    pais = db.Column(db.String(60))
    mata_mata = db.Column(db.Boolean, default=False)
    prazo_palpite = db.Column(db.DateTime)
    status = db.Column(db.String(30), default="Agendado")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    palpites = db.relationship("Palpite", backref="jogo", lazy=True)
    resultado = db.relationship("Resultado", backref="jogo", uselist=False, lazy=True)
    pontuacoes = db.relationship("Pontuacao", backref="jogo", lazy=True)


class Palpite(db.Model):
    __tablename__ = "palpites"
    id = db.Column(db.Integer, primary_key=True)
    competidor_id = db.Column(db.Integer, db.ForeignKey("competidores.id"), nullable=False)
    jogo_id = db.Column(db.Integer, db.ForeignKey("jogos.id"), nullable=False)
    palpite_gols_a = db.Column(db.Integer)
    palpite_gols_b = db.Column(db.Integer)
    palpite_classificado = db.Column(db.String(60))
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    data_ultima_alteracao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    bloqueado = db.Column(db.Boolean, default=False)
    valido = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("competidor_id", "jogo_id", name="uq_competidor_jogo"),
    )

    historico = db.relationship("HistoricoPalpite", backref="palpite", lazy=True)


class Resultado(db.Model):
    __tablename__ = "resultados"
    id = db.Column(db.Integer, primary_key=True)
    jogo_id = db.Column(db.Integer, db.ForeignKey("jogos.id"), nullable=False, unique=True)
    gols_a = db.Column(db.Integer, nullable=False)
    gols_b = db.Column(db.Integer, nullable=False)
    classificado = db.Column(db.String(60))
    resultado_lancado = db.Column(db.Boolean, default=True)
    data_lancamento = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_lancamento = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Pontuacao(db.Model):
    __tablename__ = "pontuacoes"
    id = db.Column(db.Integer, primary_key=True)
    competidor_id = db.Column(db.Integer, db.ForeignKey("competidores.id"), nullable=False)
    jogo_id = db.Column(db.Integer, db.ForeignKey("jogos.id"), nullable=False)
    pontos = db.Column(db.Integer, default=0)
    placar_exato = db.Column(db.Boolean, default=False)
    vencedor_correto = db.Column(db.Boolean, default=False)
    saldo_correto = db.Column(db.Boolean, default=False)
    gols_time_a_correto = db.Column(db.Boolean, default=False)
    gols_time_b_correto = db.Column(db.Boolean, default=False)
    classificado_correto = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("competidor_id", "jogo_id", name="uq_pont_competidor_jogo"),
    )


class HistoricoPalpite(db.Model):
    __tablename__ = "historico_palpites"
    id = db.Column(db.Integer, primary_key=True)
    palpite_id = db.Column(db.Integer, db.ForeignKey("palpites.id"), nullable=False)
    competidor_id = db.Column(db.Integer, db.ForeignKey("competidores.id"), nullable=False)
    jogo_id = db.Column(db.Integer, db.ForeignKey("jogos.id"), nullable=False)
    palpite_gols_a_anterior = db.Column(db.Integer)
    palpite_gols_b_anterior = db.Column(db.Integer)
    palpite_classificado_anterior = db.Column(db.String(60))
    palpite_gols_a_novo = db.Column(db.Integer)
    palpite_gols_b_novo = db.Column(db.Integer)
    palpite_classificado_novo = db.Column(db.String(60))
    data_alteracao = db.Column(db.DateTime, default=datetime.utcnow)


class SolicitacaoExclusaoDados(db.Model):
    __tablename__ = "solicitacoes_exclusao_dados"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    motivo = db.Column(db.Text)
    status = db.Column(db.String(30), default="Pendente")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
