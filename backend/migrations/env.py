"""
Alembic environment configuration for Flask-Migrate.

Loads database configuration from Flask app config.
"""

import logging
import os
import sys
from logging.config import fileConfig

from flask import current_app
from alembic import context

# Ensure the backend app is in the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")


def get_engine():
    """Get SQLAlchemy engine from Flask-Migrate extension."""
    try:
        # Flask-SQLAlchemy < 3.0
        return current_app.extensions["migrate"].db.get_engine()
    except (TypeError, AttributeError):
        # Flask-SQLAlchemy >= 3.0
        return current_app.extensions["migrate"].db.engine


def get_engine_url():
    """Get database URL from engine, properly escaped for Alembic."""
    try:
        return get_engine().url.render_as_string(hide_password=False).replace(
            "%", "%%"
        )
    except AttributeError:
        return str(get_engine().url).replace("%", "%%")


def get_metadata():
    """Get SQLAlchemy metadata from Flask-Migrate extension."""
    target_db = current_app.extensions["migrate"].db
    
    # Import all models to ensure they're registered with metadata
    # This is crucial for autogenerate to detect all tables
    from app import models  # noqa: F401
    
    if hasattr(target_db, "metadatas"):
        return target_db.metadatas[None]
    return target_db.metadata


# Set the database URL from Flask app config
# This ensures we use the same normalized URL as the Flask app
config.set_main_option("sqlalchemy.url", get_engine_url())
target_db = current_app.extensions["migrate"].db


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    useful for generating SQL scripts without database connectivity.
    """
    url = config.get_main_option("sqlalchemy.url")
    
    context.configure(
        url=url,
        target_metadata=get_metadata(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Creates an engine and associates a connection with the context.
    """

    def process_revision_directives(context, revision, directives):
        """Callback to prevent empty migrations."""
        if getattr(config.cmd_opts, "autogenerate", False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info("No changes in schema detected.")

    conf_args = current_app.extensions["migrate"].configure_args.copy()
    if conf_args.get("process_revision_directives") is None:
        conf_args["process_revision_directives"] = process_revision_directives

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            **conf_args,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
