"""
Request Logging Middleware — logs every inbound API request
"""
import time
import uuid
import logging

logger = logging.getLogger('school.api')


class RequestLoggingMiddleware:
    """Logs each HTTP request with timing, method, path, and response status."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = str(uuid.uuid4())[:8]
        request.request_id = request_id
        start_time = time.time()

        user_info = (
            f"user={request.user.email}"
            if hasattr(request, 'user') and request.user.is_authenticated
            else 'anonymous'
        )

        logger.info(
            "[%s] -> %s %s | %s | IP=%s",
            request_id,
            request.method,
            request.get_full_path(),
            user_info,
            _get_client_ip(request),
        )

        response = self.get_response(request)

        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(
            "[%s] <- %s %s | status=%s | %sms",
            request_id,
            request.method,
            request.get_full_path(),
            response.status_code,
            duration_ms,
        )
        return response


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')