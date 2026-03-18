"""
Student Models — Faculty, Department, Programme, Student Profile,
                  Guardian, Documents, Enrollment.
Supports both secondary-school and university-style academic structures.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from auditlog.registry import auditlog

User = get_user_model()


# ─── Academic Session ─────────────────────────────────────────────────────────

class AcademicSession(models.Model):
    """e.g. 2024/2025"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicSession.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


# ─── Faculty & Department ─────────────────────────────────────────────────────

class Faculty(models.Model):
    """Top-level academic grouping — e.g. Faculty of Engineering."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=10, unique=True)
    dean = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        limit_choices_to={'role': 'teacher'}, related_name='faculty_dean',
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Faculties'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Department(models.Model):
    """Academic department within a Faculty."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=10, unique=True)
    hod = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        limit_choices_to={'role': 'teacher'}, related_name='department_hod',
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['faculty', 'name']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


# ─── Programme ────────────────────────────────────────────────────────────────

class Programme(models.Model):
    """Degree programme offered by a department — e.g. B.Sc Computer Science."""

    DEGREE_TYPES = [
        ('ND', 'National Diploma'),
        ('HND', 'Higher National Diploma'),
        ('BSC', 'Bachelor of Science'),
        ('BEng', 'Bachelor of Engineering'),
        ('BA', 'Bachelor of Arts'),
        ('BEd', 'Bachelor of Education'),
        ('MBA', 'Master of Business Administration'),
        ('MSC', 'Master of Science'),
        ('PHD', 'Doctor of Philosophy'),
        ('CERT', 'Certificate'),
        ('DIP', 'Diploma'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='programmes')
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=15, unique=True)
    degree_type = models.CharField(max_length=10, choices=DEGREE_TYPES)
    duration_years = models.PositiveSmallIntegerField(default=4)
    total_units_required = models.PositiveIntegerField(default=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['department', 'name']
        ordering = ['name']

    def __str__(self):
        return f"{self.degree_type} {self.name} ({self.code})"


# ─── Classroom ────────────────────────────────────────────────────────────────

class ClassRoom(models.Model):
    """Physical or virtual classroom/level — e.g. 100L, 200L, JSS1A."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    grade_level = models.CharField(max_length=20)
    capacity = models.PositiveIntegerField(default=40)
    class_teacher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        limit_choices_to={'role': 'teacher'}, related_name='classes_taught',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['name', 'grade_level']
        ordering = ['grade_level', 'name']

    def __str__(self):
        return f"{self.grade_level} — {self.name}"


# ─── Student Profile ──────────────────────────────────────────────────────────

class StudentProfile(models.Model):
    """Full student record: personal info, academic placement, status."""

    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]

    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'), ('AB+', 'AB+'), ('AB-', 'AB-'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('graduated', 'Graduated'),
        ('suspended', 'Suspended'),
        ('withdrawn', 'Withdrawn'),
        ('deferred', 'Deferred'),
    ]

    ENTRY_MODE_CHOICES = [
        ('utme', 'UTME'),
        ('direct_entry', 'Direct Entry'),
        ('transfer', 'Transfer'),
        ('postgraduate', 'Postgraduate'),
    ]

    SEMESTER_CHOICES = [
        ('1st', '1st Semester'), ('2nd', '2nd Semester'),
        ('1st Term', '1st Term'), ('2nd Term', '2nd Term'), ('3rd Term', '3rd Term'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')

    # ── Identity
    student_id = models.CharField(max_length=20, unique=True, db_index=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    religion = models.CharField(max_length=50, blank=True)
    marital_status = models.CharField(
        max_length=20,
        choices=[('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced')],
        default='single',
    )

    # ── Contact
    address = models.TextField(blank=True)
    state_of_origin = models.CharField(max_length=50, blank=True)
    lga = models.CharField(max_length=100, blank=True, verbose_name='LGA')
    nationality = models.CharField(max_length=50, default='Nigerian')
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)

    # ── Academic Placement
    programme = models.ForeignKey(
        Programme, on_delete=models.SET_NULL, null=True, blank=True, related_name='students',
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='students',
    )
    current_class = models.ForeignKey(
        ClassRoom, on_delete=models.SET_NULL, null=True, blank=True, related_name='students',
    )
    current_level = models.CharField(max_length=10, blank=True, help_text='e.g. 100, 200, 300, 400')
    current_semester = models.CharField(max_length=10, blank=True, choices=SEMESTER_CHOICES)

    # ── Admission
    admission_date = models.DateField()
    entry_mode = models.CharField(max_length=20, choices=ENTRY_MODE_CHOICES, default='utme')
    jamb_registration_number = models.CharField(max_length=20, blank=True)
    previous_school = models.CharField(max_length=200, blank=True)

    # ── Medical
    medical_conditions = models.TextField(blank=True)
    disabilities = models.TextField(blank=True)

    # ── Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    graduation_date = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['student_id']

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_id})"

    @property
    def age(self):
        from datetime import date
        today = date.today()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


# ─── Student Document ─────────────────────────────────────────────────────────

class StudentDocument(models.Model):
    """Supporting documents uploaded by or for a student."""

    DOCUMENT_TYPES = [
        ('birth_certificate', 'Birth Certificate'),
        ('jamb_result', 'JAMB Result'),
        ('o_level_result', "O'Level Result"),
        ('a_level_result', "A'Level Result"),
        ('medical_report', 'Medical Report'),
        ('passport_photo', 'Passport Photograph'),
        ('transcript', 'Transcript'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='student_documents/', null=True, blank=True)
    notes = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_docs')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.student_id} — {self.title}"


# ─── Guardian ─────────────────────────────────────────────────────────────────

class Guardian(models.Model):
    RELATIONSHIP_CHOICES = [
        ('father', 'Father'), ('mother', 'Mother'),
        ('guardian', 'Guardian'), ('sibling', 'Sibling'), ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='guardian_profile',
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    occupation = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    students = models.ManyToManyField(StudentProfile, related_name='guardians', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.relationship})"


# ─── Audit Registration ───────────────────────────────────────────────────────
auditlog.register(StudentProfile)
auditlog.register(ClassRoom)
auditlog.register(Department)
auditlog.register(Programme)
auditlog.register(Faculty)
