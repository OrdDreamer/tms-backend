import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.factories import UserFactory


@pytest.mark.django_db
class TestUserLogoutView:
    def test_logout_success(self, api_client, user):
        refresh = RefreshToken.for_user(user)
        response = api_client.post(
            reverse("auth-logout"),
            {"refresh": str(refresh)},
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_logout_invalid_token(self, api_client):
        response = api_client.post(
            reverse("auth-logout"),
            {"refresh": "invalid"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserListView:
    def test_requires_auth(self, api_client):
        response = api_client.get(reverse("users:user-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_users(self, authenticated_client, user):
        response = authenticated_client.get(reverse("users:user-list"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_pagination(self, authenticated_client, user):
        for i in range(25):
            UserFactory(email=f"bulk{i}@example.com")
        response = authenticated_client.get(reverse("users:user-list"))
        assert response.data["count"] == 26  # 25 + authenticated user
        assert len(response.data["results"]) == 20  # default limit

    def test_search(self, authenticated_client, user):
        UserFactory(email="searchme@example.com", first_name="Findable")
        response = authenticated_client.get(
            reverse("users:user-list"), {"search": "Findable"},
        )
        assert response.data["count"] == 1


@pytest.mark.django_db
class TestUserDetailView:
    def test_retrieve_user(self, authenticated_client, user):
        other = UserFactory()
        response = authenticated_client.get(
            reverse("users:user-detail", kwargs={"user_id": other.id}),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == other.email

    def test_not_found(self, authenticated_client):
        response = authenticated_client.get(
            reverse("users:user-detail", kwargs={"user_id": 99999}),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestUserMeView:
    def test_get_me(self, authenticated_client, user):
        response = authenticated_client.get(reverse("users:user-me"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email

    def test_patch_me(self, authenticated_client, user):
        response = authenticated_client.patch(
            reverse("users:user-me"),
            {"first_name": "Updated"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Updated"


@pytest.mark.django_db
class TestUserChangePasswordView:
    def test_change_password_success(self, authenticated_client, user):
        response = authenticated_client.post(
            reverse("users:user-change-password"),
            {
                "current_password": "testpass123",
                "new_password": "newstrongpass123",
                "new_password_confirm": "newstrongpass123",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_change_password_wrong_current(self, authenticated_client, user):
        response = authenticated_client.post(
            reverse("users:user-change-password"),
            {
                "current_password": "wrongpass",
                "new_password": "newstrongpass123",
                "new_password_confirm": "newstrongpass123",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_mismatch(self, authenticated_client, user):
        response = authenticated_client.post(
            reverse("users:user-change-password"),
            {
                "current_password": "testpass123",
                "new_password": "newstrongpass123",
                "new_password_confirm": "different123",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
