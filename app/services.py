"""Regras de negócio e funções auxiliares.

As rotas (app/routes) só recebem a requisição e chamam estas funções;
é aqui que ficam as validações e as regras do sistema.
"""
from datetime import date

from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import Categoria, Execucao, Log, Rotina, Usuario


class ErroNegocio(Exception):
    """Erro de validação ou de regra de negócio, devolvido ao cliente em JSON."""

    def __init__(self, mensagem, status=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


# ---------------------------------------------------------------- auxiliares
def buscar_ou_404(modelo, id_, nome):
    objeto = db.session.get(modelo, id_)
    if objeto is None:
        raise ErroNegocio(f"{nome} não encontrado(a).", 404)
    return objeto


def exigir_campos(dados, *campos):
    faltando = [c for c in campos if dados.get(c) in (None, "")]
    if faltando:
        raise ErroNegocio("Campos obrigatórios ausentes: " + ", ".join(faltando), 400)


def validar_texto(valor, campo, maximo):
    if not isinstance(valor, str) or not valor.strip():
        raise ErroNegocio(f'O campo "{campo}" deve ser um texto não vazio.', 400)
    if len(valor.strip()) > maximo:
        raise ErroNegocio(f'O campo "{campo}" aceita no máximo {maximo} caracteres.', 400)
    return valor.strip()


def registrar_log(usuario_id, acao, descricao, rotina_id=None):
    """Adiciona um log à sessão. Quem chama faz o commit (assim tudo é salvo junto)."""
    db.session.add(Log(usuario_id=usuario_id, rotina_id=rotina_id, acao=acao, descricao=descricao))


# ------------------------------------------------------------------ usuários
def criar_usuario(dados):
    exigir_campos(dados, "nome", "email")
    nome = validar_texto(dados["nome"], "nome", 100)
    email = validar_texto(dados["email"], "email", 120).lower()
    if "@" not in email:
        raise ErroNegocio("E-mail inválido.", 400)
    if Usuario.query.filter_by(email=email).first():
        raise ErroNegocio("Já existe um usuário com este e-mail.", 409)

    usuario = Usuario(nome=nome, email=email)
    db.session.add(usuario)
    db.session.commit()
    return usuario


def atualizar_usuario(usuario, dados):
    if "nome" in dados:
        usuario.nome = validar_texto(dados["nome"], "nome", 100)
    if "email" in dados:
        email = validar_texto(dados["email"], "email", 120).lower()
        if "@" not in email:
            raise ErroNegocio("E-mail inválido.", 400)
        outro = Usuario.query.filter_by(email=email).first()
        if outro and outro.id != usuario.id:
            raise ErroNegocio("Já existe um usuário com este e-mail.", 409)
        usuario.email = email
    db.session.commit()
    return usuario


# ---------------------------------------------------------------- categorias
def criar_categoria(dados):
    exigir_campos(dados, "nome")
    nome = validar_texto(dados["nome"], "nome", 50)
    if Categoria.query.filter(db.func.lower(Categoria.nome) == nome.lower()).first():
        raise ErroNegocio("Já existe uma categoria com este nome.", 409)
    categoria = Categoria(nome=nome, descricao=dados.get("descricao"))
    db.session.add(categoria)
    db.session.commit()
    return categoria


def atualizar_categoria(categoria, dados):
    if "nome" in dados:
        nome = validar_texto(dados["nome"], "nome", 50)
        outra = Categoria.query.filter(db.func.lower(Categoria.nome) == nome.lower()).first()
        if outra and outra.id != categoria.id:
            raise ErroNegocio("Já existe uma categoria com este nome.", 409)
        categoria.nome = nome
    if "descricao" in dados:
        categoria.descricao = dados["descricao"]
    db.session.commit()
    return categoria


def remover_categoria(categoria):
    if categoria.rotinas:
        raise ErroNegocio("Categoria em uso por rotinas; não pode ser removida.", 409)
    db.session.delete(categoria)
    db.session.commit()


# ------------------------------------------------------------------- rotinas
def criar_rotina(dados):
    exigir_campos(dados, "usuario_id", "nome")
    usuario = buscar_ou_404(Usuario, dados["usuario_id"], "Usuário")
    categoria_id = dados.get("categoria_id")
    if categoria_id is not None:
        buscar_ou_404(Categoria, categoria_id, "Categoria")

    rotina = Rotina(
        usuario_id=usuario.id,
        categoria_id=categoria_id,
        nome=validar_texto(dados["nome"], "nome", 100),
        descricao=dados.get("descricao"),
    )
    db.session.add(rotina)
    db.session.flush()  # gera o id da rotina antes do commit, para usar no log
    registrar_log(usuario.id, "CRIAR_ROTINA", f"Rotina '{rotina.nome}' criada.", rotina.id)
    db.session.commit()
    return rotina


def atualizar_rotina(rotina, dados):
    if "nome" in dados:
        rotina.nome = validar_texto(dados["nome"], "nome", 100)
    if "descricao" in dados:
        rotina.descricao = dados["descricao"]
    if "categoria_id" in dados:
        if dados["categoria_id"] is not None:
            buscar_ou_404(Categoria, dados["categoria_id"], "Categoria")
        rotina.categoria_id = dados["categoria_id"]
    registrar_log(rotina.usuario_id, "ATUALIZAR_ROTINA", f"Rotina '{rotina.nome}' atualizada.", rotina.id)
    db.session.commit()
    return rotina


def alterar_status_rotina(rotina, ativa):
    if not isinstance(ativa, bool):
        raise ErroNegocio('O campo "ativa" deve ser true ou false.', 400)
    if rotina.ativa == ativa:
        situacao = "ativa" if ativa else "inativa"
        raise ErroNegocio(f"A rotina já está {situacao}.", 409)

    rotina.ativa = ativa
    acao = "ATIVAR_ROTINA" if ativa else "DESATIVAR_ROTINA"
    verbo = "ativada" if ativa else "desativada"
    registrar_log(rotina.usuario_id, acao, f"Rotina '{rotina.nome}' {verbo}.", rotina.id)
    db.session.commit()
    return rotina


def remover_rotina(rotina):
    # O log é gravado sem rotina_id, pois a rotina deixará de existir
    registrar_log(rotina.usuario_id, "REMOVER_ROTINA", f"Rotina '{rotina.nome}' (id {rotina.id}) removida.")
    db.session.delete(rotina)
    db.session.commit()


# ---------------------------------------------------------------- execuções
def registrar_execucao(rotina, dados):
    """REGRA PRINCIPAL: uma rotina só pode ser registrada uma vez por dia e apenas se estiver ativa."""
    # 1) Rotina precisa estar ativa
    if not rotina.ativa:
        raise ErroNegocio("Não é possível registrar execução de uma rotina inativa.", 409)

    # 2) Data da execução (padrão: hoje); não aceita datas futuras
    texto_data = dados.get("data")
    if texto_data is None:
        data_execucao = date.today()
    else:
        try:
            data_execucao = date.fromisoformat(str(texto_data))
        except ValueError:
            raise ErroNegocio("Data inválida. Use o formato AAAA-MM-DD.", 400)
    if data_execucao > date.today():
        raise ErroNegocio("Não é possível registrar execução em data futura.", 400)

    # 3) Não pode existir outra execução da mesma rotina no mesmo dia
    ja_existe = Execucao.query.filter_by(rotina_id=rotina.id, data=data_execucao).first()
    if ja_existe:
        raise ErroNegocio(f"A rotina já foi registrada em {data_execucao.isoformat()}.", 409)

    execucao = Execucao(rotina_id=rotina.id, data=data_execucao, observacao=dados.get("observacao"))
    db.session.add(execucao)
    registrar_log(
        rotina.usuario_id,
        "EXECUTAR_ROTINA",
        f"Rotina '{rotina.nome}' executada em {data_execucao.isoformat()}.",
        rotina.id,
    )
    try:
        db.session.commit()
    except IntegrityError:
        # Segunda barreira: a constraint única do banco barra requisições simultâneas
        db.session.rollback()
        raise ErroNegocio(f"A rotina já foi registrada em {data_execucao.isoformat()}.", 409)
    return execucao


def remover_execucao(execucao):
    rotina = execucao.rotina
    registrar_log(
        rotina.usuario_id,
        "REMOVER_EXECUCAO",
        f"Execução de {execucao.data.isoformat()} da rotina '{rotina.nome}' removida.",
        rotina.id,
    )
    db.session.delete(execucao)
    db.session.commit()
