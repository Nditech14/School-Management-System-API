"""
Custom User Model — Email-based auth, case-insensitive, role-based.
"""
import uuid
import logging
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from auditlog.registry import auditlog
from cloudinary.models import CloudinaryField

logger = logging.getLogger('school.api')


class UserManager(BaseUserManager):
    """Custom manager: email is the unique identifier (case-insensitive)."""

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Email address is required.')
        email = self.normalize_email(email).lower()  # always lowercase
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for the School Management System.
    - Email-based login (case-insensitive)
    - Role-based access control
    - Cloudinary profile photo
    """

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student', db_index=True)
    profile_photo = CloudinaryField(
    'profile_photo',
    folder='school/profile_photos',
    null=True,
    blank=True,
    transformation=[
        {'width': 400, 'height': 400, 'crop': 'fill', 'gravity': 'face'},
        {'quality': 'auto', 'fetch_format': 'auto'},
    ],
    help_text='Stored via Cloudinary — auto-resized to 400x400'
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}> [{self.role}]"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    def save(self, *args, **kwargs):
        # Normalize email to lowercase always
        self.email = self.email.lower()
        super().save(*args, **kwargs)


auditlog.register(User, exclude_fields=['password', 'last_login'])
