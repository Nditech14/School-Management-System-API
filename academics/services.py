"""
Academic Services — CGPA computation, transcript generation.
All business logic lives here (Clean Architecture: service layer).
"""
import logging
from decimal import Decimal
from django.db.models import Sum, Q

from students.models import StudentProfile
from .models import Enrollment, CourseGrade, SemesterResult

logger = logging.getLogger('school.api')
audit_logger = logging.getLogger('school.audit')


class CGPAService:
    """
    Computes GPA per semester and cumulative CGPA for a student.

    Formula:
        GPA  = Σ(grade_point × credit_units) / Σ(credit_units)  [per semester]
        CGPA = Σ all quality points / Σ all credit units         [cumulative]
    """

    @staticmethod
    def _class_of_degree(cgpa: Decimal) -> str:
        if cgpa >= Decimal('4.50'): return 'First Class Honours'
        if cgpa >= Decimal('3.50'): return 'Second Class Upper (2:1)'
        if cgpa >= Decimal('2.40'): return 'Second Class Lower (2:2)'
        if cgpa >= Decimal('1.50'): return 'Third Class'
        if cgpa >= Decimal('1.00'): return 'Pass'
        return 'Fail'

    @classmethod
    def compute_semester_gpa(cls, student: StudentProfile, session, semester: str) -> dict:
        """
        Compute and persist GPA for one session/semester.
        Returns a dict with gpa and supporting data.
        """
        enrollments = Enrollment.objects.filter(
            student=student,
            academic_session=session,
            semester=semester,
            status__in=['completed', 'failed'],
        ).select_related('course', 'grade')

        total_units_registered = 0
        total_units_passed = 0
        total_quality_points = Decimal('0')

        for enrollment in enrollments:
            cu = enrollment.course.credit_units
            total_units_registered += cu
            try:
                grade = enrollment.grade
                if grade.grade_letter != 'F':
                    total_units_passed += cu
                total_quality_points += grade.quality_point
            except CourseGrade.DoesNotExist:
                pass  # grade not yet recorded

        gpa = (
            (total_quality_points / total_units_registered).quantize(Decimal('0.01'))
            if total_units_registered > 0 else Decimal('0.00')
        )

        on_probation = gpa < Decimal('1.00') and total_units_registered > 0

        result, _ = SemesterResult.objects.update_or_create(
            student=student,
            academic_session=session,
            semester=semester,
            defaults={
                'total_credit_units_registered': total_units_registered,
                'total_credit_units_passed': total_units_passed,
                'total_quality_points': total_quality_points,
                'gpa': gpa,
                'is_on_probation': on_probation,
            },
        )
        return {
            'session': str(session),
            'semester': semester,
            'total_units_registered': total_units_registered,
            'total_units_passed': total_units_passed,
            'total_quality_points': float(total_quality_points),
            'gpa': float(gpa),
            'is_on_probation': on_probation,
        }

    @classmethod
    def compute_cgpa(cls, student: StudentProfile) -> dict:
        """
        Compute cumulative CGPA across ALL sessions.
        Returns full breakdown per semester + cumulative stats.
        """
        results = SemesterResult.objects.filter(student=student).select_related('academic_session').order_by(
            'academic_session__start_date', 'semester'
        )

        cumulative_units = 0
        cumulative_quality_points = Decimal('0')
        semesters = []

        for r in results:
            cumulative_units += r.total_credit_units_registered
            cumulative_quality_points += r.total_quality_points
            semesters.append({
                'session': r.academic_session.name,
                'semester': r.semester,
                'units_registered': r.total_credit_units_registered,
                'units_passed': r.total_credit_units_passed,
                'quality_points': float(r.total_quality_points),
                'gpa': float(r.gpa),
                'is_on_probation': r.is_on_probation,
            })

        cgpa = (
            (cumulative_quality_points / cumulative_units).quantize(Decimal('0.02'))
            if cumulative_units > 0 else Decimal('0.00')
        )

        return {
            'student_id': student.student_id,
            'student_name': student.user.get_full_name(),
            'programme': str(student.programme) if student.programme else None,
            'department': str(student.department) if student.department else None,
            'cumulative_units_registered': cumulative_units,
            'cumulative_quality_points': float(cumulative_quality_points),
            'cgpa': float(cgpa),
            'class_of_degree': cls._class_of_degree(cgpa),
            'semesters': semesters,
        }


class TranscriptService:
    """Builds the full academic transcript for a student."""

    @staticmethod
    def generate(student: StudentProfile) -> dict:
        """Return complete transcript data."""
        from .models import CourseGrade
        from students.models import AcademicSession

        grades = (
            CourseGrade.objects
            .filter(enrollment__student=student, is_published=True)
            .select_related(
                'enrollment__course',
                'enrollment__academic_session',
                'enrollment__course__department',
            )
            .order_by(
                'enrollment__academic_session__start_date',
                'enrollment__semester',
                'enrollment__course__code',
            )
        )

        # Group by session → semester → courses
        sessions_map = {}
        for g in grades:
            e = g.enrollment
            sess_key = e.academic_session.name
            sem_key = e.semester
            sessions_map.setdefault(sess_key, {}).setdefault(sem_key, []).append({
                'course_code': e.course.code,
                'course_name': e.course.name,
                'credit_units': e.course.credit_units,
                'ca_score': float(g.ca_score),
                'assignment_score': float(g.assignment_score),
                'exam_score': float(g.exam_score),
                'total_score': float(g.total_score),
                'grade_letter': g.grade_letter,
                'grade_point': float(g.grade_point),
                'quality_point': float(g.quality_point),
            })

        transcript_sessions = []
        for session_name, semesters in sessions_map.items():
            for semester, courses in semesters.items():
                transcript_sessions.append({
                    'session': session_name,
                    'semester': semester,
                    'courses': courses,
                })

        cgpa_data = CGPAService.compute_cgpa(student)

        return {
            'student': {
                'id': str(student.id),
                'student_id': student.student_id,
                'full_name': student.user.get_full_name(),
                'email': student.user.email,
                'programme': str(student.programme) if student.programme else None,
                'department': str(student.department) if student.department else None,
                'level': student.current_level,
                'admission_date': str(student.admission_date),
                'status': student.status,
            },
            'transcript': transcript_sessions,
            'summary': {
                'cgpa': cgpa_data['cgpa'],
                'class_of_degree': cgpa_data['class_of_degree'],
                'cumulative_units_registered': cgpa_data['cumulative_units_registered'],
                'cumulative_quality_points': cgpa_data['cumulative_quality_points'],
            },
        }
