from django.db import models

from apps.languages.models import Language


class TranslationKey(models.Model):
    """
    Represents a key for translations within a project.
    """
    key = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique identifier for the translation"
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="translation_keys",
        help_text="Unique identifier for the translation"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of the translation key"
    )

    class Meta:
        ordering = ["key"]
        verbose_name = "Translation Key"
        verbose_name_plural = "Translation Keys"

    def __str__(self):
        return f"{self.key} ({self.project.slug})"


class TranslationValue(models.Model):
    """
    Represents the actual translated text for a given key and language.
    """
    translation_key = models.ForeignKey(
        TranslationKey,
        on_delete=models.CASCADE,
        related_name="values",
        help_text="The translation key this value belongs to"
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="translation_values",
        help_text="Language of the translation"
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
        ordering = ["translation_key", "language"]
        verbose_name = "Translation Value"
        verbose_name_plural = "Translation Values"

    def __str__(self):
        return (
            f"{self.translation_key.key} "
            f"[{self.language.code}]: {self.value[:50]}"
        )
