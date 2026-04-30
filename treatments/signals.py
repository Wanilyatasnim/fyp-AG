from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MonitoringVisit, Treatment
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=MonitoringVisit)
def synchronize_monitoring_to_treatment(sender, instance, created, **kwargs):
    """
    Synchronize MonitoringVisit bacilloscopy results to the Treatment model's 
    dataset-aligned Month_X fields. 
    This ensures that Rule-Based Clinical Overrides (e.g. MDR-TB + M4 Positive)
    trigger automatically when a clinician records a new visit.
    """
    patient = instance.patient
    treatment, created_t = Treatment.objects.get_or_create(patient=patient)
    
    month = instance.visit_month
    result = instance.bacilloscopy_result
    
    # 1=Positive, 2=Negative -> matches Treatment model mapping
    if 1 <= month <= 6 and result is not None:
        setattr(treatment, f'Bacilloscopy_Month_{month}', result)
        treatment.save()
        logger.info(f"Synchronized visit Month {month} result {result} for patient {patient.name}")


@receiver(post_save, sender=MonitoringVisit)
def check_ml_prediction_criteria(sender, instance, created, **kwargs):
    """
    Check if patient meets prediction criteria after a visit is saved.
    Scenario: ≥ 2 visits.
    If met, trigger ML prediction update.
    """
    if created:
        patient = instance.patient
        visits_count = MonitoringVisit.objects.filter(patient=patient).count()
        # Criteria: At least 2 visits
        if visits_count >= 2:
            try:
                # We can proactively run predictions here if we have a model instance
                # For now, just logging fulfillment of criteria
                logger.info(f"Triggering ML criteria met for patient {patient.patient_id}.")
            except Exception as e:
                logger.error(f"Failed to trigger criteria check: {str(e)}")
