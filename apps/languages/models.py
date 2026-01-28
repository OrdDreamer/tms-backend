from django.db import models


class Language(models.Model):
    """
    Represents a language available in the system.
    """
    code = models.CharField(
        max_length=10,
        unique=True,
        help_text="ISO code of the language, e.g. 'en', 'uk', 'fr'"
    )
    name = models.CharField(
        max_length=100,
        help_text=(
            "Human-readable name of the language, e.g. 'English', 'Українська'"
        )
    )

    class Meta:
        ordering = ["code"]
        verbose_name = "Language"
        verbose_name_plural = "Languages"

    def __str__(self):
        return f"{self.name} ({self.code})"
