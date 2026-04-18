import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture
def user_password():
    return "testpass123"


@pytest.fixture
def user_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


@pytest.fixture
def api_client_with_refresh_cookie(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.cookies["refresh_token"] = str(refresh)
    return client, str(refresh)
