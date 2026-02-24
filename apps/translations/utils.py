from django.db import transaction

from apps.core.exceptions import TranslationError
from apps.projects.models import ProjectLanguage
from apps.translations.models import TranslationKey, TranslationValue


def translation_key_create(*, project, key, description=""):
    """
    Create a new translation key for a project.

    Args:
        project: Project — project the key belongs to.
        key: str — dot/underscore-separated key identifier (auto-lowercased).
        description: str — optional human-readable description.

    Returns:
        TranslationKey — persisted instance.

    Raises:
        django.core.exceptions.ValidationError — if key format is invalid
            or (key, project) pair already exists.
    """
    key = key.lower()

    translation_key = TranslationKey(
        project=project,
        key=key,
        description=description,
    )
    translation_key.full_clean()
    translation_key.save()
    return translation_key


def translation_key_update(*, translation_key, key=None, description=None):
    """
    Partially update an existing translation key.

    Only the provided (non-None) fields are updated.

    Args:
        translation_key: TranslationKey — instance to update.
        key: str | None — new key value (auto-lowercased).
        description: str | None — new description.

    Returns:
        TranslationKey — updated instance.

    Raises:
        django.core.exceptions.ValidationError — if new key format is invalid
            or uniqueness constraint is violated.
    """
    update_fields = []

    if key is not None:
        translation_key.key = key.lower()
        update_fields.append("key")

    if description is not None:
        translation_key.description = description
        update_fields.append("description")

    if not update_fields:
        return translation_key

    translation_key.full_clean()
    translation_key.save(update_fields=[*update_fields, "updated_at"])
    return translation_key


def translation_key_delete(*, translation_key):
    """
    Delete a translation key and all its related translation values (CASCADE).

    Args:
        translation_key: TranslationKey — instance to delete.
    """
    translation_key.delete()


def _validate_language_belongs_to_project(*, translation_key, language):
    """
    Assert that a language is configured for the translation key's project.


    Raises:
        TranslationError — if the language is not in the project's language set.
    """
    exists = ProjectLanguage.objects.filter(
        project=translation_key.project,
        language=language,
    ).exists()

    if not exists:
        raise TranslationError(
            f"Language '{language}' is not configured for project "
            f"'{translation_key.project.slug}'.",
            extra={"language": language},
        )


def translation_value_create(*, translation_key, language, value):
    """
    Create a single translation value for a given key and language.

    Validates that the language is configured for the key's project
    before persisting.

    Args:
        translation_key: TranslationKey — parent key.
        language: str — language code (ISO 639-1).
        value: str — translated text.

    Returns:
        TranslationValue — persisted instance.

    Raises:
        TranslationError — if language is not configured for the project.
        django.core.exceptions.ValidationError — if uniqueness constraint
            (translation_key, language) is violated.
    """
    _validate_language_belongs_to_project(
        translation_key=translation_key,
        language=language,
    )

    translation_value = TranslationValue(
        translation_key=translation_key,
        language=language,
        value=value,
    )
    translation_value.full_clean()
    translation_value.save()
    return translation_value


def translation_value_update(*, translation_value, value):
    """
    Update the translated text of an existing translation value.

    Args:
        translation_value: TranslationValue — instance to update.
        value: str — new translated text.

    Returns:
        TranslationValue — updated instance.
    """
    translation_value.value = value
    translation_value.full_clean()
    translation_value.save(update_fields=["value", "updated_at"])
    return translation_value


def translation_value_delete(*, translation_value):
    """
    Delete a single translation value.

    Args:
        translation_value: TranslationValue — instance to delete.
    """
    translation_value.delete()


@transaction.atomic
def translation_value_bulk_update(*, translation_key, values_data):
    """
    Bulk create or update translation values for a given key.

    For each item in values_data: if a TranslationValue already exists for
    that (translation_key, language) — update it; otherwise — create a new one.

    Args:
        translation_key: TranslationKey — parent key.
        values_data: list[dict] — items with keys:
            "language" (str) — language code (ISO 639-1),
            "value" (str) — translated text.

    Returns:
        dict — {"created": list[TranslationValue],
                 "updated": list[TranslationValue]}.

    Raises:
        TranslationError — if any language is not configured for the project.
    """
    languages = [item["language"] for item in values_data]

    project_languages = set(
        ProjectLanguage.objects
        .filter(project=translation_key.project, language__in=languages)
        .values_list("language", flat=True)
    )

    invalid_languages = set(languages) - project_languages
    if invalid_languages:
        raise TranslationError(
            "Some languages are not configured for this project.",
            extra={"invalid_languages": sorted(invalid_languages)},
        )

    existing = {
        tv.language: tv
        for tv in TranslationValue.objects.filter(
            translation_key=translation_key,
            language__in=languages,
        )
    }

    to_create = []
    to_update = []

    for item in values_data:
        language = item["language"]
        value = item["value"]

        if language in existing:
            tv = existing[language]
            tv.value = value
            to_update.append(tv)
        else:
            to_create.append(TranslationValue(
                translation_key=translation_key,
                language=language,
                value=value,
            ))

    created = []
    if to_create:
        created = TranslationValue.objects.bulk_create(to_create)

    if to_update:
        TranslationValue.objects.bulk_update(
            to_update,
            ["value", "updated_at"]
        )

    return {"created": created, "updated": to_update}


@transaction.atomic
def translation_key_create_with_values(
        *,
        project,
        key,
        description="",
        values_data
):
    """
    Create a translation key and its values in a single transaction.

    Delegates key creation to translation_key_create and values to
    translation_value_bulk_update.

    Args:
        project: Project — project the key belongs to.
        key: str — dot/underscore-separated key identifier (auto-lowercased).
        description: str — optional human-readable description.
        values_data: list[dict] — items with keys:
            "language" (str) — language code (ISO 639-1),
            "value" (str) — translated text.

    Returns:
        dict — {"translation_key": TranslationKey,
                 "values": list[TranslationValue]}.

    Raises:
        django.core.exceptions.ValidationError — if key format is invalid.
        TranslationError — if any language is not configured for the project.
    """
    translation_key = translation_key_create(
        project=project,
        key=key,
        description=description,
    )

    result = {"translation_key": translation_key, "values": []}

    if values_data:
        bulk_result = translation_value_bulk_update(
            translation_key=translation_key,
            values_data=values_data,
        )
        result["values"] = bulk_result["created"]

    return result


def translation_key_bulk_create(*, project, keys_data):
    """
    Bulk create multiple translation keys (optionally with values) for a project.

    Intended for import scenarios (e.g. uploading a JSON/YAML file with
    all keys and translations at once).

    Args:
        project: Project — target project.
        keys_data: list[dict] — items with keys:
            "key" (str) — key identifier,
            "description" (str, optional) — human-readable description,
            "values" (list[dict], optional) — each with
                "language" (str) and "value" (str).

    Returns:
        Not yet implemented.

    Raises:
        NotImplementedError — always; reserved for the import feature.
    """
    raise NotImplementedError(
        "translation_key_bulk_create is reserved for the import feature."
    )
