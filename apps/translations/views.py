from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Project, ProjectLanguage
from apps.translations.models import TranslationKey, TranslationValue
from apps.translations.serializers import (
    TranslationBulkUpdateInputSerializer,
    TranslationKeyBulkDeleteInputSerializer,
    TranslationKeyCreateInputSerializer,
    TranslationKeyDetailOutputSerializer,
    TranslationKeyListFilterSerializer,
    TranslationKeyListOutputSerializer,
    TranslationKeyUpdateInputSerializer,
    TranslationValueCreateInputSerializer,
    TranslationValueOutputSerializer,
)
from apps.translations.utils import (
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


def _get_project(project_id):
    return get_object_or_404(Project, id=project_id)


def _get_translation_key(project_id, key_id):
    return get_object_or_404(
        TranslationKey, id=key_id, project_id=project_id,
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

    def get(self, request, project_id):
        project = _get_project(project_id)
        project_languages = _get_project_languages(project)

        filters = TranslationKeyListFilterSerializer(
            data=request.query_params,
        )
        filters.is_valid(raise_exception=True)

        qs = TranslationKey.objects.filter(
            project=project,
        ).prefetch_related("values")

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
            context={"project_languages": project_languages},
        )
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, project_id):
        project = _get_project(project_id)
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
    def get(self, request, project_id, key_id):
        tk = _get_translation_key(project_id, key_id)
        project_languages = _get_project_languages(tk.project)

        output = TranslationKeyDetailOutputSerializer(
            tk, context={"project_languages": project_languages},
        )
        return Response(output.data)

    def patch(self, request, project_id, key_id):
        tk = _get_translation_key(project_id, key_id)
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

    def delete(self, request, project_id, key_id):
        tk = _get_translation_key(project_id, key_id)
        translation_key_delete(translation_key=tk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TranslationKeyBulkDeleteAPIView(APIView):
    def post(self, request, project_id):
        project = _get_project(project_id)

        serializer = TranslationKeyBulkDeleteInputSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        deleted_count = translation_key_bulk_delete(
            project=project, key_ids=serializer.validated_data["ids"],
        )
        return Response(
            {"deleted_count": deleted_count},
            status=status.HTTP_200_OK,
        )


class TranslationListAPIView(APIView):
    """
    GET  — list all translations for a key.
    PATCH — batch create/update translations for a key.
    """

    def get(self, request, project_id, key_id):
        tk = _get_translation_key(project_id, key_id)

        values = TranslationValue.objects.filter(translation_key=tk)
        serializer = TranslationValueOutputSerializer(values, many=True)
        return Response(serializer.data)

    def patch(self, request, project_id, key_id):
        tk = _get_translation_key(project_id, key_id)
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
    """
    PUT    — idempotent create-or-replace a single translation.
    DELETE — remove a single translation.
    """

    def put(self, request, project_id, key_id, lang_code):
        tk = _get_translation_key(project_id, key_id)

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
            output = TranslationValueOutputSerializer(tv)
            return Response(output.data)

        tv = translation_value_create(
            translation_key=tk,
            language=lang_code,
            value=serializer.validated_data["value"],
        )
        output = TranslationValueOutputSerializer(tv)
        return Response(output.data, status=status.HTTP_201_CREATED)

    def delete(self, request, project_id, key_id, lang_code):
        tv = get_object_or_404(
            TranslationValue,
            translation_key_id=key_id,
            translation_key__project_id=project_id,
            language=lang_code,
        )
        translation_value_delete(translation_value=tv)
        return Response(status=status.HTTP_204_NO_CONTENT)
