from django.db import models
from django.contrib.auth.models import User
from datetime import time, timedelta, datetime

class Patient(models.Model):
    patient_id=models.CharField(max_length=30,default="pat_456")
    contact = models.CharField(max_length=15)

class Doctor(models.Model):
    def default_available_slots():
        """
        Default function to generate available slots for the next working day
        """
        today = datetime.today()
        next_day = today + timedelta(days=1)

        # Check if the next day is a working day
        work_days = []  # This should be fetched from the Doctor instance or defined somewhere

        if next_day.strftime("%A") not in work_days:
            return {}  # Return an empty dictionary if it's a non-working day

        start_time = time(9, 0)  # 9:00 AM
        end_time = time(17, 30)  # 5:30 PM
        slot_duration = timedelta(minutes=30)  # Each slot is 30 minutes

        slots = []
        while start_time <= end_time:
            slots.append({"time": start_time.strftime("%H:%M"), "remaining": 10})  # Default 10 remaining slots
            start_time = (datetime.combine(next_day, start_time) + slot_duration).time()

        return {next_day.strftime("%Y-%m-%d"): slots}

    def default_work_days():
        return []  # Return an empty list or a list of working days as needed

    doctor_id = models.CharField(max_length=30, default="123")
    name = models.CharField(max_length=30, default="abc")
    email = models.EmailField(default="doctor@gmail.com")
    password = models.CharField(max_length=21, default="hello")
    specialization = models.CharField(max_length=255)
    max_slots_per_time = models.IntegerField(default=3)  # Max patients per slot
    available_slots = models.JSONField(default=default_available_slots)  # Stores available slots per day
    work_days = models.JSONField(default=default_work_days)  # Stores working days like ["Monday", "Tuesday"]

    def generate_daily_slots(self):
        """
        Generate fresh slots for the next working day automatically.
        This should run as a scheduled task daily at midnight.
        """
        today = datetime.today()
        next_day = today + timedelta(days=1)

        if next_day.strftime("%A") not in self.work_days:
            return  # Skip slot generation if it's a non-working day

        start_time = time(9, 0)  # 9:00 AM
        end_time = time(17, 30)  # 5:30 PM
        slot_duration = timedelta(minutes=30)  # Each slot is 30 minutes

        slots = []
        while start_time <= end_time:
            slots.append({"time": start_time.strftime("%H:%M"), "remaining": self.max_slots_per_time})
            start_time = (datetime.combine(next_day, start_time) + slot_duration).time()

        self.available_slots = {next_day.strftime("%Y-%m-%d"): slots}
        self.save()
class Appointment(models.Model):
    appointment_id=models.CharField(max_length=30,default="12345")
    patient_id=models.CharField(max_length=30,default="12345")
    doctor_id = models.CharField(max_length=30,default="45678")
    date = models.DateField()
    scheduled_time = models.TimeField()
    status = models.CharField(max_length=20, choices=[("booked", "Booked"), ("cancelled", "Cancelled"), ("rescheduled", "Rescheduled")], default="booked")



