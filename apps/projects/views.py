from django.db.models import prefetch_related_objects
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Project, ProjectLanguage
from apps.projects.serializers import (
    ProjectCreateInputSerializer,
    ProjectDetailOutputSerializer,
    ProjectExportFilterSerializer,
    ProjectLanguageCreateInputSerializer,
    ProjectLanguageListOutputSerializer,
    ProjectLanguageUpdateInputSerializer,
    ProjectListOutputSerializer,
    ProjectUpdateInputSerializer,
)
from apps.projects.utils import (
    project_create,
    project_delete,
    project_language_add,
    project_language_remove,
    project_language_set_base,
    project_update,
)
from apps.translations.utils import project_translations_export


def _get_project(project_id, prefetch=None):
    qs = Project.objects.all()
    if prefetch:
        qs = qs.prefetch_related(*prefetch)
    return get_object_or_404(qs, id=project_id)


class ProjectListCreateAPIView(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 20
        max_limit = 100

    @extend_schema(
        summary="List projects",
        responses=ProjectListOutputSerializer(many=True),
        tags=["Projects"],
    )
    def get(self, request):
        projects = Project.objects.all()

        paginator = self.Pagination()
        page = paginator.paginate_queryset(projects, request)
        serializer = ProjectListOutputSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        summary="Create a project",
        request=ProjectCreateInputSerializer,
        responses={201: ProjectDetailOutputSerializer},
        tags=["Projects"],
    )
    def post(self, request):
        serializer = ProjectCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = project_create(**serializer.validated_data)
        prefetch_related_objects([project], "languages")

        output = ProjectDetailOutputSerializer(project)
        return Response(output.data, status=status.HTTP_201_CREATED)


class ProjectDetailAPIView(APIView):
    @extend_schema(
        summary="Retrieve a project",
        responses=ProjectDetailOutputSerializer,
        tags=["Projects"],
    )
    def get(self, request, project_id):
        project = _get_project(project_id, prefetch=["languages"])

        serializer = ProjectDetailOutputSerializer(project)
        return Response(serializer.data)

    @extend_schema(
        summary="Update a project",
        request=ProjectUpdateInputSerializer,
        responses=ProjectDetailOutputSerializer,
        tags=["Projects"],
    )
    def patch(self, request, project_id):
        project = _get_project(project_id, prefetch=["languages"])

        serializer = ProjectUpdateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = project_update(project=project, **serializer.validated_data)

        output = ProjectDetailOutputSerializer(project)
        return Response(output.data)

    @extend_schema(
        summary="Delete a project",
        responses={204: None},
        tags=["Projects"],
    )
    def delete(self, request, project_id):
        project = _get_project(project_id)
        project_delete(project=project)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectLanguageListCreateAPIView(APIView):
    @extend_schema(
        summary="List project languages",
        responses=ProjectLanguageListOutputSerializer(many=True),
        tags=["Project Languages"],
    )
    def get(self, request, project_id):
        project = _get_project(project_id)

        languages = ProjectLanguage.objects.filter(project=project)
        serializer = ProjectLanguageListOutputSerializer(languages, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Add a language to a project",
        request=ProjectLanguageCreateInputSerializer,
        responses={201: ProjectLanguageListOutputSerializer},
        tags=["Project Languages"],
    )
    def post(self, request, project_id):
        project = _get_project(project_id)

        serializer = ProjectLanguageCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project_language = project_language_add(
            project=project, **serializer.validated_data,
        )

        output = ProjectLanguageListOutputSerializer(project_language)
        return Response(output.data, status=status.HTTP_201_CREATED)


class ProjectLanguageDetailAPIView(APIView):
    @extend_schema(
        summary="Update a project language",
        request=ProjectLanguageUpdateInputSerializer,
        responses=ProjectLanguageListOutputSerializer,
        tags=["Project Languages"],
    )
    def patch(self, request, project_id, lang_code):
        project_language = get_object_or_404(
            ProjectLanguage,
            project_id=project_id,
            language=lang_code,
        )

        serializer = ProjectLanguageUpdateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data["is_base_language"]:
            project_language = project_language_set_base(
                project_language=project_language,
            )

        output = ProjectLanguageListOutputSerializer(project_language)
        return Response(output.data)

    @extend_schema(
        summary="Remove a project language",
        responses={204: None},
        tags=["Project Languages"],
    )
    def delete(self, request, project_id, lang_code):
        project_language = get_object_or_404(
            ProjectLanguage,
            project_id=project_id,
            language=lang_code,
        )
        project_language_remove(project_language=project_language)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectExportAPIView(APIView):
    @extend_schema(
        summary="Export project translations",
        responses={(200, "application/json"): OpenApiTypes.OBJECT},
        tags=["Projects"],
    )
    def get(self, request, project_id):
        project = _get_project(project_id)

        serializer = ProjectExportFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        language = serializer.validated_data.get("lang")
        data = project_translations_export(
            project=project, language=language,
        )
        return Response(data)
