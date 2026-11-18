from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from config import Config

from .extensions import db, migrate
from .services import ErroNegocio


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.json.ensure_ascii = False  # mantém acentos nas respostas JSON

    db.init_app(app)
    migrate.init_app(app, db)

    # Importar os models é o que permite ao Flask-Migrate "enxergar" as tabelas
    from . import models  # noqa: F401
    from .routes import categorias, execucoes, logs, rotinas, usuarios

    for modulo in (usuarios, categorias, rotinas, execucoes, logs):
        app.register_blueprint(modulo.bp)

    @app.get("/")
    def raiz():
        return jsonify({"sistema": "Gestão de Rotinas", "status": "ok"})

    @app.errorhandler(ErroNegocio)
    def tratar_erro_negocio(erro):
        return jsonify({"erro": erro.mensagem}), erro.status

    @app.errorhandler(HTTPException)
    def tratar_erro_http(erro):
        return jsonify({"erro": erro.description}), erro.code

    return app
