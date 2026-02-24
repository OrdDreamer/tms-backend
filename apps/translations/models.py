from django.core.validators import RegexValidator
from django.db import models

from apps.core.choices import LanguageChoices
from apps.core.models import BaseModel

key_validator = RegexValidator(
    regex=r"^[a-z0-9]+(?:[._][a-z0-9]+)*$",
    message=('Use lowercase letters and digits separated by "_" or "." '
             "(e.g., my_code_name, api.v1.endpoint).")
)

KEY_FORMAT_HELP = (
    "Lowercase letters and digits (a-z, 0-9), separated by dot or underscore; "
    "e.g. api.v1.endpoint or form.submit_button. At least 2 segments."
)


class TranslationKey(BaseModel):
    """
    Represents a key for translations within a project.

    Key format constraints (desired validation):

    - Keys must match: ^[a-z0-9]+(?:[._][a-z0-9]+)*$
    - Allowed chars: a-z, 0-9, ., _
    - Dot (.) separates namespaces
    - Underscore (_) separates words inside a segment
    - Keys must be at least 2 segments long
    - No flat keys
    """
    key = models.CharField(
        max_length=255,
        help_text=KEY_FORMAT_HELP,
        validators=[key_validator],
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="translation_keys",
        help_text="Project this translation key belongs to"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of the translation key"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["key", "project"],
                name="unique_key_per_project"
            )
        ]
        indexes = [
            models.Index(fields=["project", "key"]),
        ]
        ordering = ["project__slug", "key"]
        verbose_name = "Translation Key"
        verbose_name_plural = "Translation Keys"

    def clean(self):
        if self.key:
            self.key = self.key.lower()

    def __str__(self):
        return f"{self.key} ({self.project.slug})"


class TranslationValue(BaseModel):
    """
    Represents the actual translated text for a given key and language.

    NOTE:
        For MVP simplicity, `language` is stored as a plain CharField instead
        of a foreign key to ProjectLanguage.

        This intentionally allows translation records to exist independently
        of the current set of project languages (e.g. when languages are added
        or removed over time).

        Full domain consistency (ensuring that each translation language
        belongs to the project) is enforced at the service layer.

        This is a conscious trade-off for MVP speed and flexibility and may be
        revisited or tightened in the future if stronger referential integrity
        is required at the database level.
    """
    translation_key = models.ForeignKey(
        TranslationKey,
        on_delete=models.CASCADE,
        related_name="values",
        help_text="The translation key this value belongs to"
    )
    language = models.CharField(
        max_length=5,
        choices=LanguageChoices.choices,
        help_text="Language of the translation (ISO 639-1)"
    )
    value = models.TextField(
        help_text="Translated text"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["translation_key", "language"],
                name="unique_translation_per_language"
            )
        ]
        indexes = [
            models.Index(fields=["translation_key", "language"]),
        ]
        ordering = ["translation_key__key", "language"]
        verbose_name = "Translation Value"
        verbose_name_plural = "Translation Values"

    def __str__(self):
        return f"{self.translation_key.key} [{self.language}]"
