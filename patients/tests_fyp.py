from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from patients.models import Patient

class PatientManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.clinician_a = User.objects.create_user(username='clinician_a', password='p', role='CLINICIAN')
        self.clinician_b = User.objects.create_user(username='clinician_b', password='p', role='CLINICIAN')
        
    def test_T12_register_new_patient_valid(self):
        """T12: Register new patient with valid data."""
        self.client.force_login(self.clinician_a)
        data = {
            'name': 'John Doe',
            'Age': 45,
            'Sex': 1, # Male
            'Race': 1,
            'HIV': 4, # Negative
            'Clinical_Form': 1, # Pulmonary
            'Chest_X_Ray': 2, # Normal
        }
        resp = self.client.post(reverse('patient_create'), data)
        self.assertEqual(resp.status_code, 302) # Redirect to detail or list
        # Check ownership
        patient = Patient.objects.get(name='John Doe')
        self.assertEqual(patient.assigned_clinician, self.clinician_a)

    def test_T13_register_missing_required_fields(self):
        """T13: Validation error for missing required fields."""
        self.client.force_login(self.clinician_a)
        data = {'name': '', 'Age': 45} # Missing name
        resp = self.client.post(reverse('patient_create'), data)
        self.assertEqual(resp.status_code, 200) # Returns same form
        self.assertContains(resp, "field is required")

    def test_T14_clinician_isolation_IDOR(self):
        """T14: Clinician A cannot access Clinician B's patient via URL."""
        # Setup patient for B
        patient_b = Patient.objects.create(name="B's Patient", Age=50, assigned_clinician=self.clinician_b)
        
        # Login A
        self.client.force_login(self.clinician_a)
        
        # Try to view B's dashboard
        url = reverse('patient_dashboard', args=[patient_b.patient_id])
        resp = self.client.get(url)
        # Should be 404 (because we scoped the query with assigned_clinician)
        self.assertEqual(resp.status_code, 404)

    def test_T16_patient_list_filtering_own_only(self):
        """T16: Clinician A only sees their own patients in the list."""
        Patient.objects.create(name="Patient A", Age=30, assigned_clinician=self.clinician_a)
        Patient.objects.create(name="Patient B", Age=40, assigned_clinician=self.clinician_b)
        
        self.client.force_login(self.clinician_a)
        resp = self.client.get(reverse('patient_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Patient A")
        self.assertNotContains(resp, "Patient B")

    def test_T17_search_by_name(self):
        """T17: Search functionality works correctly."""
        Patient.objects.create(name="Unique Name Search", Age=30, assigned_clinician=self.clinician_a)
        self.client.force_login(self.clinician_a)
        resp = self.client.get(reverse('patient_list') + '?q=Unique')
        self.assertContains(resp, "Unique Name Search")
        
        # Negative search
        resp = self.client.get(reverse('patient_list') + '?q=NonExistent')
        self.assertNotContains(resp, "Unique Name Search")
