import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.exceptions import AuthError
from apps.factories import UserFactory
from apps.users.utils import user_change_password, user_create, user_logout, user_update


@pytest.mark.django_db
class TestUserCreate:
    def test_creates_user(self):
        user = user_create(email="new@example.com", password="strongpass123")
        assert user.email == "new@example.com"
        assert user.check_password("strongpass123")

    def test_with_extra_fields(self):
        user = user_create(
            email="new@example.com", password="strongpass123",
            first_name="John", last_name="Doe",
        )
        assert user.first_name == "John"


@pytest.mark.django_db
class TestUserUpdate:
    def test_updates_first_name(self):
        user = UserFactory()
        updated = user_update(user=user, first_name="Updated")
        assert updated.first_name == "Updated"

    def test_updates_email_normalized(self):
        user = UserFactory()
        updated = user_update(user=user, email="New@EXAMPLE.COM")
        assert updated.email == "new@example.com"

    def test_no_fields_returns_user(self):
        user = UserFactory()
        result = user_update(user=user)
        assert result == user


@pytest.mark.django_db
class TestUserChangePassword:
    def test_success(self):
        user = UserFactory()
        user_change_password(
            user=user, current_password="testpass123", new_password="newstrongpass123",
        )
        assert user.check_password("newstrongpass123")

    def test_wrong_current_password(self):
        user = UserFactory()
        with pytest.raises(AuthError, match="Invalid current password"):
            user_change_password(
                user=user, current_password="wrong", new_password="newstrongpass123",
            )

    def test_blacklists_tokens(self):
        user = UserFactory()
        refresh = RefreshToken.for_user(user)
        user_change_password(
            user=user, current_password="testpass123", new_password="newstrongpass123",
        )
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
        assert BlacklistedToken.objects.filter(token__user=user).exists()


@pytest.mark.django_db
class TestUserLogout:
    def test_blacklists_token(self):
        user = UserFactory()
        refresh = RefreshToken.for_user(user)
        user_logout(refresh_token=str(refresh))
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
        assert BlacklistedToken.objects.exists()

    def test_invalid_token_raises(self):
        with pytest.raises(AuthError, match="Invalid or expired"):
            user_logout(refresh_token="invalid-token")
