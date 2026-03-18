"""
Student Views
Faculty, Department, Programme, ClassRoom, AcademicSession,
Student CRUD, StudentDocuments, Guardians
"""
import logging
from django.contrib.auth import get_user_model
from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.permissions import IsAdminUser, IsAdminOrTeacher
from core.responses import APIResponse
from audit_trail.utils import log_action
from .models import (
    Faculty, Department, Programme, ClassRoom, AcademicSession,
    StudentProfile, StudentDocument, Guardian,
)
from .serializers import (
    FacultySerializer, DepartmentSerializer, DepartmentListSerializer,
    ProgrammeSerializer, ClassRoomSerializer, AcademicSessionSerializer,
    StudentProfileSerializer, StudentListSerializer, StudentDetailSerializer,
    StudentDocumentSerializer, GuardianSerializer,
)

User = get_user_model()
logger = logging.getLogger('school.api')
audit_logger = logging.getLogger('school.audit')


# ─── Academic Session ─────────────────────────────────────────────────────────

@extend_schema(tags=['Academic Sessions'])
class AcademicSessionListCreateView(generics.ListCreateAPIView):
    queryset = AcademicSession.objects.all()
    serializer_class = AcademicSessionSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]

    @extend_schema(summary='List all academic sessions')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Create academic session (Admin/Teacher)')
    def post(self, request, *args, **kwargs): return super().post(request, *args, **kwargs)


@extend_schema(tags=['Academic Sessions'])
class AcademicSessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AcademicSession.objects.all()
    serializer_class = AcademicSessionSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'

    @extend_schema(summary='Get academic session')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Update academic session (Admin)')
    def put(self, request, *args, **kwargs): return super().put(request, *args, **kwargs)

    @extend_schema(summary='Delete academic session (Admin)')
    def delete(self, request, *args, **kwargs): return super().delete(request, *args, **kwargs)


# ─── Faculty ──────────────────────────────────────────────────────────────────

@extend_schema(tags=['Faculties'])
class FacultyListCreateView(generics.ListCreateAPIView):
    queryset = Faculty.objects.prefetch_related('departments').all()
    serializer_class = FacultySerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code']

    @extend_schema(summary='List all faculties')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Create faculty (Admin/Teacher)')
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        log_action(request.user, 'CREATE', 'Faculty', description='Faculty created', request=request)
        return response


@extend_schema(tags=['Faculties'])
class FacultyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Faculty.objects.prefetch_related('departments').all()
    serializer_class = FacultySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'

    @extend_schema(summary='Get faculty')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Update faculty (Admin)')
    def put(self, request, *args, **kwargs): return super().put(request, *args, **kwargs)

    @extend_schema(summary='Partially update faculty (Admin)')
    def patch(self, request, *args, **kwargs): return super().patch(request, *args, **kwargs)

    @extend_schema(summary='Delete faculty (Admin)')
    def delete(self, request, *args, **kwargs): return super().delete(request, *args, **kwargs)


@extend_schema(tags=['Faculties'])
class FacultyDepartmentsView(generics.ListAPIView):
    """List all departments under a specific faculty."""
    serializer_class = DepartmentListSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(summary='List departments in a faculty')
    def get_queryset(self):
        return Department.objects.filter(
            faculty_id=self.kwargs['id'], is_active=True
        ).select_related('faculty')


# ─── Department ───────────────────────────────────────────────────────────────

@extend_schema(tags=['Departments'])
class DepartmentListCreateView(generics.ListCreateAPIView):
    queryset = Department.objects.select_related('faculty', 'hod').all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['faculty', 'is_active']
    search_fields = ['name', 'code', 'faculty__name']
    ordering_fields = ['name', 'code']

    @extend_schema(summary='List all departments')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Create department (Admin)')
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        log_action(request.user, 'CREATE', 'Department', description='Department created', request=request)
        return response


@extend_schema(tags=['Departments'])
class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Department.objects.select_related('faculty', 'hod').all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'

    @extend_schema(summary='Get department')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Update department (Admin)')
    def put(self, request, *args, **kwargs): return super().put(request, *args, **kwargs)

    @extend_schema(summary='Partially update department (Admin)')
    def patch(self, request, *args, **kwargs): return super().patch(request, *args, **kwargs)

    @extend_schema(summary='Delete department (Admin)')
    def delete(self, request, *args, **kwargs): return super().delete(request, *args, **kwargs)


# ─── Programme ────────────────────────────────────────────────────────────────

@extend_schema(tags=['Programmes'])
class ProgrammeListCreateView(generics.ListCreateAPIView):
    queryset = Programme.objects.select_related('department__faculty').all()
    serializer_class = ProgrammeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'degree_type', 'is_active']
    search_fields = ['name', 'code', 'department__name']
    ordering_fields = ['name', 'code', 'degree_type']

    @extend_schema(summary='List all programmes')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Create programme (Admin)')
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        log_action(request.user, 'CREATE', 'Programme', description='Programme created', request=request)
        return response


@extend_schema(tags=['Programmes'])
class ProgrammeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Programme.objects.select_related('department__faculty').all()
    serializer_class = ProgrammeSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'

    @extend_schema(summary='Get programme')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Update programme (Admin)')
    def put(self, request, *args, **kwargs): return super().put(request, *args, **kwargs)

    @extend_schema(summary='Delete programme (Admin)')
    def delete(self, request, *args, **kwargs): return super().delete(request, *args, **kwargs)


# ─── Classroom ────────────────────────────────────────────────────────────────

@extend_schema(tags=['Classrooms'])
class ClassRoomListCreateView(generics.ListCreateAPIView):
    queryset = ClassRoom.objects.select_related('class_teacher').all()
    serializer_class = ClassRoomSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['grade_level']
    search_fields = ['name', 'grade_level']

    @extend_schema(summary='List classrooms')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Create classroom (Admin/Teacher)')
    def post(self, request, *args, **kwargs): return super().post(request, *args, **kwargs)


@extend_schema(tags=['Classrooms'])
class ClassRoomDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ClassRoom.objects.all()
    serializer_class = ClassRoomSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'


# ─── Students ────────────────────────────────────────────────────────────────

@extend_schema(tags=['Students'])
class StudentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'gender', 'is_active', 'status', 'current_class',
        'department', 'programme', 'current_level', 'entry_mode',
    ]
    search_fields = [
        'student_id', 'user__first_name', 'user__last_name',
        'user__email', 'jamb_registration_number',
    ]
    ordering_fields = ['student_id', 'admission_date', 'user__first_name', 'current_level']
    ordering = ['student_id']

    def get_queryset(self):
        return StudentProfile.objects.select_related(
            'user', 'current_class', 'department__faculty', 'programme'
        ).all()

    def get_serializer_class(self):
        return StudentListSerializer if self.request.method == 'GET' else StudentProfileSerializer

    @extend_schema(summary='List all students', responses={200: StudentListSerializer(many=True)})
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Register new student (Admin/Teacher)', request=StudentProfileSerializer)
    def post(self, request, *args, **kwargs):
        serializer = StudentProfileSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        log_action(
            request.user, 'CREATE', 'Student', student.student_id,
            f"Student {student.student_id} registered", request=request,
        )
        return APIResponse.created(
            data=StudentDetailSerializer(student, context={'request': request}).data,
            message='Student registered successfully.',
        )


@extend_schema(tags=['Students'])
class StudentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = StudentProfile.objects.select_related(
        'user', 'current_class', 'department__faculty', 'programme'
    ).prefetch_related('guardians', 'documents').all()
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StudentDetailSerializer
        return StudentProfileSerializer

    @extend_schema(summary='Get full student record (with guardians & documents)')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Update student record (Admin/Teacher)')
    def put(self, request, *args, **kwargs):
        student = self.get_object()
        response = super().put(request, *args, **kwargs)
        log_action(request.user, 'UPDATE', 'Student', student.student_id,
                   'Student record updated', request=request)
        return response

    @extend_schema(summary='Partially update student (Admin/Teacher)')
    def patch(self, request, *args, **kwargs): return super().patch(request, *args, **kwargs)

    @extend_schema(summary='Delete student (Admin only)')
    def delete(self, request, *args, **kwargs):
        student = self.get_object()
        log_action(request.user, 'DELETE', 'Student', student.student_id,
                   'Student deleted', request=request)
        return super().delete(request, *args, **kwargs)


@extend_schema(tags=['Students'])
class StudentByStudentIdView(generics.RetrieveAPIView):
    """Lookup a student by their student_id string (e.g. STU/2024/001)."""
    serializer_class = StudentDetailSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    lookup_field = 'student_id'
    queryset = StudentProfile.objects.select_related(
        'user', 'department', 'programme', 'current_class'
    ).prefetch_related('guardians', 'documents').all()

    @extend_schema(summary='Get student by student_id')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)


# ─── Student Documents ───────────────────────────────────────────────────────

@extend_schema(tags=['Student Documents'])
class StudentDocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = StudentDocumentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['document_type', 'student']

    def get_queryset(self):
        return StudentDocument.objects.filter(
            student_id=self.kwargs['student_id']
        ).select_related('uploaded_by')

    @extend_schema(summary="List a student's documents")
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary="Upload document for student (Admin/Teacher)")
    def post(self, request, *args, **kwargs):
        request.data._mutable = True if hasattr(request.data, '_mutable') else None
        request.data['student'] = str(kwargs['student_id'])
        return super().post(request, *args, **kwargs)


@extend_schema(tags=['Student Documents'])
class StudentDocumentDetailView(generics.RetrieveDestroyAPIView):
    queryset = StudentDocument.objects.all()
    serializer_class = StudentDocumentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    lookup_field = 'id'

    @extend_schema(summary='Get document')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Delete document (Admin only)')
    def delete(self, request, *args, **kwargs): return super().delete(request, *args, **kwargs)


# ─── Guardians ───────────────────────────────────────────────────────────────

@extend_schema(tags=['Guardians'])
class GuardianListCreateView(generics.ListCreateAPIView):
    queryset = Guardian.objects.all()
    serializer_class = GuardianSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'email', 'phone_number']

    @extend_schema(summary='List guardians')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Add guardian')
    def post(self, request, *args, **kwargs): return super().post(request, *args, **kwargs)


@extend_schema(tags=['Guardians'])
class GuardianDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Guardian.objects.all()
    serializer_class = GuardianSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    lookup_field = 'id'

    @extend_schema(summary='Get guardian')
    def get(self, request, *args, **kwargs): return super().get(request, *args, **kwargs)

    @extend_schema(summary='Update guardian')
    def put(self, request, *args, **kwargs): return super().put(request, *args, **kwargs)

    @extend_schema(summary='Delete guardian (Admin)')
    def delete(self, request, *args, **kwargs): return super().delete(request, *args, **kwargs)
