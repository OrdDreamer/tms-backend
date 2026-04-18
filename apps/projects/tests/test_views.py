import pytest
from django.urls import reverse
from rest_framework import status

from apps.factories import ProjectFactory, ProjectLanguageFactory
from apps.projects.models import Project
from apps.translations.utils import (
    translation_key_create,
    translation_value_create,
)


@pytest.fixture
def project_with_langs(db):
    project = ProjectFactory(slug="test-proj")
    ProjectLanguageFactory(
        project=project, language="en", is_base_language=True
    )
    ProjectLanguageFactory(
        project=project, language="uk", is_base_language=False
    )
    return project


@pytest.mark.django_db
class TestProjectListCreateView:
    def test_list_requires_auth(self, api_client):
        response = api_client.get(reverse("projects:project-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_projects(self, authenticated_client):
        ProjectFactory.create_batch(3)
        response = authenticated_client.get(reverse("projects:project-list"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_create_project(self, authenticated_client):
        response = authenticated_client.post(
            reverse("projects:project-list"),
            {"slug": "new-proj", "name": "New Project"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["slug"] == "new-proj"
        assert Project.objects.filter(slug="new-proj").exists()


@pytest.mark.django_db
class TestProjectDetailView:
    def test_retrieve(self, authenticated_client):
        project = ProjectFactory(slug="detail-proj")
        ProjectLanguageFactory(
            project=project, language="en", is_base_language=True
        )
        response = authenticated_client.get(
            reverse(
                "projects:project-detail",
                kwargs={"project_slug": "detail-proj"},
            ),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["slug"] == "detail-proj"
        assert len(response.data["languages"]) == 1

    def test_update(self, authenticated_client):
        project = ProjectFactory(slug="upd-proj")
        ProjectLanguageFactory(
            project=project, language="en", is_base_language=True
        )
        response = authenticated_client.patch(
            reverse(
                "projects:project-detail", kwargs={"project_slug": "upd-proj"}
            ),
            {"name": "Updated Name"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Name"

    def test_delete(self, authenticated_client):
        ProjectFactory(slug="del-proj")
        response = authenticated_client.delete(
            reverse(
                "projects:project-detail", kwargs={"project_slug": "del-proj"}
            ),
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Project.objects.filter(slug="del-proj").exists()

    def test_not_found(self, authenticated_client):
        response = authenticated_client.get(
            reverse(
                "projects:project-detail",
                kwargs={"project_slug": "nonexistent"},
            ),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestProjectLanguageViews:
    def test_list_languages(self, authenticated_client, project_with_langs):
        response = authenticated_client.get(
            reverse(
                "projects:project-language-list",
                kwargs={"project_slug": "test-proj"},
            ),
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_add_language(self, authenticated_client, project_with_langs):
        response = authenticated_client.post(
            reverse(
                "projects:project-language-list",
                kwargs={"project_slug": "test-proj"},
            ),
            {"language": "pl"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["language"] == "pl"

    def test_set_base_language(self, authenticated_client, project_with_langs):
        response = authenticated_client.patch(
            reverse(
                "projects:project-language-detail",
                kwargs={
                    "project_slug": "test-proj",
                    "lang_code": "uk",
                },
            ),
            {"is_base_language": True},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_base_language"] is True

    def test_remove_language(self, authenticated_client, project_with_langs):
        response = authenticated_client.delete(
            reverse(
                "projects:project-language-detail",
                kwargs={
                    "project_slug": "test-proj",
                    "lang_code": "uk",
                },
            ),
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestProjectExportView:
    def test_export_flat(self, authenticated_client, project_with_langs):
        tk = translation_key_create(
            project=project_with_langs,
            key="common.hello",
        )
        translation_value_create(
            translation_key=tk,
            language="en",
            value="Hello",
        )
        response = authenticated_client.get(
            reverse(
                "projects:project-export", kwargs={"project_slug": "test-proj"}
            ),
        )
        assert response.status_code == status.HTTP_200_OK
        assert "en" in response.data
        assert response.data["en"]["common.hello"] == "Hello"

    def test_export_nested(self, authenticated_client, project_with_langs):
        tk = translation_key_create(
            project=project_with_langs,
            key="common.hello",
        )
        translation_value_create(
            translation_key=tk,
            language="en",
            value="Hello",
        )
        response = authenticated_client.get(
            reverse(
                "projects:project-export", kwargs={"project_slug": "test-proj"}
            ),
            {"export_format": "nested"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["en"]["common"]["hello"] == "Hello"

    def test_export_single_language(
        self, authenticated_client, project_with_langs
    ):
        tk = translation_key_create(
            project=project_with_langs,
            key="common.hello",
        )
        translation_value_create(
            translation_key=tk,
            language="en",
            value="Hello",
        )
        response = authenticated_client.get(
            reverse(
                "projects:project-export", kwargs={"project_slug": "test-proj"}
            ),
            {"lang": "en"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["common.hello"] == "Hello"
