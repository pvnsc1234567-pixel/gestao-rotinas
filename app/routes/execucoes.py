from flask import Blueprint, jsonify, request

from ..models import Execucao, Rotina
from ..services import buscar_ou_404, registrar_execucao, remover_execucao

bp = Blueprint("execucoes", __name__)


@bp.post("/rotinas/<int:rotina_id>/execucoes")
def registrar(rotina_id):
    """Registra a execução da rotina. Corpo opcional: {"data": "AAAA-MM-DD", "observacao": "..."}"""
    rotina = buscar_ou_404(Rotina, rotina_id, "Rotina")
    execucao = registrar_execucao(rotina, request.get_json(silent=True) or {})
    return jsonify(execucao.to_dict()), 201


@bp.get("/rotinas/<int:rotina_id>/execucoes")
def listar(rotina_id):
    rotina = buscar_ou_404(Rotina, rotina_id, "Rotina")
    execucoes = Execucao.query.filter_by(rotina_id=rotina.id).order_by(Execucao.data.desc()).all()
    return jsonify([e.to_dict() for e in execucoes])


@bp.delete("/execucoes/<int:execucao_id>")
def remover(execucao_id):
    remover_execucao(buscar_ou_404(Execucao, execucao_id, "Execução"))
    return "", 204
