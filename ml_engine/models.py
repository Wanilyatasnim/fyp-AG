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

class ModelMetric(models.Model):
    version = models.CharField(max_length=50, default='1.0.0')
    accuracy = models.FloatField()
    precision = models.FloatField()
    recall = models.FloatField()
    f1_score = models.FloatField()
    auc_roc = models.FloatField()
    global_importance = models.JSONField(help_text="Global SHAP values")
    model_name = models.CharField(max_length=100, default='XGBoost')
    created_at = models.DateTimeField(auto_now_add=True)

    def __cl__(self):
        return f"Metric v{self.version} ({self.auc_roc:.4f})"
