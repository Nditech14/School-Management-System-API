"""
Academic Serializers
Covers: Course, Enrollment, CourseGrade, SemesterResult, CGPARecord,
        Subject (secondary), Grade (secondary), Attendance
"""
from decimal import Decimal
from rest_framework import serializers
from .models import (
    Course, Enrollment, CourseGrade, SemesterResult, CGPARecord,
    Subject, Grade, Attendance, compute_grade, classify_cgpa,
)


# ─── Subject (secondary school) ───────────────────────────────────────────────

class SubjectSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Subject
        fields = ['id', 'name', 'code', 'description', 'teacher', 'teacher_name',
                  'classes', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_code(self, value):
        return value.upper().strip()

    def get_teacher_name(self, obj):
        return obj.teacher.get_full_name() if obj.teacher else None


# ─── Course (university) ──────────────────────────────────────────────────────

class CourseSerializer(serializers.ModelSerializer):
    lecturer_name = serializers.SerializerMethodField(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    programme_name = serializers.CharField(source='programme.name', read_only=True)
    prerequisites_info = serializers.SerializerMethodField(read_only=True)
    enrolled_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'department', 'department_name', 'programme', 'programme_name',
            'name', 'code', 'description', 'credit_units',
            'level', 'semester', 'course_type',
            'lecturer', 'lecturer_name',
            'prerequisites', 'prerequisites_info',
            'is_active', 'enrolled_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_code(self, value):
        return value.upper().strip()

    def get_lecturer_name(self, obj):
        return obj.lecturer.get_full_name() if obj.lecturer else None

    def get_prerequisites_info(self, obj):
        return [{'id': str(p.id), 'code': p.code, 'name': p.name}
                for p in obj.prerequisites.all()]

    def get_enrolled_count(self, obj):
        return obj.enrollments.filter(status='enrolled').count()


class CourseListSerializer(serializers.ModelSerializer):
    """Lightweight course representation."""
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'code', 'name', 'credit_units', 'level',
                  'semester', 'course_type', 'department_name']


# ─── Enrollment ───────────────────────────────────────────────────────────────

class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField(read_only=True)
    student_id_no = serializers.CharField(source='student.student_id', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    credit_units = serializers.IntegerField(source='course.credit_units', read_only=True)
    session_name = serializers.CharField(source='academic_session.name', read_only=True)
    enrolled_by_name = serializers.SerializerMethodField(read_only=True)
    has_grade = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            'id', 'student', 'student_name', 'student_id_no',
            'course', 'course_code', 'course_name', 'credit_units',
            'academic_session', 'session_name', 'semester',
            'status', 'has_grade',
            'enrolled_by', 'enrolled_by_name',
            'enrolled_at', 'updated_at',
        ]
        read_only_fields = ['id', 'enrolled_by', 'enrolled_at', 'updated_at']

    def get_student_name(self, obj):
        return obj.student.user.get_full_name()

    def get_enrolled_by_name(self, obj):
        return obj.enrolled_by.get_full_name() if obj.enrolled_by else None

    def get_has_grade(self, obj):
        return hasattr(obj, 'grade')

    def validate(self, attrs):
        student = attrs.get('student')
        course = attrs.get('course')
        session = attrs.get('academic_session')
        semester = attrs.get('semester')

        # Check duplicate enrollment
        if self.instance is None:
            if Enrollment.objects.filter(
                student=student, course=course,
                academic_session=session, semester=semester
            ).exists():
                raise serializers.ValidationError(
                    f"Student is already enrolled in {course.code} for this session/semester."
                )

        # Check prerequisites
        if course and student:
            for prereq in course.prerequisites.all():
                completed = Enrollment.objects.filter(
                    student=student, course=prereq, status='completed'
                ).exists()
                if not completed:
                    raise serializers.ValidationError(
                        f"Prerequisite not met: {prereq.code} — {prereq.name} must be completed first."
                    )
        return attrs

    def create(self, validated_data):
        validated_data['enrolled_by'] = self.context['request'].user
        return super().create(validated_data)


class BulkEnrollmentSerializer(serializers.Serializer):
    """Enroll a student in multiple courses at once."""
    student = serializers.UUIDField()
    courses = serializers.ListField(child=serializers.UUIDField(), min_length=1)
    academic_session = serializers.UUIDField()
    semester = serializers.ChoiceField(choices=[('1st', '1st Semester'), ('2nd', '2nd Semester')])


# ─── Course Grade ─────────────────────────────────────────────────────────────

class CourseGradeSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField(read_only=True)
    student_id_no = serializers.SerializerMethodField(read_only=True)
    course_code = serializers.SerializerMethodField(read_only=True)
    course_name = serializers.SerializerMethodField(read_only=True)
    credit_units = serializers.SerializerMethodField(read_only=True)
    session_name = serializers.SerializerMethodField(read_only=True)
    semester = serializers.SerializerMethodField(read_only=True)
    recorded_by_name = serializers.SerializerMethodField(read_only=True)
    score_breakdown = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CourseGrade
        fields = [
            'id', 'enrollment',
            'student_name', 'student_id_no',
            'course_code', 'course_name', 'credit_units',
            'session_name', 'semester',
            'ca_score', 'assignment_score', 'exam_score',
            'total_score', 'grade_letter', 'grade_point', 'quality_point',
            'score_breakdown',
            'remarks', 'is_published',
            'recorded_by', 'recorded_by_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'total_score', 'grade_letter', 'grade_point', 'quality_point',
            'recorded_by', 'created_at', 'updated_at',
        ]

    def get_student_name(self, obj):
        return obj.enrollment.student.user.get_full_name()

    def get_student_id_no(self, obj):
        return obj.enrollment.student.student_id

    def get_course_code(self, obj):
        return obj.enrollment.course.code

    def get_course_name(self, obj):
        return obj.enrollment.course.name

    def get_credit_units(self, obj):
        return obj.enrollment.course.credit_units

    def get_session_name(self, obj):
        return obj.enrollment.academic_session.name

    def get_semester(self, obj):
        return obj.enrollment.semester

    def get_recorded_by_name(self, obj):
        return obj.recorded_by.get_full_name() if obj.recorded_by else None

    def get_score_breakdown(self, obj):
        return {
            'ca_score': float(obj.ca_score),
            'assignment_score': float(obj.assignment_score),
            'exam_score': float(obj.exam_score),
            'total': float(obj.total_score),
            'grade': obj.grade_letter,
            'grade_point': float(obj.grade_point),
        }

    def validate(self, attrs):
        ca = attrs.get('ca_score', Decimal('0'))
        assign = attrs.get('assignment_score', Decimal('0'))
        exam = attrs.get('exam_score', Decimal('0'))
        total = ca + assign + exam
        if total > 100:
            raise serializers.ValidationError("Total score cannot exceed 100.")
        return attrs

    def create(self, validated_data):
        validated_data['recorded_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['recorded_by'] = self.context['request'].user
        return super().update(instance, validated_data)


# ─── Semester Result ──────────────────────────────────────────────────────────

class SemesterResultSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField(read_only=True)
    student_id_no = serializers.CharField(source='student.student_id', read_only=True)
    session_name = serializers.CharField(source='academic_session.name', read_only=True)
    course_grades = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SemesterResult
        fields = [
            'id', 'student', 'student_name', 'student_id_no',
            'academic_session', 'session_name', 'semester',
            'total_credit_units_registered', 'total_credit_units_passed',
            'total_quality_points', 'gpa',
            'class_of_degree', 'is_on_probation',
            'course_grades', 'computed_at',
        ]
        read_only_fields = fields  # fully computed

    def get_student_name(self, obj):
        return obj.student.user.get_full_name()

    def get_course_grades(self, obj):
        enrollments = Enrollment.objects.filter(
            student=obj.student,
            academic_session=obj.academic_session,
            semester=obj.semester,
        ).select_related('course', 'grade')

        results = []
        for enr in enrollments:
            item = {
                'course_code': enr.course.code,
                'course_name': enr.course.name,
                'credit_units': enr.course.credit_units,
                'status': enr.status,
            }
            try:
                g = enr.grade
                item.update({
                    'ca_score': float(g.ca_score),
                    'assignment_score': float(g.assignment_score),
                    'exam_score': float(g.exam_score),
                    'total_score': float(g.total_score),
                    'grade_letter': g.grade_letter,
                    'grade_point': float(g.grade_point),
                    'quality_point': float(g.quality_point),
                    'is_published': g.is_published,
                })
            except CourseGrade.DoesNotExist:
                item.update({
                    'total_score': None,
                    'grade_letter': 'N/A',
                    'is_published': False,
                })
            results.append(item)
        return results


# ─── CGPA Record ─────────────────────────────────────────────────────────────

class CGPARecordSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField(read_only=True)
    student_id_no = serializers.CharField(source='student.student_id', read_only=True)
    department = serializers.SerializerMethodField(read_only=True)
    programme = serializers.SerializerMethodField(read_only=True)
    semester_breakdown = serializers.SerializerMethodField(read_only=True)
    honour_classification = serializers.CharField(source='class_of_degree', read_only=True)

    class Meta:
        model = CGPARecord
        fields = [
            'id', 'student', 'student_name', 'student_id_no',
            'department', 'programme',
            'total_credit_units_registered', 'total_credit_units_passed',
            'total_quality_points', 'cgpa', 'honour_classification',
            'semesters_completed',
            'semester_breakdown', 'computed_at',
        ]
        read_only_fields = fields

    def get_student_name(self, obj):
        return obj.student.user.get_full_name()

    def get_department(self, obj):
        if obj.student.department:
            return {'id': str(obj.student.department.id), 'name': obj.student.department.name}
        return None

    def get_programme(self, obj):
        if obj.student.programme:
            return {'id': str(obj.student.programme.id), 'name': obj.student.programme.name}
        return None

    def get_semester_breakdown(self, obj):
        results = SemesterResult.objects.filter(
            student=obj.student
        ).select_related('academic_session').order_by('academic_session__start_date', 'semester')

        return [
            {
                'session': r.academic_session.name,
                'semester': r.semester,
                'gpa': float(r.gpa),
                'credit_units_registered': r.total_credit_units_registered,
                'credit_units_passed': r.total_credit_units_passed,
                'quality_points': float(r.total_quality_points),
                'is_on_probation': r.is_on_probation,
            }
            for r in results
        ]


# ─── Transcript ───────────────────────────────────────────────────────────────

class TranscriptSerializer(serializers.Serializer):
    """Read-only full academic transcript for a student."""

    student = serializers.SerializerMethodField()
    programme = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    cgpa = serializers.DecimalField(max_digits=4, decimal_places=2)
    class_of_degree = serializers.CharField()
    total_credit_units_registered = serializers.IntegerField()
    total_credit_units_passed = serializers.IntegerField()
    semesters = serializers.SerializerMethodField()

    def get_student(self, obj):
        s = obj['student']
        return {
            'student_id': s.student_id,
            'full_name': s.user.get_full_name(),
            'email': s.user.email,
            'admission_date': s.admission_date,
            'entry_mode': s.entry_mode,
            'current_level': s.current_level,
            'status': s.status,
        }

    def get_programme(self, obj):
        p = obj['student'].programme
        return str(p) if p else None

    def get_department(self, obj):
        d = obj['student'].department
        return d.name if d else None

    def get_semesters(self, obj):
        return obj.get('semesters', [])


# ─── Secondary School Grade ───────────────────────────────────────────────────

class GradeSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField(read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = Grade
        fields = [
            'id', 'student', 'student_name', 'subject', 'subject_name',
            'academic_session', 'term',
            'ca_score', 'exam_score', 'total_score', 'grade_letter',
            'remarks', 'recorded_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'total_score', 'grade_letter', 'recorded_by',
                            'created_at', 'updated_at']

    def get_student_name(self, obj):
        return obj.student.user.get_full_name()

    def create(self, validated_data):
        validated_data['recorded_by'] = self.context['request'].user
        return super().create(validated_data)


# ─── Attendance ───────────────────────────────────────────────────────────────

class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField(read_only=True)
    course_code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id', 'student', 'student_name', 'date', 'status',
            'course', 'course_code', 'subject', 'notes',
            'marked_by', 'created_at',
        ]
        read_only_fields = ['id', 'marked_by', 'created_at']

    def get_student_name(self, obj):
        return obj.student.user.get_full_name()

    def get_course_code(self, obj):
        return obj.course.code if obj.course else None

    def create(self, validated_data):
        validated_data['marked_by'] = self.context['request'].user
        return super().create(validated_data)
