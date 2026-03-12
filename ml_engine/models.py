from django.db import models
from patients.models import Patient
import uuid

class Prediction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient_id = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='predictions')
    prediction_date = models.DateTimeField(auto_now_add=True)
    risk_score = models.FloatField()
    risk_category = models.CharField(max_length=50, choices=[('Low', 'Low Risk'), ('Moderate', 'Moderate Risk'), ('High', 'High Risk')])
    model_used = models.CharField(max_length=100)
    shap_values = models.JSONField(null=True, blank=True)
    triggered_by = models.CharField(max_length=255, null=True, blank=True)  # e.g., "MonitoringVisit ID 123", "Manual"

    def __str__(self):
        return f"Prediction {self.risk_category} ({self.risk_score:.2f}) for Patient {self.patient_id_id} on {self.prediction_date.strftime('%Y-%m-%d')}"
