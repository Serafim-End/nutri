"""
Tests for authentication endpoints.
"""

import pytest


class TestAuth:
    """Test authentication endpoints."""

    def test_verify_telegram_missing_body(self, client):
        """Test verification with missing request body."""
        response = client.post("/api/auth/telegram/verify")
        assert response.status_code == 400
        assert "error" in response.json

    def test_verify_telegram_invalid_init_data(self, client):
        """Test verification with invalid init_data."""
        response = client.post(
            "/api/auth/telegram/verify",
            json={"init_data": "invalid_data"},
        )
        assert response.status_code == 401

    def test_verify_telegram_test_data_in_debug(self, app, client):
        """Test verification with test data in debug mode."""
        app.debug = True
        response = client.post(
            "/api/auth/telegram/verify",
            json={"init_data": "test_123456_John_Doe"},
        )
        # Should succeed in debug mode with test_ prefix
        assert response.status_code == 200
        assert "access_token" in response.json
        assert response.json["profile"]["telegram_user_id"] == 123456
        app.debug = False

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json["status"] == "healthy"


