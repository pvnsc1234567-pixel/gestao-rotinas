from flask import Blueprint, jsonify, request

from ..models import Categoria
from ..services import atualizar_categoria, buscar_ou_404, criar_categoria, remover_categoria

bp = Blueprint("categorias", __name__, url_prefix="/categorias")


@bp.post("")
def criar():
    categoria = criar_categoria(request.get_json(silent=True) or {})
    return jsonify(categoria.to_dict()), 201


@bp.get("")
def listar():
    categorias = Categoria.query.order_by(Categoria.nome).all()
    return jsonify([c.to_dict() for c in categorias])


@bp.get("/<int:categoria_id>")
def detalhar(categoria_id):
    return jsonify(buscar_ou_404(Categoria, categoria_id, "Categoria").to_dict())


@bp.put("/<int:categoria_id>")
def atualizar(categoria_id):
    categoria = buscar_ou_404(Categoria, categoria_id, "Categoria")
    atualizar_categoria(categoria, request.get_json(silent=True) or {})
    return jsonify(categoria.to_dict())


@bp.delete("/<int:categoria_id>")
def remover(categoria_id):
    remover_categoria(buscar_ou_404(Categoria, categoria_id, "Categoria"))
    return "", 204
