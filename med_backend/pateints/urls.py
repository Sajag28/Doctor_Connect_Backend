from django.urls import path
from .views import (
    RegisterPatient, PatientLogin, PatientDashboard, CreateMedicalRecord, ViewRecords,
    UpdateRecord, DeleteRecord, SetDoctorAvailability, BookAppointment, RescheduleAppointment,
    CancelAppointment, RegisterDoctor, DoctorLogin,DoctorDetails,MedicalRecords, TestMail,PatientAppointment,DoctorAppointment
)

urlpatterns = [
    # Patient routes
    path('patient/register/', RegisterPatient.as_view(), name='register_patient'),
    path('patient/login/', PatientLogin.as_view(), name='patient_login'),
    path('patient/dashboard/', PatientDashboard.as_view(), name='patient_dashboard'),
    path('patient/testmail/',TestMail.as_view(),name="test_mail"),
    path("patient/appointments/<str:patient_id>/", PatientAppointment.as_view(), name="get_patient_appointments"),

    # Medical Records
    path('records/create/', CreateMedicalRecord.as_view(), name='create_record'),
    path('records/view/<str:patient_id>/', ViewRecords.as_view(), name='view_records'),
    path('records/update/<str:record_id>/', UpdateRecord.as_view(), name='update_record'),
    path('records/delete/<str:record_id>/', DeleteRecord.as_view(), name='delete_record'),
    path('records/list/', MedicalRecords.as_view(), name="list_records"),

    # Doctor routes
    path('doctor/register/', RegisterDoctor.as_view(), name='register_doctor'),
    path('doctor/login/', DoctorLogin.as_view(), name='doctor_login'),
    path('doctor/set_availability/', SetDoctorAvailability.as_view(), name='set_doctor_availability'),
    path('doctor/details/',DoctorDetails.as_view(),name='DoctorDetails'),
    path('doctor/appointments/<str:doctor_id>/',DoctorAppointment.as_view(),name="doctor_appointment"),
    
    # Appointment routes
    path('appointment/book/', BookAppointment.as_view(), name='book_appointment'),
    path('appointment/reschedule/<str:appointment_id>/', RescheduleAppointment.as_view(), name='reschedule_appointment'),
    path('appointment/cancel/<str:appointment_id>/', CancelAppointment.as_view(), name='cancel_appointment'),
]
