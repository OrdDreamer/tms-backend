import uuid

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.projects.models import Project


@pytest.mark.django_db
class TestBaseModel:
    def test_uuid_pk_generated(self):
        project = Project.objects.create(slug="test", name="Test")
        assert isinstance(project.id, uuid.UUID)

    def test_created_at_set_on_create(self):
        before = timezone.now()
        project = Project.objects.create(slug="test", name="Test")
        assert project.created_at >= before

    def test_updated_at_set_on_save(self):
        project = Project.objects.create(slug="test", name="Test")
        old_updated = project.updated_at
        project.name = "Updated"
        project.save()
        project.refresh_from_db()
        assert project.updated_at > old_updated

    def test_full_clean_called_on_save(self):
        project = Project(slug="!invalid slug!", name="Test")
        with pytest.raises(ValidationError):
            project.save()

    def test_abstract_model_not_in_db(self):
        from apps.core.models import BaseModel

        assert BaseModel._meta.abstract is True
