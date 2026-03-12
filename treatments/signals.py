from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MonitoringVisit, Treatment
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=MonitoringVisit)
def check_ml_prediction_criteria(sender, instance, created, **kwargs):
    """
    Check if patient meets prediction criteria after a visit is saved.
    Scenario: ≥ 3 months treatment AND ≥ 2 visits.
    If met, trigger ML prediction.
    """
    if created:
        patient = instance.patient
        visits_count = MonitoringVisit.objects.filter(patient=patient).count()
        # Criteria: At least 2 visits and latest visit_month >= 3 ?
        # Or treatment Days_In_Treatment > 90? We'll check visit count and highest visit month
        
        highest_month = MonitoringVisit.objects.filter(patient=patient).order_by('-visit_month').first().visit_month
        
        if visits_count >= 2 and highest_month >= 3:
            try:
                # Assuming ml_engine has a function like trigger_prediction
                # Since ml_engine is in same project, we can import it
                from ml_engine.models import Prediction
                # We would call a method, just stubbing it to be safe for now,
                # as the actual ml predict_ptld_risk is a task later in the list.
                logger.info(f"Triggering ML prediction for patient {patient.patient_id} - criteria met.")
                # We can call predict_ptld_risk(patient.patient_id) here later.
            except Exception as e:
                logger.error(f"Failed to trigger ML prediction for patient {patient.patient_id}: {str(e)}")
