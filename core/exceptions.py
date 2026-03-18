"""
Custom Exception Handler — Clean, structured error responses
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework.exceptions import (
    AuthenticationFailed, NotAuthenticated, PermissionDenied,
    ValidationError, NotFound, MethodNotAllowed, Throttled,
)

logger = logging.getLogger('school.api')


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns structured JSON error responses.
    Format: { "success": false, "message": "...", "errors": {...}, "status_code": 400 }
    """
    # Let DRF handle the initial processing
    response = exception_handler(exc, context)

    # Handle Django's built-in ValidationError
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(detail=exc.messages)
        response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            'success': False,
            'status_code': response.status_code,
            'message': _get_error_message(exc, response),
            'errors': _format_errors(response.data),
        }
        log_level = logging.WARNING if response.status_code >= 500 else logging.INFO
        logger.log(
            log_level,
            "API Error [%s] %s: %s",
            response.status_code,
            context.get('view', '').__class__.__name__ if context.get('view') else 'Unknown',
            error_data['message'],
        )
        response.data = error_data
    else:
        # Unhandled exception
        logger.exception("Unhandled exception in view: %s", exc)
        response = Response(
            {
                'success': False,
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'message': 'An unexpected error occurred. Please try again later.',
                'errors': None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _get_error_message(exc, response):
    """Extract a human-readable message from the exception."""
    if isinstance(exc, AuthenticationFailed):
        return 'Authentication failed. Invalid credentials or token.'
    if isinstance(exc, NotAuthenticated):
        return 'Authentication required. Please provide a valid token.'
    if isinstance(exc, PermissionDenied):
        return 'You do not have permission to perform this action.'
    if isinstance(exc, NotFound) or isinstance(exc, Http404):
        return 'The requested resource was not found.'
    if isinstance(exc, MethodNotAllowed):
        return f'Method not allowed: {exc.args[0] if exc.args else ""}'
    if isinstance(exc, Throttled):
        return f'Request was throttled. Expected available in {exc.wait} seconds.'
    if isinstance(exc, ValidationError):
        return 'Validation failed. Please check the submitted data.'
    return 'An error occurred.'


def _format_errors(data):
    """Normalize error data into a consistent dictionary format."""
    if isinstance(data, list):
        return {'detail': data}
    if isinstance(data, dict):
        if 'detail' in data and len(data) == 1:
            return {'detail': str(data['detail'])}
        return {
            field: [str(err) for err in errors] if isinstance(errors, list) else [str(errors)]
            for field, errors in data.items()
        }
    return {'detail': str(data)}
