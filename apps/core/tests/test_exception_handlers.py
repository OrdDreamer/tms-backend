import pytest
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.test import APIRequestFactory

from apps.core.exception_handlers import custom_exception_handler
from apps.core.exceptions import ApplicationError, ProjectError


class TestCustomExceptionHandler:
    def _get_context(self):
        factory = APIRequestFactory()
        request = factory.get("/")
        return {"request": request, "view": None}

    def test_django_validation_error_dict(self):
        exc = DjangoValidationError({"name": ["This field is required."]})
        response = custom_exception_handler(exc, self._get_context())
        assert response.status_code == 400
        assert response.data["message"] == "Validation error"
        assert "name" in response.data["extra"]

    def test_django_validation_error_list(self):
        exc = DjangoValidationError(["Something went wrong."])
        response = custom_exception_handler(exc, self._get_context())
        assert response.status_code == 400
        assert "non_field_errors" in response.data["extra"]

    def test_application_error(self):
        exc = ApplicationError("Custom error", extra={"key": "val"})
        response = custom_exception_handler(exc, self._get_context())
        assert response.status_code == 400
        assert response.data["message"] == "Custom error"
        assert response.data["extra"] == {"key": "val"}

    def test_project_error_subclass(self):
        exc = ProjectError("Project problem")
        response = custom_exception_handler(exc, self._get_context())
        assert response.status_code == 400
        assert response.data["message"] == "Project problem"

    def test_drf_error_wrapped(self):
        from rest_framework.exceptions import NotFound
        exc = NotFound("Not found")
        response = custom_exception_handler(exc, self._get_context())
        assert response.status_code == 404
        assert response.data["message"] == "Request failed"

    def test_unhandled_exception_returns_none(self):
        exc = RuntimeError("unhandled")
        response = custom_exception_handler(exc, self._get_context())
        assert response is None
