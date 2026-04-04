import uuid
from django.db import models
from django.conf import settings


class Patient(models.Model):
    """
    Aligned with brazil_tb_2019_last20k_english.xlsx (38 columns).
    Column names match the dataset exactly to simplify feature extraction for ML.
    """
    # ── Core Identifiers ──────────────────────────────────────────────────
    patient_id  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=255, default='Unknown Patient')
    created_at  = models.DateTimeField(auto_now_add=True)
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='patients_created'
    )
    assigned_clinician = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, limit_choices_to={'role': 'CLINICIAN'},
        related_name='assigned_patients'
    )
    treatment_status = models.CharField(
        max_length=20, 
        choices=[('Active', 'Active'), ('Completed', 'Completed'), ('Lost', 'Lost to Follow-up')],
        default='Active'
    )
    treatment_start_date = models.DateField(null=True, blank=True)
    dob = models.DateField(null=True, blank=True)

    # ── Dataset Column 1: Notification_Date ───────────────────────────────
    Notification_Date = models.DateField(null=True, blank=True)

    # ── Dataset Column 2: Sex ─────────────────────────────────────────────
    Sex = models.IntegerField(
        choices=[(1, 'Male'), (2, 'Female'), (9, 'Ignored')],
        null=True, blank=True
    )

    # ── Dataset Column 3: Race ────────────────────────────────────────────
    Race = models.IntegerField(
        choices=[(1, 'White'), (2, 'Black'), (3, 'Yellow'), (4, 'Brown'), (5, 'Indigenous'), (9, 'Ignored')],
        null=True, blank=True
    )

    # ── Dataset Column 4: Treatment (treatment_type) ─────────────────────
    Treatment = models.IntegerField(
        choices=[(1, 'New Case'), (2, 'Relapse'), (3, 'Re-entry'), (4, "Don't Know"), (5, 'Transfer'), (6, 'Post-mortem'), (9, 'Ignored')],
        null=True, blank=True
    )

    # ── Dataset Column 5: Chest_X_Ray ─────────────────────────────────────
    Chest_X_Ray = models.IntegerField(
        choices=[(1, 'Suspect'), (2, 'Normal'), (3, 'Other Pathology'), (4, 'Not Performed'), (9, 'Ignored')],
        null=True, blank=True
    )

    # ── Dataset Column 6: Tuberculin_Test ────────────────────────────────
    Tuberculin_Test = models.IntegerField(
        choices=[(1, 'Reactor'), (2, 'Non-Reactor'), (3, 'Not Performed'), (4, 'Not Evaluated')],
        null=True, blank=True
    )

    # ── Dataset Column 7: Clinical_Form ──────────────────────────────────
    Clinical_Form = models.IntegerField(
        choices=[(1, 'Pulmonary'), (2, 'Extrapulmonary'), (3, 'Pulmonary+Extrapulmonary'), (9, 'Ignored')],
        null=True, blank=True
    )

    # ── Dataset Columns 8–12 & 34–35: 7 Comorbidities ────────────────────
    AIDS_Comorbidity           = models.IntegerField(choices=[(1, 'Yes'), (2, 'No'), (9, 'Ignored')], null=True, blank=True)
    Alcoholism_Comorbidity     = models.IntegerField(choices=[(1, 'Yes'), (2, 'No'), (9, 'Ignored')], null=True, blank=True)
    Diabetes_Comorbidity       = models.IntegerField(choices=[(1, 'Yes'), (2, 'No'), (9, 'Ignored')], null=True, blank=True)
    Mental_Disorder_Comorbidity= models.IntegerField(choices=[(1, 'Yes'), (2, 'No'), (9, 'Ignored')], null=True, blank=True)
    Other_Comorbidity          = models.IntegerField(choices=[(1, 'Yes'), (2, 'No'), (9, 'Ignored')], null=True, blank=True)
    Drug_Addiction_Comorbidity = models.IntegerField(choices=[(1, 'Yes'), (2, 'No'), (9, 'Ignored')], null=True, blank=True)
    Smoking_Comorbidity        = models.IntegerField(choices=[(1, 'Yes'), (2, 'No'), (9, 'Ignored')], null=True, blank=True)

    # ── Dataset Column 17: HIV ────────────────────────────────────────────
    HIV = models.IntegerField(
        choices=[(1, 'Positive'), (2, 'Negative'), (3, 'In Progress'), (4, 'Not Performed'), (9, 'Ignored')],
        null=True, blank=True
    )

    # ── Dataset Column 26: Occupational_Disease ──────────────────────────
    Occupational_Disease = models.IntegerField(
        choices=[(1, 'Yes'), (2, 'No'), (9, 'Ignored')],
        null=True, blank=True
    )

    # ── Dataset Column 36: State ──────────────────────────────────────────
    State = models.CharField(max_length=100, null=True, blank=True)

    # ── Dataset Column 38: Age ────────────────────────────────────────────
    Age = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.patient_id})"
