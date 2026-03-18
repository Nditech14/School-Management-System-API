"""
Audit Trail Views — Read-only for admins.
"""
import logging
from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from core.permissions import IsAdminUser
from .models import AuditLog
from .serializers import AuditLogSerializer

logger = logging.getLogger('school.audit')


@extend_schema(tags=['Audit Trail'])
class AuditLogListView(generics.ListAPIView):
    """Admin-only: read the full audit log."""
    queryset = AuditLog.objects.select_related('user').all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action', 'resource', 'user']
    search_fields = ['description', 'resource_id', 'user__email']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    @extend_schema(summary='List audit logs (Admin only)')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@extend_schema(tags=['Audit Trail'])
class AuditLogDetailView(generics.RetrieveAPIView):
    queryset = AuditLog.objects.select_related('user').all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'

    @extend_schema(summary='Get audit log entry (Admin only)')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
