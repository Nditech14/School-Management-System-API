"""
Audit Trail utility — call this from any view or service to log business events.
"""
import logging
from .models import AuditLog

audit_logger = logging.getLogger('school.audit')


def log_action(
    user,
    action: str,
    resource: str,
    resource_id: str = '',
    description: str = '',
    request=None,
    old_value=None,
    new_value=None,
):
    """
    Create an AuditLog entry and write to the audit log file.

    Usage:
        log_action(request.user, 'CREATE', 'Student', student.student_id,
                   'New student registered', request=request)
    """
    ip_address = None
    user_agent = ''

    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_address = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:512]

    entry = AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        resource=resource,
        resource_id=str(resource_id),
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        old_value=old_value,
        new_value=new_value,
    )

    audit_logger.info(
        "AUDIT | %s | %s | %s [id=%s] | %s",
        user.email if user and user.is_authenticated else 'System',
        action,
        resource,
        resource_id,
        description,
    )

    return entry
