import pytest

from apps.users.models import User


@pytest.mark.django_db
class TestCustomUserManager:
    def test_create_user(self):
        user = User.objects.create_user(email="test@example.com", password="pass123")
        assert user.email == "test@example.com"
        assert user.check_password("pass123")
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_user_normalizes_email(self):
        user = User.objects.create_user(email="Test@EXAMPLE.COM", password="pass123")
        assert user.email == "test@example.com"

    def test_create_user_no_email_raises(self):
        with pytest.raises(ValueError, match="Email"):
            User.objects.create_user(email="", password="pass123")

    def test_create_superuser(self):
        user = User.objects.create_superuser(email="admin@example.com", password="pass123")
        assert user.is_staff
        assert user.is_superuser

    def test_create_superuser_not_staff_raises(self):
        with pytest.raises(ValueError, match="is_staff"):
            User.objects.create_superuser(
                email="admin@example.com", password="pass123", is_staff=False,
            )

    def test_create_superuser_not_superuser_raises(self):
        with pytest.raises(ValueError, match="is_superuser"):
            User.objects.create_superuser(
                email="admin@example.com", password="pass123", is_superuser=False,
            )

    def test_get_by_natural_key_case_insensitive(self):
        User.objects.create_user(email="test@example.com", password="pass123")
        user = User.objects.get_by_natural_key("Test@EXAMPLE.COM")
        assert user.email == "test@example.com"


@pytest.mark.django_db
class TestUserModel:
    def test_username_field_is_email(self):
        assert User.USERNAME_FIELD == "email"

    def test_str_returns_email(self):
        user = User.objects.create_user(email="test@example.com", password="pass123")
        assert str(user) == "test@example.com"

    def test_ordering(self):
        assert User._meta.ordering == ["email"]
