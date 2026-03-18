from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_email', 'user_name',
            'action', 'resource', 'resource_id',
            'description', 'ip_address', 'old_value', 'new_value', 'timestamp',
        ]
        read_only_fields = ['id', 'timestamp']

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None

    def get_user_name(self, obj):
        return obj.user.get_full_name() if obj.user else 'System'
