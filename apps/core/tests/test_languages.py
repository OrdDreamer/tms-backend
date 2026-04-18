import pytest
from rest_framework.test import APIClient

from apps.core.choices import LanguageChoices


@pytest.mark.django_db
class TestLanguageListAPIView:
    def setup_method(self):
        self.client = APIClient()

    def test_returns_all_languages(self):
        response = self.client.get("/api/v1/languages/")
        assert response.status_code == 200
        assert len(response.data) == len(LanguageChoices.choices)

    def test_response_shape(self):
        response = self.client.get("/api/v1/languages/")
        for item in response.data:
            assert "code" in item
            assert "name" in item

    def test_contains_known_language(self):
        response = self.client.get("/api/v1/languages/")
        assert {"code": "en", "name": "English"} in response.data

    def test_no_auth_required(self):
        response = self.client.get("/api/v1/languages/")
        assert response.status_code == 200
