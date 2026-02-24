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
        ordering = ["name"]
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return f"({self.slug}) {self.name}"

    def get_base_language(self):
        for lang in self.languages.all():
            if lang.is_base_language:
                return lang
        return None


class ProjectLanguage(BaseModel):
    """
    Represents a target language for a project.

    Each project can have multiple target languages for translation.
    The base language is stored in Project.base_language.

    Business logic (adding, removing, setting base language) lives
    in apps.projects.utils.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="languages",
        help_text="Project this language belongs to"
    )
    language = models.CharField(
        max_length=5,
        choices=LanguageChoices,
        help_text="Target language (ISO 639-1)"
    )
    is_base_language = models.BooleanField(
        default=False,
        help_text=("Indicates if this language is the "
                   "base language of the project")
    )

    class Meta:
        """
        Each project-language relationship must be unique.
        Only one base language is allowed per project.
        """
        constraints = [
            models.UniqueConstraint(
                fields=["project", "language"],
                name="unique_project_language"
            ),
            # Requires SQLite 3.8.0+ and Django 3.2+
            # (partial indexes support)
            models.UniqueConstraint(
                fields=["project"],
                condition=models.Q(is_base_language=True),
                name="unique_base_language_per_project"
            ),
        ]
        ordering = ["project__name", "language"]
        verbose_name = "Project Language"
        verbose_name_plural = "Project Languages"

    def clean(self):
        """
        Ensure that each project always has a base language.
        """
        if not self.project:
            return

        base_language_does_not_exist = not ProjectLanguage.objects.filter(
            project=self.project,
            is_base_language=True
        ).exclude(pk=self.pk).exists()
        current_instance_is_not_base = not self.is_base_language

        if base_language_does_not_exist and current_instance_is_not_base:
            raise ValidationError(
                ("This project does not have a base language set. "
                 "Please set a base language")
            )

    def __repr__(self):
        return (
            f"<ProjectLanguage id={self.pk} "
            f"project={self.project_id} "
            f"language={self.language} "
            f"base={self.is_base_language}>"
        )

    def __str__(self):
        return f"[{self.project.slug}] {self.get_language_display()}"
