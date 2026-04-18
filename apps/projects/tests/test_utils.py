import pytest
from django.core.exceptions import ValidationError

from apps.core.exceptions import ProjectError
from apps.factories import ProjectFactory
from apps.projects.models import ProjectLanguage
from apps.projects.utils import (
    project_create,
    project_delete,
    project_language_add,
    project_language_bulk_add,
    project_language_remove,
    project_language_set_base,
    project_update,
)


@pytest.mark.django_db
class TestProjectCreate:
    def test_creates_project(self):
        project = project_create(slug="new", name="New Project")
        assert project.slug == "new"
        assert project.name == "New Project"

    def test_duplicate_slug_raises(self):
        project_create(slug="dup", name="First")
        with pytest.raises(ValidationError):
            project_create(slug="dup", name="Second")

    def test_with_description(self):
        project = project_create(
            slug="desc", name="Desc", description="A description"
        )
        assert project.description == "A description"


@pytest.mark.django_db
class TestProjectUpdate:
    def test_update_name(self):
        project = ProjectFactory()
        updated = project_update(project=project, name="Updated")
        assert updated.name == "Updated"

    def test_update_slug(self):
        project = ProjectFactory()
        updated = project_update(project=project, slug="new-slug")
        assert updated.slug == "new-slug"

    def test_no_fields_noop(self):
        project = ProjectFactory()
        result = project_update(project=project)
        assert result == project


@pytest.mark.django_db
class TestProjectDelete:
    def test_deletes_project(self):
        project = ProjectFactory()
        pk = project.pk
        project_delete(project=project)
        from apps.projects.models import Project

        assert not Project.objects.filter(pk=pk).exists()


@pytest.mark.django_db
class TestProjectLanguageAdd:
    def test_first_language_becomes_base(self):
        project = ProjectFactory()
        pl = project_language_add(project=project, language="en")
        assert pl.is_base_language is True

    def test_second_language_not_base(self):
        project = ProjectFactory()
        project_language_add(project=project, language="en")
        pl = project_language_add(project=project, language="uk")
        assert pl.is_base_language is False

    def test_add_as_base_demotes_old(self):
        project = ProjectFactory()
        en = project_language_add(project=project, language="en")
        uk = project_language_add(
            project=project, language="uk", is_base_language=True
        )
        en.refresh_from_db()
        assert en.is_base_language is False
        assert uk.is_base_language is True

    def test_duplicate_language_raises(self):
        project = ProjectFactory()
        project_language_add(project=project, language="en")
        with pytest.raises(ValidationError):
            project_language_add(project=project, language="en")


@pytest.mark.django_db
class TestProjectLanguageRemove:
    def test_remove_non_base(self):
        project = ProjectFactory()
        project_language_add(project=project, language="en")
        uk = project_language_add(project=project, language="uk")
        project_language_remove(project_language=uk)
        assert not ProjectLanguage.objects.filter(pk=uk.pk).exists()

    def test_remove_base_raises(self):
        project = ProjectFactory()
        en = project_language_add(project=project, language="en")
        project_language_add(project=project, language="uk")
        with pytest.raises(ProjectError, match="base language"):
            project_language_remove(project_language=en)

    def test_remove_only_language_raises(self):
        project = ProjectFactory()
        en = project_language_add(project=project, language="en")
        # Only language is also base, so base check fires first
        with pytest.raises(ProjectError, match="base language"):
            project_language_remove(project_language=en)


@pytest.mark.django_db
class TestProjectLanguageSetBase:
    def test_set_base(self):
        project = ProjectFactory()
        en = project_language_add(project=project, language="en")
        uk = project_language_add(project=project, language="uk")
        result = project_language_set_base(project_language=uk)
        assert result.is_base_language is True
        en.refresh_from_db()
        assert en.is_base_language is False

    def test_already_base_noop(self):
        project = ProjectFactory()
        en = project_language_add(project=project, language="en")
        result = project_language_set_base(project_language=en)
        assert result.is_base_language is True


@pytest.mark.django_db
class TestProjectLanguageBulkAdd:
    def test_bulk_add(self):
        project = ProjectFactory()
        langs = project_language_bulk_add(
            project=project,
            languages_data=[
                {"language": "en"},
                {"language": "uk"},
            ],
        )
        assert len(langs) == 2
        assert langs[0].is_base_language is True  # first becomes base

    def test_explicit_base(self):
        project = ProjectFactory()
        langs = project_language_bulk_add(
            project=project,
            languages_data=[
                {"language": "uk", "is_base_language": True},
                {"language": "en"},
            ],
        )
        uk = next(lang for lang in langs if lang.language == "uk")
        en = next(lang for lang in langs if lang.language == "en")
        assert uk.is_base_language is True
        assert en.is_base_language is False

    def test_multiple_bases_raises(self):
        project = ProjectFactory()
        with pytest.raises(ProjectError, match="one language"):
            project_language_bulk_add(
                project=project,
                languages_data=[
                    {"language": "en", "is_base_language": True},
                    {"language": "uk", "is_base_language": True},
                ],
            )
