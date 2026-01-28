from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        # Normalize the domain part of the email
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra_fields)

    def get_by_natural_key(self, username):
        """
        Normalize email before lookup so that varying case in the domain
        doesn’t block authentication.
        """
        email = self.normalize_email(username)
        return self.get(**{self.model.USERNAME_FIELD: email})


class User(AbstractUser):
    """
    Represents a user in the system with email as the unique identifier.
    Username field is not used.
    """
    username = None
    email = models.EmailField(
        unique=True,
        help_text="Email address used as the unique identifier for login"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        ordering = ["email"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email
