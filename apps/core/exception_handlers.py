from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.core.exceptions import ApplicationError


def custom_exception_handler(exc, context):
    """Custom exception handler for consistent API errors."""

    # Handle Django validation errors
    if isinstance(exc, DjangoValidationError):
        data = exc.message_dict if hasattr(exc, "message_dict") else {
            "non_field_errors": exc.messages
        }
        return Response({
            "message": "Validation error",
            "extra": data,
        }, status=400)

    if isinstance(exc, ApplicationError):
        return Response({
            "message": exc.message,
            "extra": exc.extra,
        }, status=400)

    # Default DRF handling
    response = exception_handler(exc, context)

    if response is not None:
        # Standardize DRF error format
        custom_response_data = {
            "message": "Request failed",
            "extra": response.data,
        }
        response.data = custom_response_data

    return response
