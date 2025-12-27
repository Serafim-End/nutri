"""
Flask Extensions Initialization
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

# SQLAlchemy for database ORM
db = SQLAlchemy()

# Alembic migrations via Flask-Migrate
migrate = Migrate()

# JWT authentication
jwt = JWTManager()


