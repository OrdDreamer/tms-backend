from apps.translations.serializers import (
    TranslationBulkUpdateInputSerializer,
    TranslationKeyBulkDeleteInputSerializer,
    TranslationKeyCreateInputSerializer,
    TranslationKeyListFilterSerializer,
    TranslationKeyUpdateInputSerializer,
    TranslationValueCreateInputSerializer,
)


class TestTranslationKeyCreateInputSerializer:
    def test_valid(self):
        s = TranslationKeyCreateInputSerializer(data={"key": "common.hello"})
        assert s.is_valid()

    def test_with_translations(self):
        s = TranslationKeyCreateInputSerializer(data={
            "key": "common.hello",
            "translations": {"en": "Hello", "uk": "Привіт"},
        })
        assert s.is_valid()
        assert "en" in s.validated_data["translations"]

    def test_key_required(self):
        s = TranslationKeyCreateInputSerializer(data={})
        assert not s.is_valid()
        assert "key" in s.errors


class TestTranslationKeyBulkDeleteInputSerializer:
    def test_valid(self):
        s = TranslationKeyBulkDeleteInputSerializer(data={"keys": ["a.b"]})
        assert s.is_valid()

    def test_empty_list_invalid(self):
        s = TranslationKeyBulkDeleteInputSerializer(data={"keys": []})
        assert not s.is_valid()


class TestTranslationBulkUpdateInputSerializer:
    def test_valid(self):
        s = TranslationBulkUpdateInputSerializer(
            data={"translations": {"en": "Hello"}},
        )
        assert s.is_valid()

    def test_allows_blank(self):
        s = TranslationBulkUpdateInputSerializer(
            data={"translations": {"en": ""}},
        )
        assert s.is_valid()


class TestTranslationValueCreateInputSerializer:
    def test_allows_blank(self):
        s = TranslationValueCreateInputSerializer(data={"value": ""})
        assert s.is_valid()


class TestTranslationKeyListFilterSerializer:
    def test_all_optional(self):
        s = TranslationKeyListFilterSerializer(data={})
        assert s.is_valid()
