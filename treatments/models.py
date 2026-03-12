from django.db import models
from patients.models import Patient
from django.conf import settings


class Treatment(models.Model):
    """
    Treatment model aligned with dataset columns 13–16, 18–25, 25, 33, 37.
    """
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='treatment')

    # ── Dataset Col 13–16: Baseline Bacteriology ──────────────────────────
    Bacilloscopy_Sputum   = models.IntegerField(choices=[(1,'Positive'),(2,'Negative'),(3,'Not Performed'),(4,'Not Applicable'),(9,'Ignored')], null=True, blank=True)
    Bacilloscopy_Sputum_2 = models.IntegerField(choices=[(1,'Positive'),(2,'Negative'),(3,'Not Performed'),(4,'Not Applicable'),(9,'Ignored')], null=True, blank=True)
    Bacilloscopy_Other    = models.IntegerField(choices=[(1,'Positive'),(2,'Negative'),(3,'Not Performed'),(4,'Not Applicable'),(9,'Ignored')], null=True, blank=True)
    Sputum_Culture        = models.IntegerField(choices=[(1,'Positive'),(2,'Negative'),(3,'In Progress'),(4,'Not Performed'),(9,'Ignored')],  null=True, blank=True)

    # ── Dataset Col 18–24: 7 Drug Susceptibility ──────────────────────────
    Rifampicin   = models.IntegerField(choices=[(1,'Sensitive'),(2,'Resistant'),(3,'Not Performed'),(9,'Ignored')], null=True, blank=True)
    Isoniazid    = models.IntegerField(choices=[(1,'Sensitive'),(2,'Resistant'),(3,'Not Performed'),(9,'Ignored')], null=True, blank=True)
    Ethambutol   = models.IntegerField(choices=[(1,'Sensitive'),(2,'Resistant'),(3,'Not Performed'),(9,'Ignored')], null=True, blank=True)
    Streptomycin = models.IntegerField(choices=[(1,'Sensitive'),(2,'Resistant'),(3,'Not Performed'),(9,'Ignored')], null=True, blank=True)
    Pyrazinamide = models.IntegerField(choices=[(1,'Sensitive'),(2,'Resistant'),(3,'Not Performed'),(9,'Ignored')], null=True, blank=True)
    Ethionamide  = models.IntegerField(choices=[(1,'Sensitive'),(2,'Resistant'),(3,'Not Performed'),(9,'Ignored')], null=True, blank=True)
    Other_Drugs  = models.IntegerField(choices=[(1,'Sensitive'),(2,'Resistant'),(3,'Not Performed'),(9,'Ignored')], null=True, blank=True)

    # ── Dataset Col 25: Supervised_Treatment ─────────────────────────────
    Supervised_Treatment = models.IntegerField(choices=[(1,'Yes'),(2,'No'),(9,'Ignored')], null=True, blank=True)

    # ── Dataset Col 27–32: Serial Bacilloscopy by Month ──────────────────
    Bacilloscopy_Month_1 = models.IntegerField(choices=[(1,'Positive'),(2,'Negative'),(3,'Not Performed'),(9,'Ignored')], null=True, blank=True)
    Bacilloscopy_Month_2 = models.IntegerField(choices=[(1,'Positive'),(2,'Negative'),(3,'Not Performed'),(9,'Ignored')], null=True, blank=True)
    Bacilloscopy_Month_3 = models.IntegerField(choices=[(1,'Positive'),(2,'Negative'),(3,'Not Performed'),(9,'Ignored')], null=True, blank=True)
    Bacilloscopy_Month_4 = models.IntegerField(choices=[(1,'Positive'),(2,'Negative'),(3,'Not Performed'),(9,'Ignored')], null=True, blank=True)
    Bacilloscopy_Month_5 = models.IntegerField(choices=[(1,'Positive'),(2,'Negative'),(3,'Not Performed'),(9,'Ignored')], null=True, blank=True)
    Bacilloscopy_Month_6 = models.IntegerField(choices=[(1,'Positive'),(2,'Negative'),(3,'Not Performed'),(9,'Ignored')], null=True, blank=True)

    # ── Dataset Col 33: Outcome_Status ───────────────────────────────────
    Outcome_Status = models.IntegerField(
        choices=[(1,'Cure'),(2,'Abandonment'),(3,'Death by TB'),(4,'Death Other'),(5,'Transfer'),(6,'Diagnosis Changed'),(7,'MDR-TB'),(8,'Failure'),(9,'Primary Default')],
        null=True, blank=True
    )

    # ── Dataset Col 37: Days_In_Treatment ────────────────────────────────
    Days_In_Treatment = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Treatment for {self.patient.name}"


class MonitoringVisit(models.Model):
    """Manual visit records (clinician-entered, distinct from dataset months).
    Useful for the 'live' clinical tracking workflow."""
    patient      = models.ForeignKey(Patient,   on_delete=models.CASCADE, related_name='visits')
    treatment    = models.ForeignKey(Treatment, on_delete=models.CASCADE, related_name='visits')
    visit_month  = models.IntegerField(choices=[(i, f'Month {i}') for i in range(1, 7)])
    bacilloscopy_result = models.IntegerField(
        choices=[(1,'Positive'),(2,'Negative'),(3,'Not Performed')], null=True, blank=True
    )
    visit_date     = models.DateField(null=True, blank=True)
    clinical_notes = models.TextField(blank=True, null=True)
    recorded_by    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='recorded_visits'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('patient', 'visit_month')
        ordering = ['visit_month']

    def __str__(self):
        return f"Visit Month {self.visit_month} for {self.patient.name}"
