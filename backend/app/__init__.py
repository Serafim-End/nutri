"""
NutriMatch Backend - Flask Application Factory
Telegram-based Nutritionists Marketplace API
"""

import logging
from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import text

from app.config import Config
from app.extensions import db, migrate, jwt

logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """Application factory pattern for Flask app."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Configure CORS for Telegram Mini App
    CORS(
        app,
        origins=app.config.get("CORS_ORIGINS", "*"),
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

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
        return {"status": "healthy", "service": "nutrimatch-api"}

    # Database health check endpoint
    @app.route("/health/db")
    def health_db():
        """
        Database health check endpoint.
        
        Verifies:
        - Database connectivity (SELECT 1)
        - Current Alembic migration revision
        
        Returns JSON with status, revision, and any errors.
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
