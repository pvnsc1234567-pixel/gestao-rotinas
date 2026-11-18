from datetime import datetime, timezone

from .extensions import db


def agora():
    return datetime.now(timezone.utc)


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora)

    # Se o usuário for removido, suas rotinas e seus logs também são
    rotinas = db.relationship("Rotina", back_populates="usuario", cascade="all, delete-orphan")
    logs = db.relationship("Log", back_populates="usuario", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "criado_em": self.criado_em.isoformat(),
        }


class Categoria(db.Model):
    """Tabela auxiliar: agrupa rotinas (ex.: Estudo, Exercício, Saúde)."""

    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    descricao = db.Column(db.String(255))

    rotinas = db.relationship("Rotina", back_populates="categoria")

    def to_dict(self):
        return {"id": self.id, "nome": self.nome, "descricao": self.descricao}


class Rotina(db.Model):
    """Tabela principal do sistema."""

    __tablename__ = "rotinas"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255))
    ativa = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora)

    usuario = db.relationship("Usuario", back_populates="rotinas")
    categoria = db.relationship("Categoria", back_populates="rotinas")
    execucoes = db.relationship("Execucao", back_populates="rotina", cascade="all, delete-orphan")
    # Sem cascade de remoção: ao apagar a rotina, o histórico (log) é mantido com rotina_id = NULL
    logs = db.relationship("Log", back_populates="rotina")

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "categoria_id": self.categoria_id,
            "categoria": self.categoria.nome if self.categoria else None,
            "nome": self.nome,
            "descricao": self.descricao,
            "ativa": self.ativa,
            "criado_em": self.criado_em.isoformat(),
        }


class Execucao(db.Model):
    """Registro diário de execução de uma rotina."""

    __tablename__ = "execucoes"
    # Garante no BANCO que a rotina só é registrada uma vez por dia
    __table_args__ = (db.UniqueConstraint("rotina_id", "data", name="uq_execucao_rotina_data"),)

    id = db.Column(db.Integer, primary_key=True)
    rotina_id = db.Column(db.Integer, db.ForeignKey("rotinas.id"), nullable=False)
    data = db.Column(db.Date, nullable=False)
    observacao = db.Column(db.String(255))
    criado_em = db.Column(db.DateTime, nullable=False, default=agora)

    rotina = db.relationship("Rotina", back_populates="execucoes")

    def to_dict(self):
        return {
            "id": self.id,
            "rotina_id": self.rotina_id,
            "data": self.data.isoformat(),
            "observacao": self.observacao,
            "criado_em": self.criado_em.isoformat(),
        }


class Log(db.Model):
    """Histórico de ações relevantes (criação, execução, mudança de status...)."""

    __tablename__ = "logs"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    rotina_id = db.Column(db.Integer, db.ForeignKey("rotinas.id"), nullable=True)
    acao = db.Column(db.String(30), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora)

    usuario = db.relationship("Usuario", back_populates="logs")
    rotina = db.relationship("Rotina", back_populates="logs")

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "rotina_id": self.rotina_id,
            "acao": self.acao,
            "descricao": self.descricao,
            "criado_em": self.criado_em.isoformat(),
        }
