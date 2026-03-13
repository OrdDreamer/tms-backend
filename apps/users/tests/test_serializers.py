import pytest

from apps.users.serializers import (
    UserChangePasswordInputSerializer,
    UserLogoutInputSerializer,
    UserMeUpdateInputSerializer,
)


class TestUserChangePasswordInputSerializer:
    def test_valid_data(self):
        data = {
            "current_password": "oldpass123",
            "new_password": "newpass123",
            "new_password_confirm": "newpass123",
        }
        serializer = UserChangePasswordInputSerializer(data=data)
        assert serializer.is_valid()

    def test_password_mismatch(self):
        data = {
            "current_password": "oldpass123",
            "new_password": "newpass123",
            "new_password_confirm": "different123",
        }
        serializer = UserChangePasswordInputSerializer(data=data)
        assert not serializer.is_valid()
        assert "new_password_confirm" in serializer.errors

    def test_min_length(self):
        data = {
            "current_password": "oldpass123",
            "new_password": "short",
            "new_password_confirm": "short",
        }
        serializer = UserChangePasswordInputSerializer(data=data)
        assert not serializer.is_valid()
        assert "new_password" in serializer.errors


class TestUserLogoutInputSerializer:
    def test_refresh_required(self):
        serializer = UserLogoutInputSerializer(data={})
        assert not serializer.is_valid()
        assert "refresh" in serializer.errors


class TestUserMeUpdateInputSerializer:
    def test_all_optional(self):
        serializer = UserMeUpdateInputSerializer(data={})
        assert serializer.is_valid()

    def test_partial_update(self):
        serializer = UserMeUpdateInputSerializer(data={"first_name": "John"})
        assert serializer.is_valid()
        assert serializer.validated_data["first_name"] == "John"
