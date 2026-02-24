from django.db import transaction

from apps.core.exceptions import ProjectError
from apps.projects.models import Project, ProjectLanguage


def project_create(*, slug, name, description=""):
    """
    Create a new project.

    Args:
        slug: str — unique URL-friendly identifier.
        name: str — human-readable project name.
        description: str — optional project description.

    Returns:
        Project — persisted instance.

    Raises:
        django.core.exceptions.ValidationError — if slug format is invalid
            or uniqueness constraint is violated.
    """
    project = Project(slug=slug, name=name, description=description)
    project.full_clean()
    project.save()
    return project


def project_delete(*, project):
    """
    Delete a project and all related data
    (languages, keys, values via CASCADE).

    Args:
        project: Project — instance to delete.
    """
    project.delete()


def project_update(*, project, slug=None, name=None, description=None):
    """
    Partially update an existing project.

    Only the provided (non-None) fields are updated.

    Args:
        project: Project — instance to update.
        slug: str | None — new slug value.
        name: str | None — new project name.
        description: str | None — new description.

    Returns:
        Project — updated instance.

    Raises:
        django.core.exceptions.ValidationError — if slug format is invalid
            or uniqueness constraint is violated.
    """
    update_fields = []

    if slug is not None:
        project.slug = slug
        update_fields.append("slug")

    if name is not None:
        project.name = name
        update_fields.append("name")

    if description is not None:
        project.description = description
        update_fields.append("description")

    if not update_fields:
        return project

    project.full_clean()
    project.save(update_fields=[*update_fields, "updated_at"])
    return project


@transaction.atomic
def project_language_add(*, project, language, is_base_language=False):
    """
    Add a language to a project.

    If the project has no languages yet, the new language is automatically
    set as base regardless of the is_base_language flag. If is_base_language
    is True, any existing base language is demoted.

    Args:
        project: Project — target project.
        language: str — language code (ISO 639-1).
        is_base_language: bool — whether to mark as the base language.

    Returns:
        ProjectLanguage — persisted instance.

    Raises:
        django.core.exceptions.ValidationError — if (project, language)
            pair already exists.
    """
    has_languages = ProjectLanguage.objects.filter(project=project).exists()

    if not has_languages:
        is_base_language = True

    if is_base_language:
        ProjectLanguage.objects.select_for_update().filter(
            project=project,
            is_base_language=True,
        ).update(is_base_language=False)

    project_language = ProjectLanguage(
        project=project,
        language=language,
        is_base_language=is_base_language,
    )
    project_language.full_clean()
    project_language.save()
    return project_language


@transaction.atomic
def project_language_remove(*, project_language):
    """
    Remove a language from a project.

    Cannot remove the base language or the last remaining language.

    Args:
        project_language: ProjectLanguage — instance to remove.

    Raises:
        ProjectError — if the language is the base language or the last one
            in the project.
    """
    if project_language.is_base_language:
        raise ProjectError(
            "Cannot delete the base language. "
            "First set another language as base."
        )

    languages = ProjectLanguage.objects.select_for_update().filter(
        project=project_language.project
    )
    if not languages.exclude(pk=project_language.pk).exists():
        raise ProjectError(
            "Cannot delete the last language of a project."
        )

    project_language.delete()


@transaction.atomic
def project_language_set_base(*, project_language):
    """
    Set a language as the base language for its project.

    Demotes the current base language (if any) and promotes the given one.
    No-op if the language is already the base.

    Args:
        project_language: ProjectLanguage — instance to promote.

    Returns:
        ProjectLanguage — refreshed instance with is_base_language=True.
    """
    if project_language.is_base_language:
        return project_language

    project_languages = (
        ProjectLanguage.objects
        .select_for_update()
        .filter(project=project_language.project)
    )

    project_languages.filter(
        is_base_language=True,
    ).update(is_base_language=False)

    project_languages.filter(
        pk=project_language.pk,
    ).update(is_base_language=True)

    project_language.refresh_from_db(fields=["is_base_language"])
    return project_language


@transaction.atomic
def project_language_bulk_add(*, project, languages_data):
    """
    Add multiple languages to a project at once.

    If the project has no languages yet and none of the entries is marked
    as base, the first entry is automatically promoted. At most one entry
    may have is_base_language=True.

    Args:
        project: Project — target project.
        languages_data: list[dict] — items with keys:
            "language" (str) — language code (ISO 639-1),
            "is_base_language" (bool, optional) — base flag, defaults to False.

    Returns:
        list[ProjectLanguage] — created instances.

    Raises:
        ProjectError — if more than one entry has is_base_language=True.
        django.core.exceptions.ValidationError — if any (project, language)
            pair already exists.
    """
    base_entries = [
        item
        for item in languages_data
        if item.get("is_base_language")
    ]
    if len(base_entries) > 1:
        raise ProjectError("Only one language can be set as base.")

    has_languages = ProjectLanguage.objects.filter(project=project).exists()
    has_new_base = len(base_entries) == 1

    if not has_languages and not has_new_base:
        languages_data[0]["is_base_language"] = True
        has_new_base = True

    if has_new_base:
        ProjectLanguage.objects.select_for_update().filter(
            project=project,
            is_base_language=True,
        ).update(is_base_language=False)

    created = []
    for item in languages_data:
        pl = ProjectLanguage(
            project=project,
            language=item["language"],
            is_base_language=item.get("is_base_language", False),
        )
        pl.full_clean()
        pl.save()
        created.append(pl)

    return created
