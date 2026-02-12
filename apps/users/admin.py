from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.users.models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    """
    Custom admin configuration for the User model.

    Displays email, first_name, last_name, and permission fields.
    Provides search by email and name fields.
    """
    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_superuser",
        "is_active"
    )
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    list_filter = ("is_staff", "is_superuser", "is_active")

    fieldsets = (
        (None, {"fields": ("email", "first_name", "last_name", "password")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "is_active", "groups", "user_permissions")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "first_name",
                "last_name",
                "password1",
                "password2"
            ),
        }),
    )
