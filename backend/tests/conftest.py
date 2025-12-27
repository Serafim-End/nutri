"""
Pytest configuration and fixtures.
"""

import pytest
from app import create_app
from app.config import TestingConfig
from app.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    """Create application for the tests."""
    app = create_app(TestingConfig)
    app.config["TESTING"] = True
    return app


@pytest.fixture(scope="session")
def db(app):
    """Create database for the tests."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()


@pytest.fixture(scope="function")
def session(app, db):
    """Create a new database session for a test."""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        # Bind the connection to the session
        db.session.configure(bind=connection)

        yield db.session

        db.session.remove()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_headers(app, session):
    """Create authenticated headers for testing."""
    from flask_jwt_extended import create_access_token
    from app.models import Profile

    with app.app_context():
        # Create test user
        profile = Profile(
            telegram_user_id=123456789,
            full_name="Test User",
            role="client",
        )
        session.add(profile)
        session.commit()

        # Create token
        token = create_access_token(
            identity=str(profile.id),
            additional_claims={"role": "client", "telegram_user_id": 123456789},
        )

        return {"Authorization": f"Bearer {token}"}, profile


@pytest.fixture
def admin_headers(app, session):
    """Create admin authenticated headers for testing."""
    from flask_jwt_extended import create_access_token
    from app.models import Profile

    with app.app_context():
        # Create admin user
        profile = Profile(
            telegram_user_id=999999999,
            full_name="Admin User",
            role="admin",
        )
        session.add(profile)
        session.commit()

        # Create token
        token = create_access_token(
            identity=str(profile.id),
            additional_claims={"role": "admin", "telegram_user_id": 999999999},
        )

        return {"Authorization": f"Bearer {token}"}, profile


