from flask import Blueprint, jsonify, request

from ..models import Rotina
from ..services import (
    ErroNegocio,
    alterar_status_rotina,
    atualizar_rotina,
    buscar_ou_404,
    criar_rotina,
    remover_rotina,
)

bp = Blueprint("rotinas", __name__, url_prefix="/rotinas")


@bp.post("")
def criar():
    rotina = criar_rotina(request.get_json(silent=True) or {})
    return jsonify(rotina.to_dict()), 201


@bp.get("")
def listar():
    """Filtros opcionais: ?usuario_id=1&categoria_id=2&ativa=true"""
    consulta = Rotina.query
    if request.args.get("usuario_id", type=int):
        consulta = consulta.filter_by(usuario_id=request.args.get("usuario_id", type=int))
    if request.args.get("categoria_id", type=int):
        consulta = consulta.filter_by(categoria_id=request.args.get("categoria_id", type=int))
    if "ativa" in request.args:
        valor = request.args["ativa"].lower()
        if valor not in ("true", "false"):
            raise ErroNegocio('O filtro "ativa" deve ser true ou false.', 400)
        consulta = consulta.filter_by(ativa=(valor == "true"))
    return jsonify([r.to_dict() for r in consulta.order_by(Rotina.id).all()])


@bp.get("/<int:rotina_id>")
def detalhar(rotina_id):
    return jsonify(buscar_ou_404(Rotina, rotina_id, "Rotina").to_dict())


@bp.put("/<int:rotina_id>")
def atualizar(rotina_id):
    rotina = buscar_ou_404(Rotina, rotina_id, "Rotina")
    atualizar_rotina(rotina, request.get_json(silent=True) or {})
    return jsonify(rotina.to_dict())


@bp.patch("/<int:rotina_id>/status")
def alterar_status(rotina_id):
    """Ativa ou desativa a rotina. Corpo: {"ativa": true} ou {"ativa": false}"""
    rotina = buscar_ou_404(Rotina, rotina_id, "Rotina")
    dados = request.get_json(silent=True) or {}
    if "ativa" not in dados:
        raise ErroNegocio('Campo obrigatório ausente: "ativa".', 400)
    alterar_status_rotina(rotina, dados["ativa"])
    return jsonify(rotina.to_dict())


@bp.delete("/<int:rotina_id>")
def remover(rotina_id):
    remover_rotina(buscar_ou_404(Rotina, rotina_id, "Rotina"))
    return "", 204
