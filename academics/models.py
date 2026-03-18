"""
Academic Models — Course, Enrollment, CourseGrade, SemesterResult,
                  CGPA Engine, Transcript, Attendance, Legacy Term Grades.

Grading Scale (Nigerian University Standard):
  A  = 70–100  → 5.0 GP
  B  = 60–69   → 4.0 GP
  C  = 50–59   → 3.0 GP
  D  = 45–49   → 2.0 GP
  E  = 40–44   → 1.0 GP
  F  = 0–39    → 0.0 GP
"""
import uuid
from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from students.models import StudentProfile, ClassRoom, AcademicSession, Department, Programme
from auditlog.registry import auditlog

User = get_user_model()


# ─── Grade Point Helpers ──────────────────────────────────────────────────────

GRADE_SCALE = [
    (70, 'A', Decimal('5.0')),
    (60, 'B', Decimal('4.0')),
    (50, 'C', Decimal('3.0')),
    (45, 'D', Decimal('2.0')),
    (40, 'E', Decimal('1.0')),
    (0,  'F', Decimal('0.0')),
]


def compute_grade(score: float):
    """Return (letter, grade_point) for a given percentage score."""
    for threshold, letter, gp in GRADE_SCALE:
        if score >= threshold:
            return letter, gp
    return 'F', Decimal('0.0')


def classify_cgpa(cgpa: Decimal) -> str:
    """Return class-of-degree string from a CGPA value."""
    v = float(cgpa)
    if v >= 4.50: return 'First Class Honours'
    if v >= 3.50: return 'Second Class Upper'
    if v >= 2.40: return 'Second Class Lower'
    if v >= 1.50: return 'Third Class'
    if v >= 1.00: return 'Pass'
    return 'Fail'


# ─── Subject (secondary school — no credit units) ────────────────────────────

class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        limit_choices_to={'role': 'teacher'}, related_name='subjects_taught',
    )
    classes = models.ManyToManyField(ClassRoom, related_name='subjects', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


# ─── Course (university — has credit units) ───────────────────────────────────

class Course(models.Model):
    """University/polytechnic course with credit unit weight."""

    COURSE_TYPE_CHOICES = [
        ('core', 'Core / Compulsory'),
        ('elective', 'Elective'),
        ('general', 'General Studies'),
        ('prerequisite', 'Prerequisite'),
    ]

    SEMESTER_CHOICES = [
        ('1st', '1st Semester'),
        ('2nd', '2nd Semester'),
        ('both', 'Both Semesters'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    programme = models.ForeignKey(
        Programme, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses',
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=15, unique=True)
    description = models.TextField(blank=True)
    credit_units = models.PositiveSmallIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        help_text='Credit units (weight) for CGPA calculation',
    )
    level = models.CharField(max_length=10, blank=True, help_text='e.g. 100, 200, 300, 400, 500')
    semester = models.CharField(max_length=5, choices=SEMESTER_CHOICES, default='1st')
    course_type = models.CharField(max_length=15, choices=COURSE_TYPE_CHOICES, default='core')
    lecturer = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        limit_choices_to={'role': 'teacher'}, related_name='courses_lecturing',
    )
    prerequisites = models.ManyToManyField(
        'self', symmetrical=False, blank=True, related_name='required_for',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['level', 'code']

    def __str__(self):
        return f"{self.code} — {self.name} ({self.credit_units} CU)"


# ─── Enrollment ───────────────────────────────────────────────────────────────

class Enrollment(models.Model):
    """A student enrolling in a course for a specific session/semester."""

    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('dropped', 'Dropped'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('deferred', 'Deferred'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    academic_session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='enrollments')
    semester = models.CharField(max_length=5, choices=Course.SEMESTER_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='enrolled')
    enrolled_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollments_created',
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'course', 'academic_session', 'semester']
        ordering = ['-enrolled_at']

    def __str__(self):
        return (
            f"{self.student.student_id} → {self.course.code} "
            f"| {self.academic_session} {self.semester}"
        )


# ─── Course Grade ─────────────────────────────────────────────────────────────

class CourseGrade(models.Model):
    """
    Grade for one enrolled course.
    Auto-computes total, grade letter, grade point, and quality point.
    Triggers SemesterResult recomputation on save.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='grade')

    ca_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0'),
        validators=[MinValueValidator(0), MaxValueValidator(30)],
        verbose_name='CA Score', help_text='Continuous Assessment (max 30)',
    )
    assignment_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0'),
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text='Assignment / Quiz (max 10)',
    )
    exam_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0'),
        validators=[MinValueValidator(0), MaxValueValidator(60)],
        help_text='Examination Score (max 60)',
    )

    # Auto-computed
    total_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'), editable=False)
    grade_letter = models.CharField(max_length=2, default='F', editable=False)
    grade_point = models.DecimalField(max_digits=3, decimal_places=1, default=Decimal('0.0'), editable=False)
    quality_point = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal('0'), editable=False,
        help_text='grade_point × credit_units',
    )

    remarks = models.CharField(max_length=200, blank=True)
    is_published = models.BooleanField(default=False, help_text='Visible to student once published')
    recorded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='course_grades_recorded',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        self.total_score = self.ca_score + self.assignment_score + self.exam_score
        self.grade_letter, self.grade_point = compute_grade(float(self.total_score))
        self.quality_point = self.grade_point * self.enrollment.course.credit_units
        super().save(*args, **kwargs)

        # Update enrollment status
        self.enrollment.status = 'failed' if self.grade_letter == 'F' else 'completed'
        self.enrollment.save(update_fields=['status'])

        # Trigger semester result recomputation
        SemesterResult.recompute(
            student=self.enrollment.student,
            academic_session=self.enrollment.academic_session,
            semester=self.enrollment.semester,
        )

    def __str__(self):
        return (
            f"{self.enrollment.student.student_id} | "
            f"{self.enrollment.course.code} | "
            f"{self.grade_letter} ({self.total_score})"
        )


# ─── Semester Result ──────────────────────────────────────────────────────────

class SemesterResult(models.Model):
    """
    Computed GPA summary for a student per session/semester.
    Auto-recomputed whenever a CourseGrade is saved.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='semester_results')
    academic_session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    semester = models.CharField(max_length=5, choices=Course.SEMESTER_CHOICES)

    total_credit_units_registered = models.PositiveIntegerField(default=0)
    total_credit_units_passed = models.PositiveIntegerField(default=0)
    total_quality_points = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0'))
    gpa = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))

    class_of_degree = models.CharField(max_length=50, blank=True, editable=False)
    is_on_probation = models.BooleanField(default=False, editable=False)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'academic_session', 'semester']
        ordering = ['-academic_session__start_date', 'semester']

    def __str__(self):
        return f"{self.student.student_id} | {self.academic_session} {self.semester} | GPA={self.gpa}"

    @classmethod
    def recompute(cls, student, academic_session, semester):
        """Recompute and upsert the SemesterResult for a student/session/semester."""
        enrollments = Enrollment.objects.filter(
            student=student,
            academic_session=academic_session,
            semester=semester,
            status__in=['completed', 'failed'],
        ).select_related('course', 'grade')

        total_cu = 0
        passed_cu = 0
        total_qp = Decimal('0')

        for enr in enrollments:
            cu = enr.course.credit_units
            total_cu += cu
            try:
                grade = enr.grade
                total_qp += grade.quality_point
                if grade.grade_letter not in ('F', 'E'):
                    passed_cu += cu
            except CourseGrade.DoesNotExist:
                pass

        gpa = (total_qp / total_cu).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if total_cu else Decimal('0.00')

        obj, _ = cls.objects.update_or_create(
            student=student,
            academic_session=academic_session,
            semester=semester,
            defaults={
                'total_credit_units_registered': total_cu,
                'total_credit_units_passed': passed_cu,
                'total_quality_points': total_qp,
                'gpa': gpa,
                'class_of_degree': classify_cgpa(gpa),
                'is_on_probation': float(gpa) < 1.0,
            },
        )
        return obj


# ─── CGPA Record ─────────────────────────────────────────────────────────────

class CGPARecord(models.Model):
    """
    Cumulative GPA record for a student — computed across ALL completed semesters.
    Updated automatically when SemesterResult changes.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='cgpa_record')

    total_credit_units_registered = models.PositiveIntegerField(default=0)
    total_credit_units_passed = models.PositiveIntegerField(default=0)
    total_quality_points = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    class_of_degree = models.CharField(max_length=50, blank=True)
    semesters_completed = models.PositiveIntegerField(default=0)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-cgpa']

    def __str__(self):
        return f"{self.student.student_id} | CGPA={self.cgpa} | {self.class_of_degree}"

    @classmethod
    def recompute(cls, student):
        """Aggregate all semester results to produce CGPA."""
        agg = SemesterResult.objects.filter(student=student).aggregate(
            total_cu=Sum('total_credit_units_registered'),
            total_qp=Sum('total_quality_points'),
            passed_cu=Sum('total_credit_units_passed'),
            count=models.Count('id'),
        )

        total_cu = agg['total_cu'] or 0
        total_qp = agg['total_qp'] or Decimal('0')
        passed_cu = agg['passed_cu'] or 0
        semesters = agg['count'] or 0

        cgpa = (total_qp / total_cu).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if total_cu else Decimal('0.00')

        obj, _ = cls.objects.update_or_create(
            student=student,
            defaults={
                'total_credit_units_registered': total_cu,
                'total_credit_units_passed': passed_cu,
                'total_quality_points': total_qp,
                'cgpa': cgpa,
                'class_of_degree': classify_cgpa(cgpa),
                'semesters_completed': semesters,
            },
        )
        return obj


# ─── Legacy Term-Based Grade (Secondary School) ───────────────────────────────

class Grade(models.Model):
    """Secondary/primary school term-based grade (no credit units)."""

    TERM_CHOICES = [('1st', '1st Term'), ('2nd', '2nd Term'), ('3rd', '3rd Term')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='term_grades')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grades')
    academic_session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='term_grades')
    term = models.CharField(max_length=5, choices=TERM_CHOICES)
    ca_score = models.DecimalField(max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(40)])
    exam_score = models.DecimalField(max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(60)])
    total_score = models.DecimalField(max_digits=5, decimal_places=2, editable=False, default=0)
    grade_letter = models.CharField(max_length=2, editable=False)
    remarks = models.CharField(max_length=100, blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='term_grades_recorded')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'subject', 'academic_session', 'term']
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        self.total_score = self.ca_score + self.exam_score
        self.grade_letter, _ = compute_grade(float(self.total_score))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} | {self.subject.code} | {self.term}"


# ─── Attendance ───────────────────────────────────────────────────────────────

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'), ('absent', 'Absent'),
        ('late', 'Late'), ('excused', 'Excused'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='attendances')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True, related_name='attendances')
    notes = models.CharField(max_length=255, blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='attendances_marked')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.student} | {self.date} | {self.status}"


# ─── Audit Registration ───────────────────────────────────────────────────────
auditlog.register(Course)
auditlog.register(Enrollment)
auditlog.register(CourseGrade)
auditlog.register(CGPARecord)
auditlog.register(Grade)
