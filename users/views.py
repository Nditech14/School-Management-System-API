"""
User Views — Auth, Profile, Admin user management.
"""
import logging
from django.contrib.auth import get_user_model
from rest_framework import status, generics, filters, parsers
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample
from django_filters.rest_framework import DjangoFilterBackend

from core.permissions import IsAdminUser
from core.responses import APIResponse
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    UserAdminSerializer,
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
)

User = get_user_model()
logger = logging.getLogger('school.api')
security_logger = logging.getLogger('school.security')
audit_logger = logging.getLogger('school.audit')


@extend_schema(tags=['Authentication'])
class RegisterView(APIView):
    """Register a new user account."""
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    @extend_schema(
        summary='Register new user',
        request=UserRegistrationSerializer,
        responses={201: UserProfileSerializer},
        examples=[
            OpenApiExample(
                'Registration Example',
                value={
                    'email': 'john.doe@school.edu',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'phone_number': '+2348012345678',
                    'role': 'student',
                    'password': 'SecurePass123!',
                    'password_confirm': 'SecurePass123!'
                },
                request_only=True,
            )
        ]
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        profile = UserProfileSerializer(user)
        return APIResponse.created(
            data=profile.data,
            message='Account created successfully.'
        )


@extend_schema(tags=['Authentication'])
class LoginView(TokenObtainPairView):
    """Login with email and password. Returns JWT access + refresh tokens."""
    serializer_class = CustomTokenObtainPairSerializer

    @extend_schema(
        summary='Login (Email + Password)',
        examples=[
            OpenApiExample(
                'Login Example',
                value={'email': 'JOHN.DOE@school.edu', 'password': 'SecurePass123!'},
                description='Email is case-insensitive.',
                request_only=True,
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@extend_schema(tags=['Authentication'])
class LogoutView(APIView):
    """Blacklist the refresh token to log the user out."""
    permission_classes = [IsAuthenticated]

    @extend_schema(summary='Logout (Blacklist refresh token)')
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return APIResponse.error('Refresh token is required.')
            token = RefreshToken(refresh_token)
            token.blacklist()
            security_logger.info("User logged out: %s", request.user.email)
            return APIResponse.success(message='Logged out successfully.')
        except Exception as e:
            logger.warning("Logout error for %s: %s", request.user.email, str(e))
            return APIResponse.error('Invalid or expired token.')


@extend_schema(tags=['Authentication'])
class TokenRefreshCustomView(TokenRefreshView):
    """Refresh the JWT access token using a valid refresh token."""

    @extend_schema(summary='Refresh access token')
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@extend_schema(tags=['Profile'])
class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update the current user's profile.
    Use multipart/form-data (not application/json) to upload a profile_photo file.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    # Accept both multipart (for file uploads) and JSON
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_object(self):
        return self.request.user

    @extend_schema(summary='Get my profile')
    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return APIResponse.success(data=serializer.data)

    @extend_schema(
        summary='Update my profile (use multipart/form-data for photo upload)',
        request={'multipart/form-data': UserProfileSerializer},
        responses={200: UserProfileSerializer},
    )
    def put(self, request, *args, **kwargs):
        return self._update(request, partial=False)

    @extend_schema(
        summary='Partially update my profile (use multipart/form-data for photo upload)',
        request={'multipart/form-data': UserProfileSerializer},
        responses={200: UserProfileSerializer},
    )
    def patch(self, request, *args, **kwargs):
        return self._update(request, partial=True)

    def _update(self, request, partial):
        serializer = self.get_serializer(
            self.get_object(), data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        audit_logger.info("Profile updated: %s", user.email)
        return APIResponse.success(data=serializer.data, message='Profile updated.')


@extend_schema(tags=['Profile'])
class ChangePasswordView(APIView):
    """Change the current user's password."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Change password',
        request=ChangePasswordSerializer,
        responses={200: None},
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        if not user.check_password(serializer.validated_data['old_password']):
            security_logger.warning("Failed password change attempt: %s", user.email)
            return APIResponse.error('Old password is incorrect.', status_code=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        security_logger.info("Password changed: %s", user.email)
        return APIResponse.success(message='Password changed successfully.')


@extend_schema(tags=['Admin — Users'])
class AdminUserListView(generics.ListCreateAPIView):
    """Admin: list all users or create a new user."""
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = UserAdminSerializer
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering_fields = ['date_joined', 'email', 'role']
    ordering = ['-date_joined']

    @extend_schema(summary='List all users (Admin)')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary='Create user (Admin)')
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@extend_schema(tags=['Admin — Users'])
class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Admin: retrieve, update, or deactivate a specific user."""
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = UserAdminSerializer
    queryset = User.objects.all()
    lookup_field = 'id'

    @extend_schema(summary='Get user by ID (Admin)')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary='Update user (Admin)')
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(summary='Partially update user (Admin)')
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(summary='Delete user (Admin)')
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        audit_logger.info("User deleted by admin: %s [by %s]", user.email, request.user.email)
        return super().delete(request, *args, **kwargs)