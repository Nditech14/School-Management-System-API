"""
Main URL Configuration — API v1 routing with Swagger docs.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

API_V1 = 'api/v1/'

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # API Schema & Docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API v1 — Users & Auth
    path(API_V1, include('users.urls')),

    # API v1 — Students
    path(API_V1, include('students.urls')),

    # API v1 — Academics
    path(API_V1, include('academics.urls')),

    # API v1 — Audit Trail
    path(API_V1, include('audit_trail.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
