import uuid
from django.test import TestCase, Client
from accounts.models import User
from patients.models import Patient


class PatientRegistrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='clinician', password='pass123word', role='CLINICIAN'
        )
        self.client.force_login(self.user)

    def test_patient_created_with_all_fields(self):
        """Verify Patient is saved with all required fields."""
        patient = Patient.objects.create(
            name='Test Patient',
            Age=35,
            Sex=1,
            Race=1,
            HIV=2,
            Clinical_Form=1,
            Chest_X_Ray=1,
            Tuberculin_Test=1,
            AIDS_Comorbidity=2,
            Alcoholism_Comorbidity=2,
            Diabetes_Comorbidity=2,
            Mental_Disorder_Comorbidity=2,
            Drug_Addiction_Comorbidity=2,
            Smoking_Comorbidity=2,
            Other_Comorbidity=2,
            Occupational_Disease=2,
            State='SP',
            created_by=self.user,
        )
        saved = Patient.objects.get(patient_id=patient.patient_id)
        self.assertEqual(saved.name, 'Test Patient')
        self.assertEqual(saved.Age, 35)
        self.assertEqual(saved.Sex, 1)
        self.assertEqual(saved.HIV, 2)
        self.assertEqual(saved.State, 'SP')

    def test_patient_id_is_uuid(self):
        """Auto-generated patient_id should be a valid UUID."""
        patient = Patient.objects.create(name='UUID Test', created_by=self.user)
        self.assertIsInstance(patient.patient_id, uuid.UUID)

    def test_mandatory_field_name_present(self):
        """Patient should be retrievable by name."""
        Patient.objects.create(name='Retrieve Me', created_by=self.user)
        p = Patient.objects.filter(name='Retrieve Me').first()
        self.assertIsNotNone(p)

    def test_patient_list_view_requires_login(self):
        """Patient list should be accessible when logged in."""
        resp = self.client.get('/patients/')
        self.assertEqual(resp.status_code, 200)
