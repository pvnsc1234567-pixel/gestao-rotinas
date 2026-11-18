import os

from dotenv import load_dotenv

# Lê as variáveis do arquivo .env (se existir)
load_dotenv()


class Config:
    # Conexão com o banco vem do .env; sem ela, usa SQLite local
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///rotinas.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
