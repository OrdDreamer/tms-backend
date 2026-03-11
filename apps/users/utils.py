from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken
)

from apps.core.exceptions import AuthError
from apps.users.models import User


def _blacklist_all_tokens_for_user(*, user) -> None:
    tokens = OutstandingToken.objects.filter(user=user)
    for token in tokens:
        BlacklistedToken.objects.get_or_create(token=token)


def user_logout(*, refresh_token: str) -> None:
    try:
        token = RefreshToken(refresh_token)  # type: ignore
    except TokenError:
        raise AuthError("Invalid or expired refresh token.")
    token.blacklist()


def user_create(*, email, password, **extra_fields):
    return User.objects.create_user(
        email=email,
        password=password,
        **extra_fields
    )


def user_update(*, user, email=None, first_name=None, last_name=None):
    update_fields = []

    if email is not None:
        user.email = User.objects.normalize_email(email).lower()
        update_fields.append("email")

    if first_name is not None:
        user.first_name = first_name
        update_fields.append("first_name")

    if last_name is not None:
        user.last_name = last_name
        update_fields.append("last_name")

    if not update_fields:
        return user

    user.full_clean()
    user.save(update_fields=update_fields)
    return user


def user_change_password(*, user, current_password, new_password):
    if not user.check_password(current_password):
        raise AuthError("Invalid current password.")
    validate_password(new_password, user)
    _blacklist_all_tokens_for_user(user=user)
    user.set_password(new_password)
    user.save(update_fields=["password"])
    return user
