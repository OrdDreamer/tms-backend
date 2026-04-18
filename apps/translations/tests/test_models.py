import pytest
from django.core.exceptions import ValidationError

from apps.factories import (
    ProjectFactory,
    TranslationKeyFactory,
    TranslationValueFactory,
)
from apps.translations.models import TranslationKey, TranslationValue


@pytest.mark.django_db
class TestTranslationKeyModel:
    @pytest.mark.parametrize(
        "key",
        [
            "common.hello",
            "api.v1.endpoint",
            "form.submit_button",
            "a.b",
            "section1.key2",
        ],
    )
    def test_valid_keys(self, key):
        project = ProjectFactory()
        tk = TranslationKey(project=project, key=key)
        tk.full_clean()  # should not raise

    @pytest.mark.parametrize(
        "key",
        [
            "UPPER.CASE",
            "has spaces",
            ".leading.dot",
            "trailing.dot.",
            "special!char",
            "",
        ],
    )
    def test_invalid_keys(self, key):
        project = ProjectFactory()
        tk = TranslationKey(project=project, key=key)
        with pytest.raises(ValidationError):
            tk.full_clean()

    def test_clean_lowercases_key(self):
        project = ProjectFactory()
        tk = TranslationKey(project=project, key="COMMON.HELLO")
        tk.clean()
        assert tk.key == "common.hello"

    def test_unique_key_per_project(self):
        project = ProjectFactory()
        TranslationKeyFactory(project=project, key="common.hello")
        dup = TranslationKey(project=project, key="common.hello")
        with pytest.raises(ValidationError):
            dup.full_clean()

    def test_same_key_different_projects(self):
        p1 = ProjectFactory()
        p2 = ProjectFactory()
        TranslationKeyFactory(project=p1, key="common.hello")
        TranslationKeyFactory(project=p2, key="common.hello")
        assert TranslationKey.objects.filter(key="common.hello").count() == 2


@pytest.mark.django_db
class TestTranslationValueModel:
    def test_unique_per_language(self):
        tk = TranslationKeyFactory()
        TranslationValueFactory(translation_key=tk, language="en")
        dup = TranslationValue(translation_key=tk, language="en", value="dup")
        with pytest.raises(ValidationError):
            dup.full_clean()

    def test_str(self):
        tv = TranslationValueFactory(language="en")
        assert "[en]" in str(tv)
