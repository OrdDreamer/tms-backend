from django.db import transaction

from apps.core.exceptions import TranslationError
from apps.projects.models import ProjectLanguage
from apps.translations.models import TranslationKey, TranslationValue


def _validate_language_belongs_to_project(*, translation_key, language):
    """
    Assert that a language is configured for the translation key's project.


    Raises:
        TranslationError — if the language is not in the project's
        language set.
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


def _validate_key_no_nesting_conflict(*, project, key, exclude_id=None):
    """
    Ensure that a key does not conflict with existing keys in a
    parent-child relationship.

    For example, ``menu`` and ``menu.file`` cannot coexist because
    ``menu`` would be both a leaf value and a namespace for nested keys.

    ``exclude_id`` is needed when renaming a key — the old record is
    still in the DB and would falsely conflict with the new name
    (e.g. renaming ``menu`` to ``menu.key``).

    Raises:
        TranslationError — if the key conflicts with an existing
        parent or child key.
    """
    qs = TranslationKey.objects.filter(project=project)
    if exclude_id:
        qs = qs.exclude(id=exclude_id)

    parts = key.split(".")
    ancestor_keys = [".".join(parts[:i]) for i in range(1, len(parts))]
    if ancestor_keys:
        conflicts = list(qs.filter(key__in=ancestor_keys).values_list("key", flat=True))
        if conflicts:
            raise TranslationError(
                f"Key '{key}' conflicts with an existing parent key.",
                extra={"key": key, "conflicting_keys": conflicts},
            )

    conflicts = list(qs.filter(key__startswith=f"{key}.").values_list("key", flat=True))
    if conflicts:
        raise TranslationError(
            f"Key '{key}' conflicts with existing nested keys.",
            extra={"key": key, "conflicting_keys": conflicts},
        )


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
    _validate_key_no_nesting_conflict(project=project, key=key)

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
        _validate_key_no_nesting_conflict(
            project=translation_key.project,
            key=key.lower(),
            exclude_id=translation_key.id,
        )
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

    If value is empty, the record is deleted and None is returned.

    Args:
        translation_value: TranslationValue — instance to update.
        value: str — new translated text.

    Returns:
        TranslationValue | None — updated instance, or None if value
        was blank (record deleted).
    """
    if not value:
        translation_value.delete()
        return None

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
    Bulk create, update, or delete translation values for a given key.

    For each item in values_data:
    - Existing record + non-empty value → update.
    - Existing record + empty value → delete.
    - No record + non-empty value → create.
    - No record + empty value → skip.

    Args:
        translation_key: TranslationKey — parent key.
        values_data: list[dict] — items with keys:
            "language" (str) — language code (ISO 639-1),
            "value" (str) — translated text.

    Returns:
        dict — {"created": list[TranslationValue],
                 "updated": list[TranslationValue],
                 "deleted_count": int}.

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
    to_delete_ids = []

    for item in values_data:
        language = item["language"]
        value = item["value"]

        if language in existing:
            if value:
                tv = existing[language]
                tv.value = value
                to_update.append(tv)
            else:
                to_delete_ids.append(existing[language].id)
        else:
            if value:
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

    deleted_count = 0
    if to_delete_ids:
        deleted_count, _ = TranslationValue.objects.filter(
            id__in=to_delete_ids,
        ).delete()

    return {
        "created": created,
        "updated": to_update,
        "deleted_count": deleted_count,
    }


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


def translation_key_bulk_delete(*, project, key_names):
    """
    Delete multiple translation keys by name within a project.

    Only keys belonging to the given project are deleted; names not found
    are silently ignored.

    Args:
        project: Project — project the keys belong to.
        key_names: list[str] — key identifiers to delete.

    Returns:
        int — number of keys actually deleted.
    """
    deleted_count, _ = TranslationKey.objects.filter(
        project=project,
        key__in=key_names,
    ).delete()
    return deleted_count


def project_translations_export(*, project, language=None, export_format="flat"):
    """
    Export translations for a project.

    Builds a full matrix of all project keys x target languages.
    Missing translations are represented as empty strings.

    Args:
        project: Project — project to export.
        language: str | None — if set, export only this language.
        export_format: "flat" | "nested" — output structure.
            "flat": dot-separated keys as-is.
            "nested": dots in keys produce nested dicts.
            Key nesting conflicts (e.g. "menu" and "menu.file") are
            prevented by validation at creation time. As a fallback,
            if such a conflict exists, the leaf value is replaced by
            the nested dict.

    Returns:
        dict — when language is set, returns a single language mapping;
               otherwise, returns {lang_code: mapping} for every project language.

    Raises:
        TranslationError — if language is not configured for the project.
    """
    project_langs = list(
        project.languages.values_list("language", flat=True)
    )

    if language:
        if language not in project_langs:
            raise TranslationError(
                f"Language '{language}' is not configured for project "
                f"'{project.slug}'.",
                extra={"language": language},
            )
        target_langs = [language]
    else:
        target_langs = sorted(project_langs)

    all_keys = list(
        TranslationKey.objects
        .filter(project=project)
        .order_by("key")
        .values_list("key", flat=True)
    )

    existing = (
        TranslationValue.objects
        .filter(
            translation_key__project=project,
            language__in=target_langs,
        )
        .select_related("translation_key")
    )

    value_map = {}
    for tv in existing:
        value_map[(tv.language, tv.translation_key.key)] = tv.value

    def _build_flat(lang):
        return {key: value_map.get((lang, key), "") for key in all_keys}

    def _build_nested(lang):
        tree = {}
        for key in all_keys:
            parts = key.split(".")
            node = tree
            for part in parts[:-1]:
                if part not in node or not isinstance(node[part], dict):
                    node[part] = {}
                node = node[part]
            node[parts[-1]] = value_map.get((lang, key), "")
        return tree

    builder = _build_nested if export_format == "nested" else _build_flat

    if language:
        return builder(language)

    return {lang: builder(lang) for lang in target_langs}
