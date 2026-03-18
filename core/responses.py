"""
Standardized API response helpers.
"""
from rest_framework.response import Response
from rest_framework import status


class APIResponse:
    """Factory for consistent JSON responses."""

    @staticmethod
    def success(data=None, message='Success', status_code=status.HTTP_200_OK):
        return Response({
            'success': True,
            'message': message,
            'data': data,
        }, status=status_code)

    @staticmethod
    def created(data=None, message='Created successfully'):
        return Response({
            'success': True,
            'message': message,
            'data': data,
        }, status=status.HTTP_201_CREATED)

    @staticmethod
    def error(message='An error occurred', errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        return Response({
            'success': False,
            'message': message,
            'errors': errors,
        }, status=status_code)

    @staticmethod
    def no_content(message='Deleted successfully'):
        return Response({
            'success': True,
            'message': message,
        }, status=status.HTTP_204_NO_CONTENT)
