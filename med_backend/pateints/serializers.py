from rest_framework import serializers
class PatientSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    age = serializers.IntegerField()
    gender = serializers.ChoiceField(choices=["Male", "Female", "Other"])
    email=serializers.EmailField()
    contact = serializers.CharField(max_length=15)
    medical_history = serializers.ListField(
        child=serializers.CharField(max_length=255),  # Ensuring each item is a string
        allow_empty=True  # Allow an empty list
    )
    _id=serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)  # Ensure password is included, write only

    # Custom validation for password (optional)
    def validate_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long.")
        return value
class MedicalRecordSerializer(serializers.Serializer):
    patient_id = serializers.CharField()
    record_id=serializers.CharField(required=False)
    diagnosis = serializers.CharField()
    treatment = serializers.CharField(required=False)
    doctor_id = serializers.CharField()
    
    date = serializers.CharField()

