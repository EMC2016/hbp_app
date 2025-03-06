from django.db import models

class Patient(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    familyName = models.CharField(max_length=20, null=True, blank=True)
    givenName = models.CharField(max_length=20,null = True, blank = True)

class Observation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="observations")
    observation = models.CharField(max_length=50)  
    value = models.FloatField(null=True, blank=True)  # Numeric values like BMI, glucose, etc.
    unit = models.CharField(max_length=20, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class Condition(models.Model):
    CLINICAL_STATUS_CHOICES = [
        ("active", "Active"),
        ("recurrence", "Recurrence"),
        ("relapse", "Relapse"),
        ("inactive", "Inactive"),
        ("remission", "Remission"),
        ("resolved", "Resolved"),
    ]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="conditions")
    condition = models.CharField(max_length=50) 
    clinical_status = models.CharField(
        max_length=20,
        choices=CLINICAL_STATUS_CHOICES,
        default="active"
    )
    # description = models.TextField(null=True, blank=True)
    # diagnosed_on = models.DateField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
