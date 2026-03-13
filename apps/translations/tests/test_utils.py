import pytest

from apps.core.exceptions import TranslationError
from apps.factories import (
    TranslationValueFactory,
)
from apps.translations.models import TranslationKey, TranslationValue
from apps.translations.utils import (
    project_translations_export,
    translation_key_bulk_delete,
    translation_key_create,
    translation_key_create_with_values,
    translation_key_delete,
    translation_key_update,
    translation_value_bulk_update,
    translation_value_create,
    translation_value_delete,
    translation_value_update,
)


@pytest.mark.django_db
class TestTranslationKeyCreate:
    def test_creates_key(self, project_with_langs):
        tk = translation_key_create(project=project_with_langs, key="common.hello")
        assert tk.key == "common.hello"
        assert tk.project == project_with_langs

    def test_auto_lowercases(self, project_with_langs):
        tk = translation_key_create(project=project_with_langs, key="COMMON.HELLO")
        assert tk.key == "common.hello"

    def test_nesting_conflict_parent_exists(self, project_with_langs):
        translation_key_create(project=project_with_langs, key="menu.file")
        with pytest.raises(TranslationError, match="nested keys"):
            translation_key_create(project=project_with_langs, key="menu")

    def test_nesting_conflict_child_exists(self, project_with_langs):
        translation_key_create(project=project_with_langs, key="menu")
        with pytest.raises(TranslationError, match="parent key"):
            translation_key_create(project=project_with_langs, key="menu.file")

    def test_sibling_keys_ok(self, project_with_langs):
        translation_key_create(project=project_with_langs, key="menu.file")
        tk = translation_key_create(project=project_with_langs, key="menu.edit")
        assert tk.key == "menu.edit"

    def test_with_description(self, project_with_langs):
        tk = translation_key_create(
            project=project_with_langs, key="common.hello", description="Greeting",
        )
        assert tk.description == "Greeting"


@pytest.mark.django_db
class TestTranslationKeyUpdate:
    def test_update_key(self, translation_key):
        updated = translation_key_update(
            translation_key=translation_key, key="common.goodbye",
        )
        assert updated.key == "common.goodbye"

    def test_update_description(self, translation_key):
        updated = translation_key_update(
            translation_key=translation_key, description="Updated desc",
        )
        assert updated.description == "Updated desc"

    def test_no_fields_noop(self, translation_key):
        result = translation_key_update(translation_key=translation_key)
        assert result == translation_key

    def test_rename_no_self_conflict(self, project_with_langs):
        tk = translation_key_create(project=project_with_langs, key="menu.item")
        updated = translation_key_update(translation_key=tk, key="menu.item2")
        assert updated.key == "menu.item2"


@pytest.mark.django_db
class TestTranslationKeyDelete:
    def test_deletes_key(self, translation_key):
        pk = translation_key.pk
        translation_key_delete(translation_key=translation_key)
        assert not TranslationKey.objects.filter(pk=pk).exists()

    def test_cascade_deletes_values(self, translation_key):
        TranslationValueFactory(
            translation_key=translation_key, language="en", value="Hello",
        )
        translation_key_delete(translation_key=translation_key)
        assert not TranslationValue.objects.filter(
            translation_key_id=translation_key.pk,
        ).exists()


@pytest.mark.django_db
class TestTranslationValueCreate:
    def test_creates_value(self, translation_key):
        tv = translation_value_create(
            translation_key=translation_key, language="en", value="Hello",
        )
        assert tv.value == "Hello"
        assert tv.language == "en"

    def test_invalid_language_raises(self, translation_key):
        with pytest.raises(TranslationError, match="not configured"):
            translation_value_create(
                translation_key=translation_key, language="de", value="Hallo",
            )


@pytest.mark.django_db
class TestTranslationValueUpdate:
    def test_updates_value(self, translation_key):
        tv = TranslationValueFactory(
            translation_key=translation_key, language="en", value="Hello",
        )
        result = translation_value_update(translation_value=tv, value="Hi")
        assert result.value == "Hi"

    def test_empty_value_deletes(self, translation_key):
        tv = TranslationValueFactory(
            translation_key=translation_key, language="en", value="Hello",
        )
        result = translation_value_update(translation_value=tv, value="")
        assert result is None
        assert not TranslationValue.objects.filter(pk=tv.pk).exists()


@pytest.mark.django_db
class TestTranslationValueDelete:
    def test_deletes_value(self, translation_key):
        tv = TranslationValueFactory(
            translation_key=translation_key, language="en", value="Hello",
        )
        translation_value_delete(translation_value=tv)
        assert not TranslationValue.objects.filter(pk=tv.pk).exists()


@pytest.mark.django_db
class TestTranslationValueBulkUpdate:
    def test_creates_new(self, translation_key):
        result = translation_value_bulk_update(
            translation_key=translation_key,
            values_data=[{"language": "en", "value": "Hello"}],
        )
        assert len(result["created"]) == 1
        assert result["deleted_count"] == 0

    def test_updates_existing(self, translation_key):
        TranslationValueFactory(
            translation_key=translation_key, language="en", value="Old",
        )
        result = translation_value_bulk_update(
            translation_key=translation_key,
            values_data=[{"language": "en", "value": "New"}],
        )
        assert len(result["updated"]) == 1

    def test_deletes_on_empty_value(self, translation_key):
        TranslationValueFactory(
            translation_key=translation_key, language="en", value="Hello",
        )
        result = translation_value_bulk_update(
            translation_key=translation_key,
            values_data=[{"language": "en", "value": ""}],
        )
        assert result["deleted_count"] == 1

    def test_skips_empty_new(self, translation_key):
        result = translation_value_bulk_update(
            translation_key=translation_key,
            values_data=[{"language": "en", "value": ""}],
        )
        assert len(result["created"]) == 0
        assert result["deleted_count"] == 0

    def test_invalid_language_raises(self, translation_key):
        with pytest.raises(TranslationError, match="not configured"):
            translation_value_bulk_update(
                translation_key=translation_key,
                values_data=[{"language": "de", "value": "Hallo"}],
            )

    def test_mixed_operations(self, translation_key):
        TranslationValueFactory(
            translation_key=translation_key, language="en", value="Old EN",
        )
        result = translation_value_bulk_update(
            translation_key=translation_key,
            values_data=[
                {"language": "en", "value": "New EN"},
                {"language": "uk", "value": "Привіт"},
            ],
        )
        assert len(result["created"]) == 1
        assert len(result["updated"]) == 1


@pytest.mark.django_db
class TestTranslationKeyCreateWithValues:
    def test_creates_key_and_values(self, project_with_langs):
        result = translation_key_create_with_values(
            project=project_with_langs,
            key="common.hello",
            values_data=[
                {"language": "en", "value": "Hello"},
                {"language": "uk", "value": "Привіт"},
            ],
        )
        assert result["translation_key"].key == "common.hello"
        assert len(result["values"]) == 2

    def test_creates_key_without_values(self, project_with_langs):
        result = translation_key_create_with_values(
            project=project_with_langs,
            key="common.hello",
            values_data=[],
        )
        assert result["translation_key"].key == "common.hello"
        assert len(result["values"]) == 0


@pytest.mark.django_db
class TestTranslationKeyBulkDelete:
    def test_deletes_multiple(self, project_with_langs):
        translation_key_create(project=project_with_langs, key="a.one")
        translation_key_create(project=project_with_langs, key="a.two")
        translation_key_create(project=project_with_langs, key="a.three")
        count = translation_key_bulk_delete(
            project=project_with_langs, key_names=["a.one", "a.two"],
        )
        assert count == 2
        assert TranslationKey.objects.filter(project=project_with_langs).count() == 1

    def test_ignores_nonexistent(self, project_with_langs):
        count = translation_key_bulk_delete(
            project=project_with_langs, key_names=["nonexistent.key"],
        )
        assert count == 0


@pytest.mark.django_db
class TestProjectTranslationsExport:
    def _setup_data(self, project):
        tk = translation_key_create(project=project, key="common.hello")
        translation_value_create(translation_key=tk, language="en", value="Hello")
        translation_value_create(translation_key=tk, language="uk", value="Привіт")
        return tk

    def test_export_flat_all_languages(self, project_with_langs):
        self._setup_data(project_with_langs)
        result = project_translations_export(project=project_with_langs)
        assert "en" in result
        assert "uk" in result
        assert result["en"]["common.hello"] == "Hello"
        assert result["uk"]["common.hello"] == "Привіт"

    def test_export_flat_single_language(self, project_with_langs):
        self._setup_data(project_with_langs)
        result = project_translations_export(
            project=project_with_langs, language="en",
        )
        assert result["common.hello"] == "Hello"

    def test_export_nested(self, project_with_langs):
        self._setup_data(project_with_langs)
        result = project_translations_export(
            project=project_with_langs, export_format="nested",
        )
        assert result["en"]["common"]["hello"] == "Hello"

    def test_missing_translations_empty_string(self, project_with_langs):
        tk = translation_key_create(project=project_with_langs, key="common.bye")
        translation_value_create(translation_key=tk, language="en", value="Bye")
        result = project_translations_export(project=project_with_langs)
        assert result["uk"]["common.bye"] == ""

    def test_invalid_language_raises(self, project_with_langs):
        with pytest.raises(TranslationError, match="not configured"):
            project_translations_export(
                project=project_with_langs, language="de",
            )
