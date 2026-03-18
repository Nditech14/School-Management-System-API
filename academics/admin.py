from django.contrib import admin
from .models import Subject, Course, Enrollment, CourseGrade, SemesterResult, CGPARecord, Grade, Attendance


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'teacher', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    filter_horizontal = ['classes']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'credit_units', 'level', 'semester', 'course_type', 'is_active']
    list_filter = ['department', 'course_type', 'semester', 'level', 'is_active']
    search_fields = ['name', 'code', 'department__name']
    raw_id_fields = ['department', 'programme', 'lecturer']
    filter_horizontal = ['prerequisites']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'academic_session', 'semester', 'status', 'enrolled_at']
    list_filter = ['status', 'semester', 'academic_session']
    search_fields = ['student__student_id', 'course__code']
    raw_id_fields = ['student', 'course', 'academic_session']


@admin.register(CourseGrade)
class CourseGradeAdmin(admin.ModelAdmin):
    list_display = ['get_student', 'get_course', 'ca_score', 'assignment_score',
                    'exam_score', 'total_score', 'grade_letter', 'is_published']
    list_filter = ['grade_letter', 'is_published', 'enrollment__academic_session']
    search_fields = ['enrollment__student__student_id', 'enrollment__course__code']
    raw_id_fields = ['enrollment', 'recorded_by']
    readonly_fields = ['total_score', 'grade_letter', 'grade_point', 'quality_point']

    def get_student(self, obj): return obj.enrollment.student.student_id
    def get_course(self, obj): return obj.enrollment.course.code
    get_student.short_description = 'Student ID'
    get_course.short_description = 'Course'


@admin.register(SemesterResult)
class SemesterResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'academic_session', 'semester', 'gpa',
                    'total_credit_units_registered', 'class_of_degree', 'is_on_probation']
    list_filter = ['semester', 'is_on_probation', 'academic_session']
    search_fields = ['student__student_id', 'student__user__first_name']
    readonly_fields = ['gpa', 'class_of_degree', 'is_on_probation', 'computed_at']


@admin.register(CGPARecord)
class CGPARecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'cgpa', 'class_of_degree',
                    'total_credit_units_registered', 'semesters_completed', 'computed_at']
    list_filter = ['class_of_degree']
    search_fields = ['student__student_id', 'student__user__first_name']
    readonly_fields = ['cgpa', 'class_of_degree', 'computed_at']


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'term', 'ca_score', 'exam_score', 'total_score', 'grade_letter']
    list_filter = ['term', 'grade_letter', 'academic_session']
    search_fields = ['student__student_id', 'student__user__first_name']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status', 'course', 'subject', 'marked_by']
    list_filter = ['status', 'date']
    search_fields = ['student__student_id']
    date_hierarchy = 'date'
