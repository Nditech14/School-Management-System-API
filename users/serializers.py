"""
User Serializers — Registration, Profile, JWT Token customization.
"""
import io
import logging
from PIL import Image
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()
logger = logging.getLogger('school.api')
security_logger = logging.getLogger('school.security')


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user signup. Email is normalized to lowercase."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Password must be at least 8 characters.'
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'phone_number', 'role', 'password', 'password_confirm',
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'role': {'required': False},
        }

    def validate_email(self, value):
        """Normalize email to lowercase (case-insensitive)."""
        return value.lower().strip()

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        logger.info("New user registered: %s [%s]", user.email, user.role)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for viewing/updating user profile. Supports multipart/form-data for image upload."""

    full_name = serializers.SerializerMethodField(read_only=True)
    profile_photo_url = serializers.SerializerMethodField(read_only=True)
    profile_photo = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text='Upload a profile photo (JPG, PNG, GIF). Stored on Cloudinary.',
    )

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'role', 'profile_photo', 'profile_photo_url',
            'is_active', 'date_joined', 'updated_at',
        ]
        read_only_fields = ['id', 'email', 'role', 'is_active', 'date_joined', 'updated_at']

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_profile_photo_url(self, obj):
        if obj.profile_photo:
            try:
                return obj.profile_photo.url
            except Exception:
                return None
        return None


class UserAdminSerializer(serializers.ModelSerializer):
    """Admin-level serializer: can see/edit all fields including role."""

    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'role', 'profile_photo',
            'is_active', 'is_staff', 'date_joined', 'updated_at',
        ]
        read_only_fields = ['id', 'date_joined', 'updated_at']

    def get_full_name(self, obj):
        return obj.get_full_name()


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change endpoint."""

    old_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'New passwords do not match.'})
        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer:
    - Case-insensitive email login
    - Includes user role and name in token payload
    """

    def validate(self, attrs):
        # Normalize email to lowercase before validation
        attrs['email'] = attrs.get('email', '').lower().strip()
        data = super().validate(attrs)

        # Add custom claims to response
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'full_name': self.user.get_full_name(),
            'role': self.user.role,
        }

        security_logger.info("Login successful: %s [%s]", self.user.email, self.user.role)
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Embed claims in JWT payload
        token['role'] = user.role
        token['email'] = user.email
        token['full_name'] = user.get_full_name()
        return token