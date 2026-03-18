from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'resource', 'resource_id', 'ip_address']
    list_filter = ['action', 'resource', 'timestamp']
    search_fields = ['user__email', 'resource_id', 'description']
    readonly_fields = ['id', 'timestamp', 'user', 'action', 'resource', 'resource_id',
                       'description', 'ip_address', 'user_agent', 'old_value', 'new_value']
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
