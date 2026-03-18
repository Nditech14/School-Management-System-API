from django.urls import path
from .views import (
    SubjectListCreateView, SubjectDetailView,
    CourseListCreateView, CourseDetailView,
    EnrollmentListCreateView, EnrollmentDetailView,
    BulkEnrollView, StudentEnrollmentsView,
    CourseGradeListCreateView, CourseGradeDetailView,
    GradesByCourseView, PublishGradesView,
    SemesterResultListView, StudentSemesterResultsView, RecomputeSemesterResultView,
    StudentCGPAView, CGPALeaderboardView,
    StudentTranscriptView,
    GradeListCreateView, GradeDetailView,
    AttendanceListCreateView, AttendanceDetailView,
)

urlpatterns = [
    # Subjects (secondary school)
    path('subjects/', SubjectListCreateView.as_view(), name='subject-list'),
    path('subjects/<uuid:id>/', SubjectDetailView.as_view(), name='subject-detail'),

    # Courses (university/polytechnic)
    path('courses/', CourseListCreateView.as_view(), name='course-list'),
    path('courses/<uuid:id>/', CourseDetailView.as_view(), name='course-detail'),

    # Enrollments
    path('enrollments/', EnrollmentListCreateView.as_view(), name='enrollment-list'),
    path('enrollments/bulk/', BulkEnrollView.as_view(), name='enrollment-bulk'),
    path('enrollments/<uuid:id>/', EnrollmentDetailView.as_view(), name='enrollment-detail'),
    path('students/<uuid:student_id>/enrollments/', StudentEnrollmentsView.as_view(), name='student-enrollments'),

    # Course Grades
    path('course-grades/', CourseGradeListCreateView.as_view(), name='course-grade-list'),
    path('course-grades/<uuid:id>/', CourseGradeDetailView.as_view(), name='course-grade-detail'),
    path('courses/<uuid:course_id>/grades/', GradesByCourseView.as_view(), name='grades-by-course'),
    path('courses/<uuid:course_id>/grades/publish/<uuid:session_id>/<str:semester>/',
         PublishGradesView.as_view(), name='publish-grades'),

    # Semester Results / GPA
    path('semester-results/', SemesterResultListView.as_view(), name='semester-result-list'),
    path('students/<uuid:student_id>/semester-results/', StudentSemesterResultsView.as_view(), name='student-semester-results'),
    path('students/<uuid:student_id>/semester-results/recompute/<uuid:session_id>/<str:semester>/',
         RecomputeSemesterResultView.as_view(), name='recompute-semester-result'),

    # CGPA
    path('students/<uuid:student_id>/cgpa/', StudentCGPAView.as_view(), name='student-cgpa'),
    path('cgpa/leaderboard/', CGPALeaderboardView.as_view(), name='cgpa-leaderboard'),

    # Transcript
    path('students/<uuid:student_id>/transcript/', StudentTranscriptView.as_view(), name='student-transcript'),

    # Term Grades (secondary school)
    path('term-grades/', GradeListCreateView.as_view(), name='term-grade-list'),
    path('term-grades/<uuid:id>/', GradeDetailView.as_view(), name='term-grade-detail'),

    # Attendance
    path('attendance/', AttendanceListCreateView.as_view(), name='attendance-list'),
    path('attendance/<uuid:id>/', AttendanceDetailView.as_view(), name='attendance-detail'),
]
