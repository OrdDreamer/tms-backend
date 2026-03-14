import pytest
from unittest.mock import patch
from django.db import OperationalError
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestHealthCheckAPIView:
    def setup_method(self):
        self.client = APIClient()

    def test_healthy(self):
        response = self.client.get("/api/health/")
        assert response.status_code == 200
        assert response.data == {"status": "ok", "db": "ok"}

    def test_db_unavailable(self):
        with patch(
            "apps.core.views.connection.ensure_connection",
            side_effect=OperationalError,
        ):
            response = self.client.get("/api/health/")
        assert response.status_code == 503
        assert response.data == {"status": "error", "db": "unavailable"}

    def test_no_auth_required(self):
        # Без токену — має повертати 200, не 401
        response = self.client.get("/api/health/")
        assert response.status_code == 200
