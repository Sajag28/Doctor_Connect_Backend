

# Register your models here.
from django.contrib import admin
from .models import Patient, Doctor, Appointment

# Register Patient model
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'contact')  # Customize columns displayed in the admin list view
    search_fields = ('patient_id', 'contact')  # Add search functionality to the admin

# Register Doctor model
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('doctor_id', 'specialization', 'max_slots_per_time', 'work_days')  # Customize columns displayed
    search_fields = ('doctor_id', 'specialization')  # Add search functionality to the admin

# Register Appointment model
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('appointment_id', 'patient_id', 'doctor_id', 'date', 'scheduled_time', 'status')  # Customize columns
    search_fields = ('appointment_id', 'patient_id', 'doctor_id')  # Add search functionality to the admin
    list_filter = ('status', 'date')  # Add filtering options by status and date

