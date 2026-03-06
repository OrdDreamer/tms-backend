from django.urls import include, path

from apps.projects.views import (
    ProjectDetailAPIView,
    ProjectExportAPIView,
    ProjectLanguageDetailAPIView,
    ProjectLanguageListCreateAPIView,
    ProjectListCreateAPIView,
)

app_name = "projects"

urlpatterns = [
    path(
        "",
        ProjectListCreateAPIView.as_view(),
        name="project-list",
    ),
    path(
        "<uuid:project_id>/",
        ProjectDetailAPIView.as_view(),
        name="project-detail",
    ),
    path(
        "<uuid:project_id>/languages/",
        ProjectLanguageListCreateAPIView.as_view(),
        name="project-language-list",
    ),
    path(
        "<uuid:project_id>/languages/<str:lang_code>/",
        ProjectLanguageDetailAPIView.as_view(),
        name="project-language-detail",
    ),
    path(
        "<uuid:project_id>/keys/",
        include("apps.translations.urls"),
    ),
    path(
        "<uuid:project_id>/export/",
        ProjectExportAPIView.as_view(),
        name="project-export",
    ),
]
