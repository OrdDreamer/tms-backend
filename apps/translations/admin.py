from django.contrib import admin
from django.utils.text import Truncator

from apps.translations.models import TranslationKey, TranslationValue


class TranslationValueInline(admin.TabularInline):
    model = TranslationValue
    extra = 0
    fields = ("language", "value")


@admin.register(TranslationKey)
class TranslationKeyAdmin(admin.ModelAdmin):
    """
    Admin configuration for the TranslationKey model.

    Defines list display, search, filter by project. Inline translation values.
    """
    list_display = ("key", "project", "display_description")
    search_fields = ("key", "project__slug", "project__name")
    list_filter = ("project",)
    autocomplete_fields = ("project",)
    readonly_fields = ("created_at", "updated_at")
    inlines = (TranslationValueInline,)

    fieldsets = (
        (None, {"fields": ("key", "project", "description")}),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("project")

    def display_description(self, obj):
        return Truncator(obj.description).words(10) if obj.description else "-"

    display_description.short_description = "Description"


@admin.register(TranslationValue)
class TranslationValueAdmin(admin.ModelAdmin):
    """
    Admin configuration for the TranslationValue model.

    Defines list display, search, filters by language and project.
    """
    list_display = ("display_translation_key", "language",
                    "display_value_preview")
    search_fields = (
        "translation_key__key",
        "translation_key__project__slug",
        "value",
    )
    list_filter = ("translation_key__project", "language")
    autocomplete_fields = ("translation_key",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("translation_key", "language", "value")}),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("translation_key", "translation_key__project")

    def display_translation_key(self, obj):
        return f"{obj.translation_key.key} ({obj.translation_key.project.slug})"

    display_translation_key.short_description = "Translation Key"

    def display_value_preview(self, obj):
        return Truncator(obj.value).chars(80) if obj.value else "-"

    display_value_preview.short_description = "Value"
