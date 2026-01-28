from django.db import models

from apps.languages.models import Language


class Project(models.Model):
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
    base_language = models.ForeignKey(
        Language,
        on_delete=models.SET_NULL,
        null=True,
        related_name="default_for_projects",
        help_text="Base language of the project"
    )
    languages = models.ManyToManyField(
        Language,
        related_name="projects",
        blank=True,
        help_text="Languages enabled for this project"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return f"{self.name} ({self.slug})"
