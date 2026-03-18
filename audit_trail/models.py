"""
Audit Trail — Custom activity log for the system.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AuditLog(models.Model):
    """Manual audit log for key business events."""

    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('VIEW', 'View'),
        ('EXPORT', 'Export'),
        ('OTHER', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource = models.CharField(max_length=100, help_text='e.g. Student, Grade, User')
    resource_id = models.CharField(max_length=100, blank=True, help_text='PK of affected resource')
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    old_value = models.JSONField(null=True, blank=True, help_text='Snapshot before change')
    new_value = models.JSONField(null=True, blank=True, help_text='Snapshot after change')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        user_email = self.user.email if self.user else 'System'
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {user_email} | {self.action} | {self.resource}"
