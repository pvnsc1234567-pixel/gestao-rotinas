from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Instâncias criadas aqui e ligadas ao app em create_app()
db = SQLAlchemy()
migrate = Migrate()
