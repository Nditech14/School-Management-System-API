from django.urls import path
from .views import (
    AcademicSessionListCreateView, AcademicSessionDetailView,
    FacultyListCreateView, FacultyDetailView, FacultyDepartmentsView,
    DepartmentListCreateView, DepartmentDetailView,
    ProgrammeListCreateView, ProgrammeDetailView,
    ClassRoomListCreateView, ClassRoomDetailView,
    StudentListCreateView, StudentDetailView, StudentByStudentIdView,
    StudentDocumentListCreateView, StudentDocumentDetailView,
    GuardianListCreateView, GuardianDetailView,
)

urlpatterns = [
    # Academic Sessions
    path('academic-sessions/', AcademicSessionListCreateView.as_view(), name='academic-session-list'),
    path('academic-sessions/<uuid:id>/', AcademicSessionDetailView.as_view(), name='academic-session-detail'),

    # Faculties
    path('faculties/', FacultyListCreateView.as_view(), name='faculty-list'),
    path('faculties/<uuid:id>/', FacultyDetailView.as_view(), name='faculty-detail'),
    path('faculties/<uuid:id>/departments/', FacultyDepartmentsView.as_view(), name='faculty-departments'),

    # Departments
    path('departments/', DepartmentListCreateView.as_view(), name='department-list'),
    path('departments/<uuid:id>/', DepartmentDetailView.as_view(), name='department-detail'),

    # Programmes
    path('programmes/', ProgrammeListCreateView.as_view(), name='programme-list'),
    path('programmes/<uuid:id>/', ProgrammeDetailView.as_view(), name='programme-detail'),

    # Classrooms
    path('classrooms/', ClassRoomListCreateView.as_view(), name='classroom-list'),
    path('classrooms/<uuid:id>/', ClassRoomDetailView.as_view(), name='classroom-detail'),

    # Students
    path('students/', StudentListCreateView.as_view(), name='student-list'),
    path('students/<uuid:id>/', StudentDetailView.as_view(), name='student-detail'),
    path('students/by-id/<str:student_id>/', StudentByStudentIdView.as_view(), name='student-by-student-id'),

    # Student Documents
    path('students/<uuid:student_id>/documents/', StudentDocumentListCreateView.as_view(), name='student-documents'),
    path('documents/<uuid:id>/', StudentDocumentDetailView.as_view(), name='student-document-detail'),

    # Guardians
    path('guardians/', GuardianListCreateView.as_view(), name='guardian-list'),
    path('guardians/<uuid:id>/', GuardianDetailView.as_view(), name='guardian-detail'),
]
