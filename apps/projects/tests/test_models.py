import pytest
from django.core.exceptions import ValidationError

from apps.factories import ProjectFactory, ProjectLanguageFactory
from apps.projects.models import Project, ProjectLanguage


@pytest.mark.django_db
class TestProjectModel:
    def test_slug_unique(self):
        ProjectFactory(slug="unique")
        project_dup = Project(slug="unique", name="Duplicate")
        with pytest.raises(ValidationError):
            project_dup.full_clean()

    def test_str(self):
        project = ProjectFactory(slug="my-proj", name="My Project")
        assert str(project) == "(my-proj) My Project"

    def test_ordering(self):
        assert Project._meta.ordering == ["name"]


@pytest.mark.django_db
class TestProjectLanguageModel:
    def test_unique_project_language(self):
        pl = ProjectLanguageFactory(language="en")
        dup = ProjectLanguage(
            project=pl.project,
            language="en",
            is_base_language=False,
        )
        with pytest.raises(ValidationError):
            dup.full_clean()

    def test_clean_no_base_language_raises(self):
        project = ProjectFactory()
        pl = ProjectLanguage(
            project=project, language="en", is_base_language=False
        )
        with pytest.raises(ValidationError):
            pl.clean()

    def test_clean_passes_when_base_exists(self):
        pl = ProjectLanguageFactory(language="en", is_base_language=True)
        new_pl = ProjectLanguage(
            project=pl.project,
            language="uk",
            is_base_language=False,
        )
        new_pl.clean()  # should not raise

    def test_str(self):
        pl = ProjectLanguageFactory(language="en")
        assert pl.project.slug in str(pl)

    def test_repr(self):
        pl = ProjectLanguageFactory(language="en")
        assert "ProjectLanguage" in repr(pl)
