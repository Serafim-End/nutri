"""
NutriMatch Backend - Flask Application Factory
Telegram-based Nutritionists Marketplace API
"""

import logging
from flask import Flask, jsonify, send_from_directory
import os
from flask_cors import CORS
from flasgger import Swagger
from sqlalchemy import text

from app.config import Config
from app.extensions import db, migrate, jwt
from app.swagger import SWAGGER_CONFIG, SWAGGER_TEMPLATE

logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """Application factory pattern for Flask app."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Initialize Swagger (OpenAPI documentation)
    # Available at / (Swagger UI) and /apispec.json (OpenAPI spec)
    Swagger(app, config=SWAGGER_CONFIG, template=SWAGGER_TEMPLATE)

    media_root = app.config.get("MEDIA_ROOT", "/app/media")
    try:
        os.makedirs(media_root, exist_ok=True)
    except OSError as exc:
        logger.error("Failed to create media directory %s: %s", media_root, exc)

    # Configure CORS for Telegram Mini App
    CORS(
        app,
        origins=app.config.get("CORS_ORIGINS", "*"),
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    @jwt.unauthorized_loader
    def handle_missing_token(reason):
        logger.warning(f"JWT missing: {reason}")
        return jsonify({"error": "Missing Authorization header"}), 401

    @jwt.invalid_token_loader
    def handle_invalid_token(reason):
        logger.warning(f"JWT invalid: {reason}")
        return jsonify({"error": "Invalid token"}), 401

    @jwt.expired_token_loader
    def handle_expired_token(jwt_header, jwt_payload):
        logger.info("JWT expired")
        return jsonify({"error": "Token has expired"}), 401

    @jwt.revoked_token_loader
    def handle_revoked_token(jwt_header, jwt_payload):
        logger.warning("JWT revoked")
        return jsonify({"error": "Token has been revoked"}), 401

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.clients import clients_bp
    from app.routes.nutritionists import nutritionists_bp
    from app.routes.bookings import bookings_bp
    from app.routes.payments import payments_bp
    from app.routes.admin import admin_bp
    from app.routes.public import public_bp
    from app.routes.bot import bot_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(clients_bp, url_prefix="/api/clients")
    app.register_blueprint(nutritionists_bp, url_prefix="/api/nutritionists")
    app.register_blueprint(bookings_bp, url_prefix="/api/bookings")
    app.register_blueprint(payments_bp, url_prefix="/api/payments")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(public_bp, url_prefix="/api/public")
    app.register_blueprint(bot_bp, url_prefix="/api/bot")

    # Basic health check endpoint
    @app.route("/health")
    def health():
        """
        Проверка здоровья сервиса
        ---
        tags:
          - Health
        produces:
          - application/json
        responses:
          200:
            description: Сервис работает
            schema:
              $ref: '#/definitions/HealthResponse'
        """
        return {"status": "healthy", "service": "nutrimatch-api"}

    @app.route("/media/<path:filename>")
    def media(filename: str):
        media_root = app.config.get("MEDIA_ROOT", "/app/media")
        safe_path = os.path.normpath(filename)
        if safe_path.startswith(".."):
            return jsonify({"error": "Invalid path"}), 400
        return send_from_directory(media_root, safe_path)

    @app.route("/docs/<path:filename>")
    def docs(filename: str):
        """Serve static documents (legal, public offer, etc.)."""
        docs_dir = os.path.join(os.path.dirname(__file__), "..", "static", "docs")
        safe_path = os.path.normpath(filename)
        if safe_path.startswith(".."):
            return jsonify({"error": "Invalid path"}), 400
        return send_from_directory(docs_dir, safe_path)

    # Database health check endpoint
    @app.route("/health/db")
    def health_db():
        """
        Проверка здоровья БД
        ---
        tags:
          - Health
        description: |
          Проверяет:
          - Подключение к базе данных (SELECT 1)
          - Текущую ревизию Alembic миграций
        produces:
          - application/json
        responses:
          200:
            description: БД доступна
            schema:
              $ref: '#/definitions/DatabaseHealthResponse'
          503:
            description: БД недоступна
            schema:
              $ref: '#/definitions/DatabaseHealthResponse'
        """
        result = {
            "status": "unknown",
            "database": "unknown",
            "connection": False,
            "revision": None,
            "error": None,
        }
        
        try:
            # Test database connectivity
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                result["connection"] = True
            
            # Get database info from URL (without password)
            db_url = str(db.engine.url)
            if "@" in db_url:
                # Hide password in output
                parts = db_url.split("@")
                scheme_user = parts[0].rsplit(":", 1)[0]  # Remove password
                result["database"] = f"{scheme_user}:***@{parts[1]}"
            else:
                result["database"] = db_url
            
            # Check if this is Supabase
            if "supabase" in result["database"].lower():
                result["provider"] = "supabase"
            else:
                result["provider"] = "postgresql"
            
            # Get current Alembic revision
            try:
                with db.engine.connect() as conn:
                    revision_result = conn.execute(
                        text("SELECT version_num FROM alembic_version LIMIT 1")
                    )
                    row = revision_result.fetchone()
                    if row:
                        result["revision"] = row[0]
                    else:
                        result["revision"] = "none (no migrations applied)"
            except Exception as e:
                # alembic_version table might not exist yet
                result["revision"] = f"unknown ({str(e)[:50]})"
            
            result["status"] = "healthy"
            return jsonify(result), 200
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            result["status"] = "unhealthy"
            result["error"] = str(e)
            return jsonify(result), 503

    return app
