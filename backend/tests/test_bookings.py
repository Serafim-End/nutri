"""
Tests for booking endpoints.
"""

import pytest
from datetime import datetime, timedelta


class TestBookings:
    """Test booking endpoints."""

    def test_create_booking_unauthorized(self, client):
        """Test booking creation without auth."""
        response = client.post(
            "/api/bookings",
            json={"service_id": "123", "slot_id": "456"},
        )
        assert response.status_code == 401

    def test_release_expired_holds(self, client):
        """Test expired holds release endpoint."""
        response = client.post("/api/bookings/release-expired-holds")
        assert response.status_code == 200
        assert "released_count" in response.json


class TestPublicEndpoints:
    """Test public endpoints."""

    def test_list_nutritionists(self, client):
        """Test listing nutritionists."""
        response = client.get("/api/public/nutritionists")
        assert response.status_code == 200
        assert "nutritionists" in response.json
        assert "total" in response.json

    def test_get_nutritionist_not_found(self, client):
        """Test getting non-existent nutritionist."""
        response = client.get(
            "/api/public/nutritionists/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404


