from flask import Blueprint, jsonify, request

from ..models import Log

bp = Blueprint("logs", __name__, url_prefix="/logs")


@bp.get("")
def listar():
    """Histórico de ações. Filtros opcionais: ?usuario_id=1&rotina_id=2&acao=EXECUTAR_ROTINA"""
    consulta = Log.query
    if request.args.get("usuario_id", type=int):
        consulta = consulta.filter_by(usuario_id=request.args.get("usuario_id", type=int))
    if request.args.get("rotina_id", type=int):
        consulta = consulta.filter_by(rotina_id=request.args.get("rotina_id", type=int))
    if request.args.get("acao"):
        consulta = consulta.filter_by(acao=request.args["acao"].upper())
    return jsonify([l.to_dict() for l in consulta.order_by(Log.id.desc()).all()])
