from django.contrib import admin
from .models import (
    Faculty, Department, Programme, ClassRoom, AcademicSession,
    StudentProfile, StudentDocument, Guardian,
)


@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_current']
    list_filter = ['is_current']


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'dean', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'faculty', 'hod', 'is_active']
    list_filter = ['faculty', 'is_active']
    search_fields = ['name', 'code', 'faculty__name']


@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'degree_type', 'department', 'duration_years', 'is_active']
    list_filter = ['degree_type', 'is_active', 'department__faculty']
    search_fields = ['name', 'code']


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'grade_level', 'capacity', 'class_teacher']
    list_filter = ['grade_level']
    search_fields = ['name', 'grade_level']


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = [
        'student_id', 'get_name', 'gender', 'department',
        'programme', 'current_level', 'status', 'admission_date',
    ]
    list_filter = ['gender', 'status', 'is_active', 'entry_mode', 'department', 'programme']
    search_fields = ['student_id', 'user__first_name', 'user__last_name', 'user__email',
                     'jamb_registration_number']
    raw_id_fields = ['user', 'current_class', 'department', 'programme']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Identity', {'fields': ('user', 'student_id', 'date_of_birth', 'gender', 'blood_group',
                                  'religion', 'marital_status')}),
        ('Contact', {'fields': ('address', 'state_of_origin', 'lga', 'nationality',
                                 'emergency_contact_name', 'emergency_contact_phone',
                                 'emergency_contact_relationship')}),
        ('Academic Placement', {'fields': ('programme', 'department', 'current_class',
                                            'current_level', 'current_semester')}),
        ('Admission', {'fields': ('admission_date', 'entry_mode', 'jamb_registration_number',
                                   'previous_school')}),
        ('Medical', {'fields': ('medical_conditions', 'disabilities')}),
        ('Status', {'fields': ('status', 'is_active', 'graduation_date')}),
        ('Timestamps', {'fields': ('id', 'created_at', 'updated_at')}),
    )

    def get_name(self, obj): return obj.user.get_full_name()
    get_name.short_description = 'Name'


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ['student', 'document_type', 'title', 'uploaded_by', 'created_at']
    list_filter = ['document_type']
    search_fields = ['student__student_id', 'title']


@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ['get_name', 'relationship', 'phone_number', 'email']
    search_fields = ['first_name', 'last_name', 'email', 'phone_number']
    filter_horizontal = ['students']

    def get_name(self, obj): return f"{obj.first_name} {obj.last_name}"
    get_name.short_description = 'Name'
