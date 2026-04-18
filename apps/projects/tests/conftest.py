import pytest

from apps.factories import ProjectFactory, ProjectLanguageFactory


@pytest.fixture
def project(db):
    return ProjectFactory()


@pytest.fixture
def project_with_language(db):
    pl = ProjectLanguageFactory(language="en", is_base_language=True)
    return pl.project
