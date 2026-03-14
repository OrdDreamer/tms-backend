from rest_framework import serializers

from apps.core.choices import LanguageChoices

# ----------------------
# Project Language
# ----------------------


class ProjectLanguageCreateInputSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=LanguageChoices.choices)
    is_base_language = serializers.BooleanField(default=False)


class ProjectLanguageUpdateInputSerializer(serializers.Serializer):
    is_base_language = serializers.BooleanField(required=False)


class ProjectLanguageListOutputSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    language = serializers.CharField()
    is_base_language = serializers.BooleanField()
    created_at = serializers.DateTimeField()


# ----------------------
# Project
# ----------------------


class ProjectCreateInputSerializer(serializers.Serializer):
    slug = serializers.SlugField(max_length=100)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, default="")


class ProjectUpdateInputSerializer(serializers.Serializer):
    slug = serializers.SlugField(max_length=100, required=False)
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False)


class ProjectListOutputSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    slug = serializers.SlugField()
    name = serializers.CharField()
    description = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class ProjectDetailOutputSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    slug = serializers.SlugField()
    name = serializers.CharField()
    description = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    languages = ProjectLanguageListOutputSerializer(many=True)


# ----------------------
# Export
# ----------------------


class ProjectExportFilterSerializer(serializers.Serializer):
    lang = serializers.ChoiceField(
        choices=LanguageChoices.choices,
        required=False,
    )
    export_format = serializers.ChoiceField(
        choices=[("flat", "Flat"), ("nested", "Nested")],
        default="flat",
        required=False,
    )
