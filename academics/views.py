"""
Academic Views
Course, Enrollment (single + bulk), CourseGrade, SemesterResult,
CGPA, Transcript, Subject (secondary), Grade, Attendance
"""
import logging
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from core.permissions import IsAdminUser, IsAdminOrTeacher
from core.responses import APIResponse
from audit_trail.utils import log_action
from students.models import StudentProfile, AcademicSession
from .models import (
    Course, Enrollment, CourseGrade, SemesterResult, CGPARecord,
    Subject, Grade, Attendance,
)
from .serializers import (
    CourseSerializer, CourseListSerializer,
    EnrollmentSerializer, BulkEnrollmentSerializer,
    CourseGradeSerializer,
    SemesterResultSerializer,
    CGPARecordSerializer,
    TranscriptSerializer,
    SubjectSerializer,
    GradeSerializer,
    AttendanceSerializer,
)

audit_logger = logging.getLogger('school.audit')
logger = logging.getLogger('school.api')


# ─── Subjects (Secondary School) ─────────────────────────────────────────────

@extend_schema(tags=['Subjects'])
class SubjectListCreateView(generics.ListCreateAPIView):
    queryset = Subject.objects.select_related('teacher').all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active', 'teacher']
    search_fields = ['name', 'code']

    @extend_schema(summary='List subjects')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Create subject (Admin/Teacher)')
    def post(self, request, *args, **kwargs): return super().post(request, *args, **kwargs)


@extend_schema(tags=['Subjects'])
class SubjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'


# ─── Courses (University) ─────────────────────────────────────────────────────

@extend_schema(tags=['Courses'])
class CourseListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'programme', 'level', 'semester', 'course_type', 'is_active']
    search_fields = ['name', 'code', 'department__name']
    ordering_fields = ['code', 'level', 'credit_units']
    ordering = ['level', 'code']

    def get_queryset(self):
        return Course.objects.select_related('department', 'programme', 'lecturer').prefetch_related('prerequisites').all()

    def get_serializer_class(self):
        return CourseListSerializer if self.request.method == 'GET' else CourseSerializer

    @extend_schema(summary='List all courses', responses={200: CourseListSerializer(many=True)})
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Create course (Admin/Teacher)', request=CourseSerializer)
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        log_action(request.user, 'CREATE', 'Course', description='Course created', request=request)
        return response


@extend_schema(tags=['Courses'])
class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.select_related('department', 'programme', 'lecturer').prefetch_related('prerequisites').all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    lookup_field = 'id'

    @extend_schema(summary='Get course')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Update course (Admin/Teacher)')
    def put(self, request, *args, **kwargs): return super().put(request, *args, **kwargs)

    @extend_schema(summary='Partially update course')
    def patch(self, request, *args, **kwargs): return super().patch(request, *args, **kwargs)

    @extend_schema(summary='Delete course (Admin)')
    def delete(self, request, *args, **kwargs): return super().delete(request, *args, **kwargs)


# ─── Enrollment ───────────────────────────────────────────────────────────────

@extend_schema(tags=['Enrollments'])
class EnrollmentListCreateView(generics.ListCreateAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'course', 'academic_session', 'semester', 'status']
    search_fields = ['student__student_id', 'student__user__first_name', 'course__code']
    ordering_fields = ['enrolled_at', 'student__student_id']
    ordering = ['-enrolled_at']

    def get_queryset(self):
        return Enrollment.objects.select_related(
            'student__user', 'course', 'academic_session', 'enrolled_by'
        ).all()

    @extend_schema(summary='List all enrollments')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Enroll student in a course (Admin/Teacher)')
    def post(self, request, *args, **kwargs):
        serializer = EnrollmentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        enrollment = serializer.save()
        log_action(
            request.user, 'CREATE', 'Enrollment',
            enrollment.student.student_id,
            f"Enrolled in {enrollment.course.code} | {enrollment.academic_session} {enrollment.semester}",
            request=request,
        )
        return APIResponse.created(
            data=EnrollmentSerializer(enrollment, context={'request': request}).data,
            message=f"Student enrolled in {enrollment.course.code} successfully."
        )


@extend_schema(tags=['Enrollments'])
class EnrollmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Enrollment.objects.select_related('student__user', 'course', 'academic_session').all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    lookup_field = 'id'

    @extend_schema(summary='Get enrollment')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Update enrollment status (Admin/Teacher)')
    def patch(self, request, *args, **kwargs): return super().patch(request, *args, **kwargs)

    @extend_schema(summary='Drop enrollment (Admin)')
    def delete(self, request, *args, **kwargs):
        enr = self.get_object()
        log_action(request.user, 'DELETE', 'Enrollment', str(enr.id),
                   f"Dropped {enr.student.student_id} from {enr.course.code}", request=request)
        return super().delete(request, *args, **kwargs)


@extend_schema(tags=['Enrollments'])
class BulkEnrollView(APIView):
    """Enroll a student in multiple courses in a single request."""
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]

    @extend_schema(
        summary='Bulk enroll student in multiple courses',
        request=BulkEnrollmentSerializer,
        responses={201: EnrollmentSerializer(many=True)},
        examples=[
            OpenApiExample(
                'Bulk Enroll',
                value={
                    'student': '<student-uuid>',
                    'courses': ['<course-uuid-1>', '<course-uuid-2>'],
                    'academic_session': '<session-uuid>',
                    'semester': '1st',
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = BulkEnrollmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        student = get_object_or_404(StudentProfile, id=data['student'])
        session = get_object_or_404(AcademicSession, id=data['academic_session'])

        created = []
        skipped = []
        errors = []

        with transaction.atomic():
            for course_id in data['courses']:
                course = Course.objects.filter(id=course_id).first()
                if not course:
                    errors.append({'course_id': str(course_id), 'error': 'Course not found'})
                    continue

                exists = Enrollment.objects.filter(
                    student=student, course=course,
                    academic_session=session, semester=data['semester']
                ).exists()

                if exists:
                    skipped.append(course.code)
                    continue

                enr = Enrollment.objects.create(
                    student=student,
                    course=course,
                    academic_session=session,
                    semester=data['semester'],
                    enrolled_by=request.user,
                )
                created.append(enr)

        log_action(
            request.user, 'CREATE', 'Enrollment', student.student_id,
            f"Bulk enrolled: {len(created)} courses | skipped: {len(skipped)}", request=request,
        )

        return APIResponse.created(
            data={
                'enrolled': EnrollmentSerializer(created, many=True, context={'request': request}).data,
                'skipped_already_enrolled': skipped,
                'errors': errors,
                'summary': {
                    'total_requested': len(data['courses']),
                    'enrolled': len(created),
                    'skipped': len(skipped),
                    'errors': len(errors),
                },
            },
            message=f"Bulk enrollment complete: {len(created)} enrolled."
        )


@extend_schema(tags=['Enrollments'])
class StudentEnrollmentsView(generics.ListAPIView):
    """All enrollments for a specific student."""
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['academic_session', 'semester', 'status']

    @extend_schema(summary="List a student's enrollments")
    def get_queryset(self):
        return Enrollment.objects.filter(
            student_id=self.kwargs['student_id']
        ).select_related('course', 'academic_session').order_by('-enrolled_at')


# ─── Course Grades ────────────────────────────────────────────────────────────

@extend_schema(tags=['Grades — Courses'])
class CourseGradeListCreateView(generics.ListCreateAPIView):
    serializer_class = CourseGradeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['enrollment__student', 'enrollment__course',
                        'enrollment__academic_session', 'grade_letter', 'is_published']
    search_fields = ['enrollment__student__student_id',
                     'enrollment__student__user__first_name', 'enrollment__course__code']
    ordering_fields = ['total_score', 'created_at']

    def get_queryset(self):
        return CourseGrade.objects.select_related(
            'enrollment__student__user',
            'enrollment__course',
            'enrollment__academic_session',
            'recorded_by',
        ).all()

    @extend_schema(summary='List all course grades')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Record grade for a course enrollment (Admin/Teacher)')
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        audit_logger.info("Grade recorded by %s", request.user.email)
        return response


@extend_schema(tags=['Grades — Courses'])
class CourseGradeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CourseGrade.objects.select_related(
        'enrollment__student__user', 'enrollment__course', 'recorded_by'
    ).all()
    serializer_class = CourseGradeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    lookup_field = 'id'

    @extend_schema(summary='Get course grade')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Update course grade (Admin/Teacher)')
    def put(self, request, *args, **kwargs): return super().put(request, *args, **kwargs)

    @extend_schema(summary='Partially update grade')
    def patch(self, request, *args, **kwargs): return super().patch(request, *args, **kwargs)

    @extend_schema(summary='Delete grade (Admin only)')
    def delete(self, request, *args, **kwargs): return super().delete(request, *args, **kwargs)


@extend_schema(tags=['Grades — Courses'])
class GradesByCourseView(generics.ListAPIView):
    """All grades for a specific course (across all sessions)."""
    serializer_class = CourseGradeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['enrollment__academic_session', 'enrollment__semester', 'grade_letter']

    @extend_schema(summary="List grades for a specific course")
    def get_queryset(self):
        return CourseGrade.objects.filter(
            enrollment__course_id=self.kwargs['course_id']
        ).select_related('enrollment__student__user', 'enrollment__course')


@extend_schema(tags=['Grades — Courses'])
class PublishGradesView(APIView):
    """Publish all grades for a course/session/semester (make visible to students)."""
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]

    @extend_schema(
        summary='Publish grades for a course (Admin/Teacher)',
        parameters=[
            OpenApiParameter('course_id', description='Course UUID'),
            OpenApiParameter('session_id', description='Academic Session UUID'),
            OpenApiParameter('semester', description='e.g. 1st or 2nd'),
        ],
    )
    def post(self, request, course_id, session_id, semester):
        updated = CourseGrade.objects.filter(
            enrollment__course_id=course_id,
            enrollment__academic_session_id=session_id,
            enrollment__semester=semester,
        ).update(is_published=True)

        audit_logger.info("Grades published for course %s session %s %s by %s",
                          course_id, session_id, semester, request.user.email)
        return APIResponse.success(
            message=f"{updated} grade(s) published successfully."
        )


# ─── Semester Results ─────────────────────────────────────────────────────────

@extend_schema(tags=['Semester Results'])
class SemesterResultListView(generics.ListAPIView):
    serializer_class = SemesterResultSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'academic_session', 'semester', 'is_on_probation']
    ordering_fields = ['gpa', 'computed_at']

    def get_queryset(self):
        return SemesterResult.objects.select_related(
            'student__user', 'academic_session'
        ).all()

    @extend_schema(summary='List semester results (GPA per session/semester)')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)


@extend_schema(tags=['Semester Results'])
class StudentSemesterResultsView(generics.ListAPIView):
    """All semester results for a specific student."""
    serializer_class = SemesterResultSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]

    @extend_schema(summary="List all semester results for a student")
    def get_queryset(self):
        return SemesterResult.objects.filter(
            student_id=self.kwargs['student_id']
        ).select_related('academic_session').order_by('academic_session__start_date', 'semester')


@extend_schema(tags=['Semester Results'])
class RecomputeSemesterResultView(APIView):
    """Force-recompute a student's semester GPA."""
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(summary='Recompute semester GPA for a student (Admin)')
    def post(self, request, student_id, session_id, semester):
        student = get_object_or_404(StudentProfile, id=student_id)
        session = get_object_or_404(AcademicSession, id=session_id)
        result = SemesterResult.recompute(student=student, academic_session=session, semester=semester)
        return APIResponse.success(
            data=SemesterResultSerializer(result).data,
            message='Semester result recomputed.'
        )


# ─── CGPA ─────────────────────────────────────────────────────────────────────

@extend_schema(tags=['CGPA'])
class StudentCGPAView(APIView):
    """Get (or recompute) a student's CGPA."""
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]

    @extend_schema(
        summary='Get student CGPA (auto-recomputes from all semester results)',
        parameters=[OpenApiParameter('student_id', description='Student UUID')],
        responses={200: CGPARecordSerializer},
    )
    def get(self, request, student_id):
        student = get_object_or_404(
            StudentProfile.objects.select_related('user', 'department', 'programme'),
            id=student_id,
        )
        # Always recompute fresh
        cgpa = CGPARecord.recompute(student)
        return APIResponse.success(
            data=CGPARecordSerializer(cgpa).data,
            message='CGPA computed successfully.'
        )


@extend_schema(tags=['CGPA'])
class CGPALeaderboardView(generics.ListAPIView):
    """Top students by CGPA — optionally filtered by department or programme."""
    serializer_class = CGPARecordSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend]  # removed OrderingFilter — causes slice conflict

    @extend_schema(
        summary='CGPA leaderboard (top students)',
        parameters=[
            OpenApiParameter('department', description='Filter by department UUID'),
            OpenApiParameter('programme', description='Filter by programme UUID'),
            OpenApiParameter('limit', description='Max results (default 20)'),
        ],
    )
    def get_queryset(self):
        qs = CGPARecord.objects.select_related(
            'student__user', 'student__department', 'student__programme'
        ).order_by('-cgpa')  # ✅ order here BEFORE any slice

        dept = self.request.query_params.get('department')
        prog = self.request.query_params.get('programme')

        if dept:
            qs = qs.filter(student__department_id=dept)
        if prog:
            qs = qs.filter(student__programme_id=prog)

        return qs  # ✅ NO slice here

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # ✅ Slice AFTER filtering and ordering — safe now
        try:
            limit = int(request.query_params.get('limit', 20))
            if limit < 1 or limit > 100:
                limit = 20
        except (ValueError, TypeError):
            limit = 20

        queryset = queryset[:limit]
        serializer = self.get_serializer(queryset, many=True)

        return APIResponse.success(
            data=serializer.data,
            message=f'Top {limit} students by CGPA.'
        )


# ─── Transcript ───────────────────────────────────────────────────────────────

@extend_schema(tags=['Transcript'])
class StudentTranscriptView(APIView):
    """Full academic transcript for a student — all sessions, all courses, CGPA."""
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]

    @extend_schema(
        summary='Get full academic transcript for a student',
        responses={200: TranscriptSerializer},
    )
    def get(self, request, student_id):
        student = get_object_or_404(
            StudentProfile.objects.select_related('user', 'department', 'programme'),
            id=student_id,
        )

        # Ensure CGPA is up to date
        cgpa_record = CGPARecord.recompute(student)

        # Build per-semester detail
        semester_results = SemesterResult.objects.filter(
            student=student
        ).select_related('academic_session').order_by('academic_session__start_date', 'semester')

        semesters = []
        for sr in semester_results:
            enrollments = Enrollment.objects.filter(
                student=student,
                academic_session=sr.academic_session,
                semester=sr.semester,
            ).select_related('course', 'grade')

            courses = []
            for enr in enrollments:
                row = {
                    'course_code': enr.course.code,
                    'course_name': enr.course.name,
                    'credit_units': enr.course.credit_units,
                    'status': enr.status,
                }
                try:
                    g = enr.grade
                    row.update({
                        'ca_score': float(g.ca_score),
                        'assignment_score': float(g.assignment_score),
                        'exam_score': float(g.exam_score),
                        'total_score': float(g.total_score),
                        'grade_letter': g.grade_letter,
                        'grade_point': float(g.grade_point),
                        'quality_point': float(g.quality_point),
                    })
                except CourseGrade.DoesNotExist:
                    row.update({'total_score': None, 'grade_letter': 'N/A'})
                courses.append(row)

            semesters.append({
                'session': sr.academic_session.name,
                'semester': sr.semester,
                'gpa': float(sr.gpa),
                'credit_units_registered': sr.total_credit_units_registered,
                'credit_units_passed': sr.total_credit_units_passed,
                'quality_points': float(sr.total_quality_points),
                'is_on_probation': sr.is_on_probation,
                'courses': courses,
            })

        data = {
            'student': student,
            'cgpa': cgpa_record.cgpa,
            'class_of_degree': cgpa_record.class_of_degree,
            'total_credit_units_registered': cgpa_record.total_credit_units_registered,
            'total_credit_units_passed': cgpa_record.total_credit_units_passed,
            'semesters': semesters,
        }

        return APIResponse.success(
            data=TranscriptSerializer(data).data,
            message='Transcript generated successfully.'
        )


# ─── Secondary School Grades ─────────────────────────────────────────────────

@extend_schema(tags=['Grades — Term (Secondary)'])
class GradeListCreateView(generics.ListCreateAPIView):
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'subject', 'academic_session', 'term', 'grade_letter']
    search_fields = ['student__student_id', 'student__user__first_name']
    ordering_fields = ['total_score', 'created_at']

    def get_queryset(self):
        return Grade.objects.select_related(
            'student__user', 'subject', 'academic_session', 'recorded_by'
        ).all()

    @extend_schema(summary='List term grades')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Record term grade (Admin/Teacher)')
    def post(self, request, *args, **kwargs): return super().post(request, *args, **kwargs)


@extend_schema(tags=['Grades — Term (Secondary)'])
class GradeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Grade.objects.select_related('student__user', 'subject').all()
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    lookup_field = 'id'


# ─── Attendance ───────────────────────────────────────────────────────────────

@extend_schema(tags=['Attendance'])
class AttendanceListCreateView(generics.ListCreateAPIView):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'date', 'status', 'course', 'subject']
    ordering_fields = ['date']

    def get_queryset(self):
        return Attendance.objects.select_related(
            'student__user', 'course', 'subject', 'marked_by'
        ).all()

    @extend_schema(summary='List attendance records')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Mark attendance (Admin/Teacher)')
    def post(self, request, *args, **kwargs): return super().post(request, *args, **kwargs)


@extend_schema(tags=['Attendance'])
class AttendanceDetailView(generics.RetrieveUpdateAPIView):
    queryset = Attendance.objects.select_related('student__user').all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    lookup_field = 'id'
