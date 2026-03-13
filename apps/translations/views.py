import hashlib

from django.db.models import Count, Max, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.projects.models import Project, ProjectLanguage
from apps.projects.serializers import ProjectExportFilterSerializer
from apps.translations.models import TranslationKey, TranslationValue
from apps.translations.serializers import (
    TranslationBulkUpdateInputSerializer,
    TranslationKeyBulkDeleteInputSerializer,
    TranslationKeyBulkDeleteOutputSerializer,
    TranslationKeyCreateInputSerializer,
    TranslationKeyDetailOutputSerializer,
    TranslationKeyListFilterSerializer,
    TranslationKeyListOutputSerializer,
    TranslationKeyUpdateInputSerializer,
    TranslationValueCreateInputSerializer,
    TranslationValueOutputSerializer,
)
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


def _get_project(project_slug):
    return get_object_or_404(Project, slug=project_slug)


def _get_translation_key(project_slug, key_name):
    return get_object_or_404(
        TranslationKey, key=key_name, project__slug=project_slug,
    )


def _get_project_languages(project):
    return set(
        ProjectLanguage.objects
        .filter(project=project)
        .values_list("language", flat=True)
    )


def _filter_translations_by_project_languages(translations, project_languages):
    return {k: v for k, v in translations.items() if k in project_languages}


class TranslationKeyListCreateAPIView(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 20
        max_limit = 100

    pagination_class = Pagination

    @extend_schema(
        summary="List translation keys",
        parameters=[
            OpenApiParameter(
                name="search",
                description="Filter by key name",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="lang",
                description="Filter by language code",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="untranslated",
                description=(
                    "Return only keys without a translation for the given lang"
                ),
                required=False,
                type=bool,
            ),
            OpenApiParameter(
                name="include_translations",
                description=(
                    "Include translations in the response (default true)"
                ),
                required=False,
                type=bool,
            ),
        ],
        responses=TranslationKeyListOutputSerializer(many=True),
        tags=["Translation Keys"],
    )
    def get(self, request, project_slug):
        project = _get_project(project_slug)
        project_languages = _get_project_languages(project)

        filters = TranslationKeyListFilterSerializer(
            data=request.query_params,
        )
        filters.is_valid(raise_exception=True)

        include_translations = filters.validated_data.get(
            "include_translations", True,
        )

        qs = TranslationKey.objects.filter(project=project)
        if include_translations:
            qs = qs.prefetch_related("values")

        search = filters.validated_data.get("search")
        if search:
            qs = qs.filter(key__icontains=search)

        lang = filters.validated_data.get("lang")
        untranslated = filters.validated_data.get("untranslated", False)

        if lang and untranslated:
            qs = qs.annotate(
                lang_count=Count(
                    "values", filter=Q(values__language=lang),
                ),
            ).filter(lang_count=0)
        elif lang:
            qs = qs.filter(values__language=lang).distinct()

        paginator = self.Pagination()
        page = paginator.paginate_queryset(qs, request)

        serializer = TranslationKeyListOutputSerializer(
            page, many=True,
            context={
                "project_languages": project_languages,
                "include_translations": include_translations,
            },
        )
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        summary="Create a translation key",
        request=TranslationKeyCreateInputSerializer,
        responses={201: TranslationKeyDetailOutputSerializer},
        tags=["Translation Keys"],
    )
    def post(self, request, project_slug):
        project = _get_project(project_slug)
        project_languages = _get_project_languages(project)

        serializer = TranslationKeyCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        translations = _filter_translations_by_project_languages(
            serializer.validated_data.pop("translations", {}),
            project_languages,
        )

        if translations:
            values_data = [
                {"language": lang, "value": val}
                for lang, val in translations.items()
            ]
            result = translation_key_create_with_values(
                project=project,
                values_data=values_data,
                **serializer.validated_data,
            )
            tk = result["translation_key"]
        else:
            tk = translation_key_create(
                project=project, **serializer.validated_data,
            )

        output = TranslationKeyDetailOutputSerializer(
            tk, context={"project_languages": project_languages},
        )
        return Response(output.data, status=status.HTTP_201_CREATED)


class TranslationKeyDetailAPIView(APIView):
    @extend_schema(
        summary="Retrieve a translation key",
        responses=TranslationKeyDetailOutputSerializer,
        tags=["Translation Keys"],
    )
    def get(self, request, project_slug, key_name):
        tk = _get_translation_key(project_slug, key_name)
        project_languages = _get_project_languages(tk.project)

        output = TranslationKeyDetailOutputSerializer(
            tk, context={"project_languages": project_languages},
        )
        return Response(output.data)

    @extend_schema(
        summary="Update a translation key",
        request=TranslationKeyUpdateInputSerializer,
        responses=TranslationKeyDetailOutputSerializer,
        tags=["Translation Keys"],
    )
    def patch(self, request, project_slug, key_name):
        tk = _get_translation_key(project_slug, key_name)
        project_languages = _get_project_languages(tk.project)

        serializer = TranslationKeyUpdateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tk = translation_key_update(
            translation_key=tk, **serializer.validated_data,
        )

        output = TranslationKeyDetailOutputSerializer(
            tk, context={"project_languages": project_languages},
        )
        return Response(output.data)

    @extend_schema(
        summary="Delete a translation key",
        responses={204: None},
        tags=["Translation Keys"],
    )
    def delete(self, request, project_slug, key_name):
        tk = _get_translation_key(project_slug, key_name)
        translation_key_delete(translation_key=tk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TranslationKeyBulkDeleteAPIView(APIView):
    @extend_schema(
        summary="Bulk delete translation keys",
        request=TranslationKeyBulkDeleteInputSerializer,
        responses=TranslationKeyBulkDeleteOutputSerializer,
        tags=["Translation Keys"],
    )
    def post(self, request, project_slug):
        project = _get_project(project_slug)

        serializer = TranslationKeyBulkDeleteInputSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        deleted_count = translation_key_bulk_delete(
            project=project, key_names=serializer.validated_data["keys"],
        )
        return Response(
            {"deleted_count": deleted_count},
            status=status.HTTP_200_OK,
        )


class TranslationListAPIView(APIView):
    @extend_schema(
        summary="List translations for a key",
        responses=TranslationValueOutputSerializer(many=True),
        tags=["Translations"],
    )
    def get(self, request, project_slug, key_name):
        tk = _get_translation_key(project_slug, key_name)

        values = TranslationValue.objects.filter(translation_key=tk)
        serializer = TranslationValueOutputSerializer(values, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Batch create/update translations for a key",
        request=TranslationBulkUpdateInputSerializer,
        responses=TranslationValueOutputSerializer(many=True),
        tags=["Translations"],
    )
    def patch(self, request, project_slug, key_name):
        tk = _get_translation_key(project_slug, key_name)
        project_languages = _get_project_languages(tk.project)

        serializer = TranslationBulkUpdateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        translations = _filter_translations_by_project_languages(
            serializer.validated_data["translations"],
            project_languages,
        )

        values_data = [
            {"language": lang, "value": val}
            for lang, val in translations.items()
        ]

        result = translation_value_bulk_update(
            translation_key=tk, values_data=values_data,
        )

        all_values = result["created"] + result["updated"]
        output = TranslationValueOutputSerializer(all_values, many=True)
        return Response(output.data)


class TranslationDetailAPIView(APIView):
    @extend_schema(
        summary="Create or replace a single translation",
        request=TranslationValueCreateInputSerializer,
        responses=TranslationValueOutputSerializer,
        tags=["Translations"],
    )
    def put(self, request, project_slug, key_name, lang_code):
        tk = _get_translation_key(project_slug, key_name)

        serializer = TranslationValueCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        existing = TranslationValue.objects.filter(
            translation_key=tk, language=lang_code,
        ).first()

        if existing:
            tv = translation_value_update(
                translation_value=existing,
                value=serializer.validated_data["value"],
            )
            if tv is None:
                return Response(status=status.HTTP_204_NO_CONTENT)
            output = TranslationValueOutputSerializer(tv)
            return Response(output.data)

        value = serializer.validated_data["value"]
        if not value:
            return Response(status=status.HTTP_204_NO_CONTENT)

        tv = translation_value_create(
            translation_key=tk,
            language=lang_code,
            value=value,
        )
        output = TranslationValueOutputSerializer(tv)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Remove a single translation",
        responses={204: None},
        tags=["Translations"],
    )
    def delete(self, request, project_slug, key_name, lang_code):
        tv = get_object_or_404(
            TranslationValue,
            translation_key__key=key_name,
            translation_key__project__slug=project_slug,
            language=lang_code,
        )
        translation_value_delete(translation_value=tv)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublicProjectTranslationsAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "public_api"

    @extend_schema(
        summary="Public translations export",
        parameters=[
            OpenApiParameter(
                name="lang",
                description="Export a single language (ISO 639-1 code)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="export_format",
                description="Output structure: flat (default) or nested",
                required=False,
                type=str,
                enum=["flat", "nested"],
            ),
        ],
        responses={(200, "application/json"): OpenApiTypes.OBJECT},
        tags=["Public"],
    )
    def get(self, request, project_slug):
        project = get_object_or_404(
            Project.objects.prefetch_related("languages"),
            slug=project_slug,
        )

        serializer = ProjectExportFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        language = serializer.validated_data.get("lang")
        export_format = serializer.validated_data.get(
            "export_format", "flat",
        )

        etag = self._compute_etag(project, language, export_format)

        if request.META.get("HTTP_IF_NONE_MATCH") == etag:
            response = Response(status=status.HTTP_304_NOT_MODIFIED)
            response["ETag"] = etag
            response["Cache-Control"] = "public, max-age=60"
            return response

        data = project_translations_export(
            project=project,
            language=language,
            export_format=export_format,
        )

        response = Response(data)
        response["ETag"] = etag
        response["Cache-Control"] = "public, max-age=60"
        return response

    @staticmethod
    def _compute_etag(project, language, export_format):
        key_stats = TranslationKey.objects.filter(
            project=project,
        ).aggregate(latest=Max("updated_at"), total=Count("id"))

        value_qs = TranslationValue.objects.filter(
            translation_key__project=project,
        )
        if language:
            value_qs = value_qs.filter(language=language)
        value_stats = value_qs.aggregate(
            latest=Max("updated_at"), total=Count("id"),
        )

        lang_stats = ProjectLanguage.objects.filter(
            project=project,
        ).aggregate(latest=Max("updated_at"), total=Count("id"))

        timestamps = [
            ts for ts in [
                key_stats["latest"],
                value_stats["latest"],
                lang_stats["latest"],
            ]
            if ts is not None
        ]
        ts_str = max(timestamps).isoformat() if timestamps else "empty"

        raw = (
            f"{project.slug}: {language or "all"}: {export_format}"
            f": {ts_str}"
            f": {key_stats["total"]}: {value_stats["total"]}"
            f": {lang_stats["total"]}"
        )
        return f'"{hashlib.md5(raw.encode()).hexdigest()}"'
