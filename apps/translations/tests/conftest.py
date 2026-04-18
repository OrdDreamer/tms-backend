import pytest

from apps.factories import (
    ProjectFactory,
    ProjectLanguageFactory,
    TranslationKeyFactory,
)


@pytest.fixture
def project_with_langs(db):
    project = ProjectFactory(slug="trans-proj")
    ProjectLanguageFactory(
        project=project, language="en", is_base_language=True
    )
    ProjectLanguageFactory(
        project=project, language="uk", is_base_language=False
    )
    return project


@pytest.fixture
def translation_key(project_with_langs):
    return TranslationKeyFactory(
        project=project_with_langs, key="common.hello"
    )
