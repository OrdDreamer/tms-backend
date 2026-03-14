import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from rest_framework.views import exception_handler

from apps.core.exceptions import ApplicationError

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Custom exception handler for consistent API errors."""

    if isinstance(exc, Throttled):
        wait = int(exc.wait) if exc.wait else None
        msg = (
            f"Too many requests. Retry in {wait}s."
            if wait
            else "Too many requests."
        )
        return Response({"message": msg, "extra": {}}, status=429)

    # Handle Django validation errors (400 — normal behaviour, no logging)
    if isinstance(exc, DjangoValidationError):
        data = (
            exc.message_dict
            if hasattr(exc, "message_dict")
            else {"non_field_errors": exc.messages}
        )
        return Response(
            {
                "message": "Validation error",
                "extra": data,
            },
            status=400,
        )

    if isinstance(exc, ApplicationError):
        logger.warning(
            "ApplicationError: %s | extra=%s",
            exc.message,
            exc.extra,
        )
        return Response(
            {
                "message": exc.message,
                "extra": exc.extra,
            },
            status=400,
        )

    # Default DRF handling
    response = exception_handler(exc, context)

    if response is not None:
        # Standardize DRF error format
        custom_response_data = {
            "message": "Request failed",
            "extra": response.data,
        }
        response.data = custom_response_data
    else:
        # Unhandled exception — 500
        logger.error(
            "Unhandled exception in %s",
            context.get("view", "unknown view"),
            exc_info=exc,
        )

    return response
