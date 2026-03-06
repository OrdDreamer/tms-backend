from django.shortcuts import get_object_or_404
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


def _get_project(project_id):
    return _get_project(project_id)


class ProjectListCreateAPIView(APIView):
    """
    List projects (GET) and create a project (POST).
    """

    class Pagination(LimitOffsetPagination):
        default_limit = 20
        max_limit = 100

    def get(self, request):
        projects = Project.objects.all()

        paginator = self.Pagination()
        page = paginator.paginate_queryset(projects, request)
        serializer = ProjectListOutputSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = ProjectCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = project_create(**serializer.validated_data)

        output = ProjectDetailOutputSerializer(project)
        return Response(output.data, status=status.HTTP_201_CREATED)


class ProjectDetailAPIView(APIView):
    """
    Retrieve (GET), update (PATCH), and delete (DELETE) a project.
    """

    def get(self, request, project_id):
        project = _get_project(project_id)

        serializer = ProjectDetailOutputSerializer(project)
        return Response(serializer.data)

    def patch(self, request, project_id):
        project = _get_project(project_id)

        serializer = ProjectUpdateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = project_update(project=project, **serializer.validated_data)

        output = ProjectDetailOutputSerializer(project)
        return Response(output.data)

    def delete(self, request, project_id):
        project = _get_project(project_id)
        project_delete(project=project)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectLanguageListCreateAPIView(APIView):
    """
    List project languages (GET) and add a language (POST).
    """

    def get(self, request, project_id):
        project = _get_project(project_id)

        languages = ProjectLanguage.objects.filter(project=project)
        serializer = ProjectLanguageListOutputSerializer(languages, many=True)
        return Response(serializer.data)

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
    """
    Update (PATCH) and remove (DELETE) a project language.
    """

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

    def delete(self, request, project_id, lang_code):
        project_language = get_object_or_404(
            ProjectLanguage,
            project_id=project_id,
            language=lang_code,
        )
        project_language_remove(project_language=project_language)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectExportAPIView(APIView):
    """
    Export project translations (optionally filtered by language).
    """

    def get(self, request, project_id):
        project = _get_project(project_id)

        serializer = ProjectExportFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        language = serializer.validated_data.get("lang")
        data = project_translations_export(
            project=project, language=language,
        )
        return Response(data)
