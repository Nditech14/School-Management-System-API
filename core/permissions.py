"""
Custom role-based permissions for the School Management System.
"""
from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """Only admin users can access."""
    message = 'Admin access required.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'admin'
        )


class IsTeacher(BasePermission):
    """Only teachers can access."""
    message = 'Teacher access required.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ('teacher', 'admin')
        )


class IsStudent(BasePermission):
    """Only students can access."""
    message = 'Student access required.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ('student', 'admin')
        )


class IsParent(BasePermission):
    """Only parents can access."""
    message = 'Parent access required.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ('parent', 'admin')
        )


class IsAdminOrTeacher(BasePermission):
    """Admins and teachers can access."""
    message = 'Admin or Teacher access required.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ('admin', 'teacher')
        )


class IsOwnerOrAdmin(BasePermission):
    """Allow object owner or admin."""
    message = 'You can only access your own data.'

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user
