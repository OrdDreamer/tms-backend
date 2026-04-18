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
        "<slug:project_slug>/",
        ProjectDetailAPIView.as_view(),
        name="project-detail",
    ),
    path(
        "<slug:project_slug>/languages/",
        ProjectLanguageListCreateAPIView.as_view(),
        name="project-language-list",
    ),
    path(
        "<slug:project_slug>/languages/<str:lang_code>/",
        ProjectLanguageDetailAPIView.as_view(),
        name="project-language-detail",
    ),
    path(
        "<slug:project_slug>/keys/",
        include("apps.translations.urls"),
    ),
    path(
        "<slug:project_slug>/export/",
        ProjectExportAPIView.as_view(),
        name="project-export",
    ),
]
