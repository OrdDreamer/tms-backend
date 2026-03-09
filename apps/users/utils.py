from django.contrib.auth.password_validation import validate_password

from apps.users.models import User


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


def user_change_password(*, user, new_password):
    validate_password(new_password, user)
    user.set_password(new_password)
    user.save(update_fields=["password"])
    return user
