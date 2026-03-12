from django.db.models.signals import post_save
from django.dispatch import receiver
from treatments.models import MonitoringVisit
from ml_engine.models import Prediction
from .predict import predict_ptld_risk

@receiver(post_save, sender=MonitoringVisit)
def check_prediction_criteria(sender, instance, created, **kwargs):
    """
    Trigger ML prediction check after saving a monitoring visit.
    Criteria: >= 3 months treatment and >= 2 visits (as per PRD).
    """
    if created:
        patient = instance.patient
        treatment = patient.treatment
        
        # Determine visit count and max month
        visits = patient.visits.all()
        visit_count = visits.count()
        
        # Using instance.visit_month to check if we are at month 3 or beyond
        if instance.visit_month >= 3 and visit_count >= 2:
            try:
                proba, category, model_used, shap_values = predict_ptld_risk(patient)
                
                # Check if a prediction recently happened to avoid duplicates (simplified logic)
                # In production, this might just update the latest one.
                Prediction.objects.create(
                    patient_id=patient,
                    risk_score=proba,
                    risk_category=category,
                    model_used=model_used,
                    shap_values=shap_values,
                    triggered_by=f"Auto (Visit Month {instance.visit_month})"
                )
            except Exception as e:
                # Add signal failure logging — catch exceptions and log errors without crashing CRUD save
                print(f"Prediction signal failed for patient {patient.patient_id}: {str(e)}")
