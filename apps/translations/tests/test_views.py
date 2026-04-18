import pytest
from django.urls import reverse
from rest_framework import status

from apps.factories import ProjectFactory, ProjectLanguageFactory
from apps.translations.utils import (
    translation_key_create,
    translation_value_create,
)


@pytest.fixture
def project_with_langs(db):
    project = ProjectFactory(slug="view-proj")
    ProjectLanguageFactory(
        project=project, language="en", is_base_language=True
    )
    ProjectLanguageFactory(
        project=project, language="uk", is_base_language=False
    )
    return project


@pytest.fixture
def key_with_values(project_with_langs):
    tk = translation_key_create(project=project_with_langs, key="common.hello")
    translation_value_create(translation_key=tk, language="en", value="Hello")
    translation_value_create(translation_key=tk, language="uk", value="Привіт")
    return tk


@pytest.mark.django_db
class TestTranslationKeyListCreateView:
    def _url(self, slug="view-proj"):
        return reverse(
            "projects:translations:translation-key-list",
            kwargs={"project_slug": slug},
        )

    def test_list_keys(self, authenticated_client, key_with_values):
        response = authenticated_client.get(self._url())
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_list_with_translations(
        self, authenticated_client, key_with_values
    ):
        response = authenticated_client.get(self._url())
        result = response.data["results"][0]
        assert "translations" in result
        assert result["translations"]["en"] == "Hello"

    def test_list_without_translations(
        self, authenticated_client, key_with_values
    ):
        response = authenticated_client.get(
            self._url(),
            {"include_translations": "false"},
        )
        result = response.data["results"][0]
        assert "translations" not in result

    def test_search_filter(self, authenticated_client, project_with_langs):
        translation_key_create(project=project_with_langs, key="common.hello")
        translation_key_create(project=project_with_langs, key="auth.login")
        response = authenticated_client.get(self._url(), {"search": "auth"})
        assert response.data["count"] == 1

    def test_create_key(self, authenticated_client, project_with_langs):
        response = authenticated_client.post(
            self._url(),
            {"key": "new.key"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["key"] == "new.key"

    def test_create_key_with_translations(
        self, authenticated_client, project_with_langs
    ):
        response = authenticated_client.post(
            self._url(),
            {
                "key": "new.key",
                "translations": {"en": "Hello", "uk": "Привіт"},
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["translations"]["en"] == "Hello"

    def test_untranslated_filter(
        self, authenticated_client, project_with_langs
    ):
        tk1 = translation_key_create(
            project=project_with_langs, key="common.hello"
        )
        translation_value_create(
            translation_key=tk1, language="en", value="Hello"
        )
        translation_key_create(project=project_with_langs, key="common.bye")
        response = authenticated_client.get(
            self._url(),
            {"lang": "en", "untranslated": "true"},
        )
        assert response.data["count"] == 1
        assert response.data["results"][0]["key"] == "common.bye"


@pytest.mark.django_db
class TestTranslationKeyDetailView:
    def _url(self, key_name, slug="view-proj"):
        return reverse(
            "projects:translations:translation-key-detail",
            kwargs={"project_slug": slug, "key_name": key_name},
        )

    def test_retrieve(self, authenticated_client, key_with_values):
        response = authenticated_client.get(self._url("common.hello"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["key"] == "common.hello"

    def test_update(self, authenticated_client, key_with_values):
        response = authenticated_client.patch(
            self._url("common.hello"),
            {"description": "Updated"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["description"] == "Updated"

    def test_delete(self, authenticated_client, key_with_values):
        response = authenticated_client.delete(self._url("common.hello"))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_not_found(self, authenticated_client, project_with_langs):
        response = authenticated_client.get(self._url("nonexistent.key"))
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestTranslationKeyBulkDeleteView:
    def test_bulk_delete(self, authenticated_client, project_with_langs):
        translation_key_create(project=project_with_langs, key="a.one")
        translation_key_create(project=project_with_langs, key="a.two")
        response = authenticated_client.post(
            reverse(
                "projects:translations:translation-key-bulk-delete",
                kwargs={"project_slug": "view-proj"},
            ),
            {"keys": ["a.one", "a.two"]},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["deleted_count"] == 2


@pytest.mark.django_db
class TestTranslationListView:
    def _url(self, key_name, slug="view-proj"):
        return reverse(
            "projects:translations:translation-list",
            kwargs={"project_slug": slug, "key_name": key_name},
        )

    def test_list_translations(self, authenticated_client, key_with_values):
        response = authenticated_client.get(self._url("common.hello"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_bulk_update(self, authenticated_client, key_with_values):
        response = authenticated_client.patch(
            self._url("common.hello"),
            {"translations": {"en": "Hi", "uk": "Привіт!"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestTranslationDetailView:
    def _url(self, key_name, lang, slug="view-proj"):
        return reverse(
            "projects:translations:translation-detail",
            kwargs={
                "project_slug": slug,
                "key_name": key_name,
                "lang_code": lang,
            },
        )

    def test_create_translation(
        self, authenticated_client, project_with_langs
    ):
        translation_key_create(project=project_with_langs, key="new.key")
        response = authenticated_client.put(
            self._url("new.key", "en"),
            {"value": "Hello"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["value"] == "Hello"

    def test_update_translation(self, authenticated_client, key_with_values):
        response = authenticated_client.put(
            self._url("common.hello", "en"),
            {"value": "Hi there"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["value"] == "Hi there"

    def test_delete_translation(self, authenticated_client, key_with_values):
        response = authenticated_client.delete(self._url("common.hello", "en"))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_put_empty_value_deletes(
        self, authenticated_client, key_with_values
    ):
        response = authenticated_client.put(
            self._url("common.hello", "en"),
            {"value": ""},
            format="json",
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestPublicProjectTranslationsView:
    def _url(self, slug="view-proj"):
        return reverse("public-translations", kwargs={"project_slug": slug})

    def test_no_auth_required(self, api_client, key_with_values):
        response = api_client.get(self._url())
        assert response.status_code == status.HTTP_200_OK

    def test_returns_translations(self, api_client, key_with_values):
        response = api_client.get(self._url())
        assert "en" in response.data
        assert response.data["en"]["common.hello"] == "Hello"

    def test_etag_header(self, api_client, key_with_values):
        response = api_client.get(self._url())
        assert "ETag" in response
        assert "Cache-Control" in response

    def test_etag_304(self, api_client, key_with_values):
        response1 = api_client.get(self._url())
        etag = response1["ETag"]
        response2 = api_client.get(self._url(), HTTP_IF_NONE_MATCH=etag)
        assert response2.status_code == status.HTTP_304_NOT_MODIFIED

    def test_single_language(self, api_client, key_with_values):
        response = api_client.get(self._url(), {"lang": "en"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["common.hello"] == "Hello"

    def test_nested_format(self, api_client, key_with_values):
        response = api_client.get(self._url(), {"export_format": "nested"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["en"]["common"]["hello"] == "Hello"

    def test_not_found_project(self, api_client):
        response = api_client.get(self._url("nonexistent"))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_throttle_config(self):
        from apps.translations.views import PublicProjectTranslationsAPIView

        assert PublicProjectTranslationsAPIView.throttle_scope == "public_api"
