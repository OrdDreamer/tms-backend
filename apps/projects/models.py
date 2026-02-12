from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Case, When, Value, BooleanField

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
        return f"({self.slug}) {self.name}"

    def get_base_language(self):
        return self.languages.filter(is_base_language=True).first()


class ProjectLanguage(BaseModel):
    """
    Represents a target language for a project.

    Each project can have multiple target languages for translation.
    The base language is stored in Project.base_language.

    NOTE:
    The validation and business restrictions in this model (e.g., preventing
    deletion of the base language, ensuring at least one language exists,
    enforcing a single base language) are left here for historical/contextual
    purposes and “as-is”. Full business logic and constraints should be enforced
    at the service layer. Some of these checks can be safely removed here if
    they conflict with service-layer implementation.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="languages",
        help_text="Project this language belongs to"
    )
    language = models.CharField(
        max_length=5,
        choices=LanguageChoices.choices,
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

        NOTE:
        These constraints are left in the model for historical/reference purposes.
        The full enforcement of business rules (e.g., base language uniqueness,
        deletion restrictions) should be done at the service layer. Some of these
        constraints can be removed if the service layer fully guarantees consistency.
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

        NOTE:
        This validation is kept for reference and convenience.
        Full business logic for language assignment should be handled
        in the service layer. Some checks here can be safely removed
        if they conflict with service-layer logic.
        """
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

    @transaction.atomic
    def delete(self, *args, **kwargs):
        """
        Prevent deleting the base language or the last language of a project.

        NOTE:
        This check is kept for reference and convenience.
        Full deletion logic should be enforced in the service layer.
        """
        if self.is_base_language:
            raise ValidationError(
                "Cannot delete the base language. "
                "First set another language as base."
            )

        # Lock the project languages to prevent race conditions
        languages = ProjectLanguage.objects.select_for_update().filter(
            project=self.project
        )
        if not languages.exclude(pk=self.pk).exists():
            raise ValidationError(
                "Cannot delete the last language of a project."
            )

        super().delete(*args, **kwargs)

    @transaction.atomic
    def set_base_language(self):
        """
        Atomically sets this language as the base language,
        unsetting the previous one.

        NOTE:
        This is left in the model for convenience. Full base-language
        assignment logic should be handled in the service layer.
        """
        if self.is_base_language:
            return

        ProjectLanguage.objects.select_for_update().filter(
            project=self.project
        ).update(
            is_base_language=Case(
                When(pk=self.pk, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        self.refresh_from_db(fields=["is_base_language"])

    def __repr__(self):
        return (
            f"<ProjectLanguage id={self.pk} "
            f"project={self.project_id} "
            f"language={self.language} "
            f"base={self.is_base_language}>"
        )

    def __str__(self):
        return f"[{self.project.slug}] {self.get_language_display()}"
