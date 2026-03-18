from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView, TokenRefreshCustomView,
    ProfileView, ChangePasswordView,
    AdminUserListView, AdminUserDetailView,
)

urlpatterns = [
    # Auth
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/token/refresh/', TokenRefreshCustomView.as_view(), name='token-refresh'),

    # Profile
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/change-password/', ChangePasswordView.as_view(), name='change-password'),

    # Admin — Users
    path('admin/users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('admin/users/<uuid:id>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
]
