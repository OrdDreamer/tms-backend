from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


def _translations_dict(translation_key, project_languages=None):
    existing = {tv.language: tv.value for tv in translation_key.values.all()}
    if project_languages is not None:
        return {lang: existing.get(lang, "") for lang in project_languages}
    return existing


# ----------------------
# Translation Key
# ----------------------

class TranslationKeyListFilterSerializer(serializers.Serializer):
    search = serializers.CharField(required=False)
    lang = serializers.CharField(required=False)
    untranslated = serializers.BooleanField(required=False, default=False)


class TranslationKeyCreateInputSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=255)
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        default=""
    )
    translations = serializers.DictField(
        child=serializers.CharField(allow_blank=True),
        required=False,
        default=dict,
    )


class TranslationKeyUpdateInputSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False)


class TranslationKeyListOutputSerializer(serializers.Serializer):
    id = serializers.UUIDField()  # noqa: VNE003
    key = serializers.CharField()
    description = serializers.CharField()
    translations = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    @extend_schema_field(serializers.DictField(child=serializers.CharField()))
    def get_translations(self, obj):
        return _translations_dict(obj, self.context.get("project_languages"))


class TranslationKeyDetailOutputSerializer(serializers.Serializer):
    id = serializers.UUIDField()  # noqa: VNE003
    key = serializers.CharField()
    description = serializers.CharField()
    translations = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    @extend_schema_field(serializers.DictField(child=serializers.CharField()))
    def get_translations(self, obj):
        return _translations_dict(obj, self.context.get("project_languages"))


class TranslationKeyBulkDeleteInputSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
    )


# ----------------------
# Translation Value
# ----------------------

class TranslationValueOutputSerializer(serializers.Serializer):
    language = serializers.CharField()
    value = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class TranslationValueCreateInputSerializer(serializers.Serializer):
    value = serializers.CharField(allow_blank=True)


class TranslationBulkUpdateInputSerializer(serializers.Serializer):
    translations = serializers.DictField(
        child=serializers.CharField(allow_blank=True),
    )


class TranslationKeyBulkDeleteOutputSerializer(serializers.Serializer):
    deleted_count = serializers.IntegerField()
