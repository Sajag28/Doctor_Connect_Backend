from django.http import JsonResponse,HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.sessions.backends.db import SessionStore
import uuid
import asyncio
from .serializers import PatientSerializer, MedicalRecordSerializer
from med_backend.settings import patients_collection, records_collection, appointment_history
import datetime
from datetime import timedelta,datetime,time
import med_backend.settings as settings
import jwt
from .models import Appointment,Doctor
from django.db import transaction
from .tasks import send_email_notification
import ssl
from django.views.decorators.csrf import csrf_exempt
ssl._create_default_https_context = ssl._create_unverified_context
from django.core.mail import send_mail
from django.db import transaction
# Session management
session_store = SessionStore()
#
#Generate JWT tokens
def get_tokens_for_user(patient_id):
    payload = {
        'user_id': patient_id,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }

    secret_key = settings.SECRET_KEY
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token

# Patient Registration
class RegisterPatient(APIView):
     def post(self, request):
        data = request.data
        serializer = PatientSerializer(data=data)

        if serializer.is_valid():
            patient_id = str(uuid.uuid4())  # Unique patient ID
            patient_data = serializer.validated_data
            patient_data["_id"] = patient_id
            patient_data["password"] = make_password(patient_data["password"])  # Hash password

            patients_collection.insert_one(patient_data)
            session_store[patient_id] = patient_data  # Save session
            session_store.save()

            tokens = get_tokens_for_user(patient_id)
            send_email_notification("sajagaga2806@gmail.com","Successfully Registered",f"You succesfully signed up. Your Patient ID is {patient_id}")
            return Response({"message": "Patient registered successfully", "patient_id": patient_id,"tokens":tokens})
        
        return Response(serializer.errors, status=400)

# Patient Login with JWT & Session Management
class PatientLogin(APIView):
     def post(self, request):
        data = request.data
        patient = patients_collection.find_one({"_id": data["patient_id"]})
        
        if patient and check_password(data["password"], patient["password"]):
            tokens = get_tokens_for_user(patient["_id"])

            # Store patient_id in session
            request.session["patient_id"] = patient["_id"]
            request.session.modified = True  # Mark the session as modified to ensure changes are saved
            request.session.save()  # Explicitly save the session

            return Response({
                "message": "Login successful",
                "tokens": tokens,
                "patient_id": patient["_id"]
            }, status=200)

        return Response({"error": "Invalid credentials"}, status=401)
# Patient Dashboard (Protected Route)
class PatientDashboard(APIView):
    def post(self, request):
        # Retrieve patient_id from session
        patient_id = request.data.get("patient_id")

        if not patient_id:
            return Response({"error": "Session expired. Please log in again."}, status=403)

        patient = patients_collection.find_one({"_id": patient_id}, {"_id": 0, "password": 0})
        return Response({"message": "Welcome to your dashboard", "patient_details": patient}, status=200)

# Create Medical Record
class CreateMedicalRecord(APIView):
    def post(self, request):
        data = request.data
        record_id = str(uuid.uuid4())  # Generate a unique record ID
        data["record_id"] = record_id  # Store the ID in the data
        
        serializer = MedicalRecordSerializer(data=data)
        
        if serializer.is_valid():
            records_collection.insert_one(serializer.validated_data)  # Save record
            return Response({"message": "Medical record created successfully", "record_id": record_id})

        return Response(serializer.errors, status=400)

# View Patient Records
class ViewRecords(APIView):
    

    def get(self, request, patient_id):
        records = list(records_collection.find({"patient_id": patient_id}, {"_id": 0}))

        if not records:
            return Response({"message": "No records found"}, status=200)

        return Response(records)

# Update Medical Record
class UpdateRecord(APIView):
    

    def put(self, request, record_id):
        data = request.data
        updated = records_collection.update_one({"record_id": record_id}, {"$set": data})

        if updated.matched_count == 0:
            return Response({"message": "Record not found"}, status=404)

        return Response({"message": "Medical record updated successfully"})

# Delete Medical Record
class DeleteRecord(APIView):
    

    def delete(self, request, record_id):
        deleted = records_collection.delete_one({"record_id": record_id})

        if deleted.deleted_count == 0:
            return Response({"message": "Record not found"}, status=404)

        return Response({"message": "Medical record deleted successfully"})

class SetDoctorAvailability(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        param=request.data.get("doctor_id")
        doctor = Doctor.objects.filter(doctor_id=param).first()
        if not doctor:
            return Response({"message": "Doctor not found what to do?"}, status=404)
        data = request.data
        work_days = data.get("work_days", [])  # ["Monday", "Tuesday", ...]
        max_slots_per_time = data.get("max_slots_per_time", 10)

        doctor.work_days = work_days
        doctor.max_slots_per_time = max_slots_per_time
        today = datetime.today()
        next_day = today + timedelta(days=1)

        # Check if the next day is a working day
        # work_days = []  # This should be fetched from the Doctor instance or defined somewhere

        # if next_day.strftime("%A") not in work_days:
        #     return {}  # Return an empty dictionary if it's a non-working day

        start_time = time(9, 0)  # 9:00 AM
        end_time = time(17, 30)  # 5:30 PM
        slot_duration = timedelta(minutes=30)  # Each slot is 30 minutes

        slots = []
        while start_time <= end_time:
            slots.append({"time": start_time.strftime("%H:%M"), "remaining": max_slots_per_time})  # Default 10 remaining slots
            start_time = (datetime.combine(next_day, start_time) + slot_duration).time()
        doctor.available_slots=slots
        print("Slots are: ")
        doctor.save()

        return Response({"message": f"Availability updated successfully with days:{work_days} slots: {slots}"})
class BookAppointment(APIView):
    def post(self, request):
        data = request.data
        doctor_id = data.get("doctor_id")
        patient_id = request.data.get("patient_id")  # Retrieve patient_id from session
        scheduled_time = data.get("scheduled_time")
        day = data.get("day")
        print(doctor_id)
        print(patient_id)
        print(scheduled_time)
        print(day)
        if not patient_id:
            return Response({"error": "Session expired. Please log in again."}, status=403)

        try:
         with transaction.atomic():
            doctor = Doctor.objects.filter(doctor_id=doctor_id).first()
            if not doctor:
                return Response({"error": "Doctor not found"}, status=404)
            
            print(f"Doctor available slots: {doctor.available_slots}")

            work_days = doctor.work_days
            if day not in work_days:
                return Response({"error": "Doctor is not available on this day"}, status=400)

            patient = patients_collection.find_one({"_id": patient_id})
            if not patient:
                return Response({"error": "Patient not found"}, status=404)

            # Format the date for the next day
            today = datetime.today()
            next_day = today + timedelta(days=1)  # Get the next day
            date_str = next_day.strftime("%Y-%m-%d")  # Format as YYYY-MM-DD

            # Check if the scheduled time exists in the available slots for that date
            available_slots_for_day = doctor.available_slots
            if not any(slot["time"] == scheduled_time for slot in available_slots_for_day):
                return Response({"error": "Slot not available"}, status=400)
            check_ap = Appointment.objects.filter(patient_id=patient_id, scheduled_time=scheduled_time).first()
            if check_ap:
              return Response({"error": "Appointment already exists for this time"}, status=400)

            # Create appointment
            appointment = Appointment.objects.create(
                doctor_id=doctor_id,
                patient_id=patient_id,
                scheduled_time=scheduled_time,
                status="Scheduled",
                date=datetime.today()+timedelta(days=1)
            )

            # Remove booked slot
            for slot in available_slots_for_day:
                if slot["time"] == scheduled_time:
                    if slot["remaining"] > 0:
                        slot["remaining"] -= 1
                        break
                    else:
                        return Response({"error": "No slots available"}, status=400)

            doctor.save()

            # Retrieve patient email for notification
            patient_email = patient.get("email")

            # Store appointment history
            history_entry = {
                "appointment_id": str(appointment.id),
                "doctor_id": doctor_id,
                "patient_id": patient_id,
                "scheduled_time": scheduled_time,
                "status": "Scheduled",
            }
            appointment_history.insert_one(history_entry)

            # Send email notification
            send_email_notification("sajagaga2806@gmail.com", "Appointment Booked", f"Patient ID: {patient_id} Your appointment is confirmed for {scheduled_time} tomorrow")

            return Response({"message": "Appointment booked successfully", "appointment_id": str(appointment.id)})

        except Doctor.DoesNotExist:
            return Response({"error": "Doctor not found"}, status=404)


class RescheduleAppointment(APIView):
    def post(self, request, appointment_id):
        data = request.data
        new_time = data.get("new_time")
        patient_id = request.data.get("patient_id")  # Retrieve patient_id from session

        if not patient_id:
            return Response({"error": "Session expired. Please log in again."}, status=403)

        try:
          with transaction.atomic():
            appointment = Appointment.objects.get(id=appointment_id, patient_id=patient_id)
            doctor=Doctor.objects.filter(doctor_id=appointment.doctor_id).first()
            print(f"Available slots: {doctor.available_slots}")
            if not any(slot["time"] == new_time for slot in doctor.available_slots):
            
                return Response({"error": "New slot not available"}, status=400)
            appointment_time=str(appointment.scheduled_time)[:5]
            print("Old scheduled time is: "+appointment_time)
            # Restore old slot & remove new slot
            for slot in doctor.available_slots:
                if (slot["time"]==appointment_time):
                    print("old time found")
                    rem=slot["remaining"]
                    rem=rem+1
                    slot["remaining"]=rem
                    print("Now old slots remaining: ", slot["remaining"])

                if (slot["time"]==new_time):
                    print("new time found")
                    slot["remaining"] -= 1
            
            doctor.save()

            # Update appointment
            old_time = appointment.scheduled_time
            appointment.scheduled_time = new_time
            appointment.status = "Rescheduled"
            appointment.save()
            patient = patients_collection.find_one({"_id": patient_id})
            patient_email=patient.get("email")
            # Update history
            appointment_history.update_one(
                {"appointment_id": appointment_id},
                {"$set": {
                    "scheduled_time": new_time,
                    "status": "Rescheduled",
                }}
            )

            # Send email notification
            send_email_notification("sajagaga2806@gmail.com", "Appointment Rescheduled", f"Patient ID: {patient_id} Your appointment is now scheduled for {new_time}")

            return Response({"message": f"Appointment rescheduled from {old_time} to {new_time}."})

        except Appointment.DoesNotExist:
            return Response({"error": "Appointment not found"}, status=404)

class CancelAppointment(APIView):
    def post(self, request, appointment_id):
        patient_id = request.data.get("patient_id")  # Retrieve patient_id from session

        if not patient_id:
            return Response({"error": "Session expired. Please log in again."}, status=403)

        try:
          with transaction.atomic():
            appointment = Appointment.objects.get(id=appointment_id, patient_id=patient_id)
            doctor=Doctor.objects.get(doctor_id=appointment.doctor_id)
            # Restore slot
            appointment_time=str(appointment.scheduled_time)[:5]
            for slot in doctor.available_slots:
                if (slot["time"]==appointment_time):
                    print("old time found")
                    rem=slot["remaining"]
                    rem=rem+1
                    slot["remaining"]=rem
                    print("Now old slots remaining: ", slot["remaining"])
            patient = patients_collection.find_one({"_id": patient_id})
            patient_email=patient.get("email")
            # Update appointment
            appointment.status = "Cancelled"
            appointment.save()

            # Update history
            appointment_history.update_one(
                {"appointment_id": appointment_id},
                {"$set": {
                    "status": "Cancelled",
                    
                }}
            )

            # Send email notification
            send_email_notification("sajagaga2806@gmail.com", f"Patient ID:{patient_id}Appointment Cancelled", f"Patient ID: {patient_id}Your appointment has been cancelled.")

            return Response({"message": "Appointment cancelled successfully"})

        except Appointment.DoesNotExist:
            return Response({"error": "Appointment not found"}, status=404)


class RegisterDoctor(APIView):
    def post(self, request):
        data = request.data
        if Doctor.objects.filter(email=data.get("email")).exists():
            return Response({"error": "Doctor with this email already exists"}, status=400)

        doctor = Doctor.objects.create(
            doctor_id=str(uuid.uuid4()),  # Unique doctor ID
            name=data["name"],
            email=data["email"],
            password=make_password(data["password"]),
            specialization=data.get("specialization", ""),
        )
        
        return Response({"message": "Doctor registered successfully", "doctor_id": doctor.doctor_id,"name":doctor.name}, status=201)
class DoctorLogin(APIView):
    def post(self, request):
        data = request.data
        try:
            doctor = Doctor.objects.get(email=data["email"])

            if check_password(data["password"], doctor.password):
                request.session["doctor_id"]=doctor.doctor_id
                print(request.session.get("doctor_id"))
                tokens = get_tokens_for_user(doctor.id)  # Generate JWT tokens
                return Response({"message": "Login successful", "tokens": tokens, "doctor_id": doctor.doctor_id, "name":doctor.name})
        except Doctor.DoesNotExist:
            pass

        return Response({"error": "Invalid credentials"}, status=401)

class DoctorDetails(APIView):
    def post(self,request):
     doctor_id = request.data['doctor_id']  # Get doctor_id from query parameters
     if not doctor_id:
        return JsonResponse({"error": "Doctor ID is required"}, status=400)

     doctor = Doctor.objects.filter(doctor_id=doctor_id).first()
     if doctor:
      return JsonResponse({
        "doctor_id": doctor.doctor_id,
        "name": doctor.name,
        "email": doctor.email,
        "specialization": doctor.specialization,
        
      })
     else:
         return JsonResponse({"error": "Doctor not found"}, status=404)

class MedicalRecords(APIView):
    def post(self,request):
        try:
            records = list(records_collection.find({"doctor_id": request.data.get("doctor_id")}, {"_id": 0}))  # Exclude MongoDB _id field
            return JsonResponse(records, safe=False, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        return JsonResponse({"error": "Invalid request method"}, status=400)

class TestMail(APIView):
    def get(self,request):
     send_mail(
    "Test Email from Brevo",
    "This is a test email from Django using Brevo SMTP.",
    "agrawalsiddhi836@gmail.com",
    ["sajagaga2806@gmail.com"],
    fail_silently=False,
     )
     return HttpResponse("Email sent successfully")
class PatientAppointment(APIView):
   def get(self,request, patient_id):
    try:
        appointments = list(appointment_history.find(
                {"patient_id": patient_id},  # Filter by patient_id
                {"_id": 0, "appointment_id": 1, "doctor_id": 1, "date": 1, "scheduled_time": 1, "status": 1}
            ))
        return JsonResponse(appointments, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

class DoctorAppointment(APIView):
    def get(self,request, doctor_id):
     try:
        appointments = list(appointment_history.find(
                {"doctor_id": doctor_id},  # Filter by doctor_id
                {"_id": 0, "appointment_id": 1, "patient_id": 1, "date": 1, "scheduled_time": 1, "status": 1}
            ))
        print(appointments)
        return JsonResponse(appointments, safe=False)
     except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)