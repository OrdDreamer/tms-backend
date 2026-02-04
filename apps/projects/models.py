from django.core.exceptions import ValidationError
from django.db import models

from apps.core.choices import LanguageChoices
from apps.core.models import BaseModel


class Project(BaseModel):
    """
    Represents a project which has a set of translation keys
    and associated languages.
    """
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="Unique identifier for the project used in URLs"
    )
    name = models.CharField(
        max_length=255,
        help_text="Human-readable name of the project"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of the project"
    )

    class Meta:
        ordering = ["slug", "name"]
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return f"{self.name} ({self.slug})"


class ProjectLanguage(BaseModel):
    """
    Represents a target language for a project.
    
    Each project can have multiple target languages for translation.
    The base language is stored in Project.base_language.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='languages',
        help_text="Project this language belongs to"
    )
    language = models.CharField(
        max_length=10,
        choices=LanguageChoices.choices,
        help_text="Target language (ISO 639-1)"
    )
    is_base_language = models.BooleanField(
        default=False,
        help_text="Indicates if this language is the base language of the project"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'language'],
                name='unique_project_language'
            )
        ]
        ordering = ['project__name', 'language']
        verbose_name = "Project Language"
        verbose_name_plural = "Project Languages"

    def clean(self):
        # Перевірка: лише одна базова мова
        if self.is_base_language:
            if ProjectLanguage.objects.filter(
                    project=self.project,
                    is_base_language=True
            ).exclude(pk=self.pk).exists():
                raise ValidationError(
                    "A project can have only one base language."
                )

    def delete(self, *args, **kwargs):
        if self.is_base_language:
            raise ValidationError(
                "Cannot delete the base language. "
                "First set another language as base."
            )

        if ProjectLanguage.objects.filter(project=self.project).count() <= 1:
            raise ValidationError(
                "Cannot delete the last language of a project."
            )

        super().delete(*args, **kwargs)

    def __repr__(self):
        return (f"{self.project.name} ({self.project.slug}) "
                f"- {self.get_language_display()}")

    def __str__(self):
        return f"[{self.project.slug}] {self.get_language_display()}"
