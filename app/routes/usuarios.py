from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Usuario
from ..services import atualizar_usuario, buscar_ou_404, criar_usuario

bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


@bp.post("")
def criar():
    usuario = criar_usuario(request.get_json(silent=True) or {})
    return jsonify(usuario.to_dict()), 201


@bp.get("")
def listar():
    usuarios = Usuario.query.order_by(Usuario.id).all()
    return jsonify([u.to_dict() for u in usuarios])


@bp.get("/<int:usuario_id>")
def detalhar(usuario_id):
    return jsonify(buscar_ou_404(Usuario, usuario_id, "Usuário").to_dict())


@bp.put("/<int:usuario_id>")
def atualizar(usuario_id):
    usuario = buscar_ou_404(Usuario, usuario_id, "Usuário")
    atualizar_usuario(usuario, request.get_json(silent=True) or {})
    return jsonify(usuario.to_dict())


@bp.delete("/<int:usuario_id>")
def remover(usuario_id):
    usuario = buscar_ou_404(Usuario, usuario_id, "Usuário")
    db.session.delete(usuario)
    db.session.commit()
    return "", 204
