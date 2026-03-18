"""
Student Serializers
Covers: Faculty, Department, Programme, ClassRoom, AcademicSession,
        StudentProfile, StudentDocument, Guardian
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Faculty, Department, Programme, ClassRoom, AcademicSession,
    StudentProfile, StudentDocument, Guardian,
)

User = get_user_model()


# ─── Academic Session ─────────────────────────────────────────────────────────

class AcademicSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicSession
        fields = ['id', 'name', 'start_date', 'end_date', 'is_current', 'created_at']
        read_only_fields = ['id', 'created_at']


# ─── Faculty ──────────────────────────────────────────────────────────────────

class FacultySerializer(serializers.ModelSerializer):
    dean_name = serializers.SerializerMethodField(read_only=True)
    department_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Faculty
        fields = [
            'id', 'name', 'code', 'dean', 'dean_name',
            'description', 'is_active', 'department_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_code(self, value):
        return value.upper().strip()

    def get_dean_name(self, obj):
        return obj.dean.get_full_name() if obj.dean else None

    def get_department_count(self, obj):
        return obj.departments.filter(is_active=True).count()


# ─── Department ───────────────────────────────────────────────────────────────

class DepartmentSerializer(serializers.ModelSerializer):
    hod_name = serializers.SerializerMethodField(read_only=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    programme_count = serializers.SerializerMethodField(read_only=True)
    student_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Department
        fields = [
            'id', 'faculty', 'faculty_name', 'name', 'code',
            'hod', 'hod_name', 'description', 'is_active',
            'programme_count', 'student_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_code(self, value):
        return value.upper().strip()

    def get_hod_name(self, obj):
        return obj.hod.get_full_name() if obj.hod else None

    def get_programme_count(self, obj):
        return obj.programmes.filter(is_active=True).count()

    def get_student_count(self, obj):
        return obj.students.filter(is_active=True).count()


class DepartmentListSerializer(serializers.ModelSerializer):
    """Lightweight — used inside nested representations."""
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)

    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'faculty_name']


# ─── Programme ────────────────────────────────────────────────────────────────

class ProgrammeSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    faculty_name = serializers.CharField(source='department.faculty.name', read_only=True)
    student_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Programme
        fields = [
            'id', 'department', 'department_name', 'faculty_name',
            'name', 'code', 'degree_type', 'duration_years',
            'total_units_required', 'description', 'is_active',
            'student_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_code(self, value):
        return value.upper().strip()

    def get_student_count(self, obj):
        return obj.students.filter(is_active=True).count()


# ─── Classroom ────────────────────────────────────────────────────────────────

class ClassRoomSerializer(serializers.ModelSerializer):
    class_teacher_name = serializers.SerializerMethodField(read_only=True)
    student_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ClassRoom
        fields = [
            'id', 'name', 'grade_level', 'capacity',
            'class_teacher', 'class_teacher_name', 'student_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_class_teacher_name(self, obj):
        return obj.class_teacher.get_full_name() if obj.class_teacher else None

    def get_student_count(self, obj):
        return obj.students.filter(is_active=True).count()


# ─── Guardian ─────────────────────────────────────────────────────────────────

class GuardianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guardian
        fields = [
            'id', 'user', 'first_name', 'last_name', 'email',
            'phone_number', 'relationship', 'occupation', 'address',
            'students', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_email(self, value):
        return value.lower().strip() if value else value


# ─── Student Document ─────────────────────────────────────────────────────────

class StudentDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField(read_only=True)
    file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = StudentDocument
        fields = [
            'id', 'student', 'document_type', 'title',
            'file', 'file_url', 'notes',
            'uploaded_by', 'uploaded_by_name', 'created_at',
        ]
        read_only_fields = ['id', 'uploaded_by', 'created_at']

    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() if obj.uploaded_by else None

    def get_file_url(self, obj):
        return obj.file.url if obj.file else None

    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


# ─── Student Profile ──────────────────────────────────────────────────────────

class StudentProfileSerializer(serializers.ModelSerializer):
    """Full profile — create/update."""

    # Read-only nested fields
    full_name = serializers.SerializerMethodField(read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    profile_photo = serializers.ImageField(source='user.profile_photo', read_only=True)
    programme_name = serializers.SerializerMethodField(read_only=True)
    department_name = serializers.SerializerMethodField(read_only=True)
    class_name = serializers.SerializerMethodField(read_only=True)
    age = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            # Identity
            'id', 'user', 'full_name', 'email', 'profile_photo',
            'student_id', 'date_of_birth', 'age', 'gender',
            'blood_group', 'religion', 'marital_status',
            # Contact
            'address', 'state_of_origin', 'lga', 'nationality',
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship',
            # Academic Placement
            'programme', 'programme_name',
            'department', 'department_name',
            'current_class', 'class_name',
            'current_level', 'current_semester',
            # Admission
            'admission_date', 'entry_mode',
            'jamb_registration_number', 'previous_school',
            # Medical
            'medical_conditions', 'disabilities',
            # Status
            'status', 'graduation_date', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    def get_programme_name(self, obj):
        return str(obj.programme) if obj.programme else None

    def get_department_name(self, obj):
        return obj.department.name if obj.department else None

    def get_class_name(self, obj):
        return str(obj.current_class) if obj.current_class else None

    def get_age(self, obj):
        return obj.age

    def validate_student_id(self, value):
        return value.upper().strip()


class StudentListSerializer(serializers.ModelSerializer):
    """Lightweight — list view."""
    full_name = serializers.SerializerMethodField()
    email = serializers.CharField(source='user.email', read_only=True)
    department_name = serializers.SerializerMethodField()
    programme_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'student_id', 'full_name', 'email',
            'department_name', 'programme_name',
            'current_level', 'gender', 'status', 'admission_date',
        ]

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    def get_department_name(self, obj):
        return obj.department.name if obj.department else None

    def get_programme_name(self, obj):
        return obj.programme.name if obj.programme else None


class StudentDetailSerializer(StudentProfileSerializer):
    """Full profile with nested guardians and documents."""
    guardians = GuardianSerializer(many=True, read_only=True)
    documents = StudentDocumentSerializer(many=True, read_only=True)

    class Meta(StudentProfileSerializer.Meta):
        fields = StudentProfileSerializer.Meta.fields + ['guardians', 'documents']
