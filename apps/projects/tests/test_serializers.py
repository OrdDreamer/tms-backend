from apps.projects.serializers import (
    ProjectCreateInputSerializer,
    ProjectUpdateInputSerializer,
    ProjectExportFilterSerializer,
)


class TestProjectCreateInputSerializer:
    def test_valid(self):
        data = {"slug": "my-project", "name": "My Project"}
        s = ProjectCreateInputSerializer(data=data)
        assert s.is_valid()

    def test_slug_required(self):
        s = ProjectCreateInputSerializer(data={"name": "Proj"})
        assert not s.is_valid()
        assert "slug" in s.errors

    def test_description_optional(self):
        data = {"slug": "proj", "name": "Proj"}
        s = ProjectCreateInputSerializer(data=data)
        assert s.is_valid()
        assert s.validated_data["description"] == ""


class TestProjectUpdateInputSerializer:
    def test_all_optional(self):
        s = ProjectUpdateInputSerializer(data={})
        assert s.is_valid()


class TestProjectExportFilterSerializer:
    def test_defaults(self):
        s = ProjectExportFilterSerializer(data={})
        assert s.is_valid()
        assert s.validated_data["export_format"] == "flat"

    def test_invalid_format(self):
        s = ProjectExportFilterSerializer(data={"export_format": "xml"})
        assert not s.is_valid()
