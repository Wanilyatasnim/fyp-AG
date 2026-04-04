from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from patients.models import Patient

class SecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.clinician = User.objects.create_user(username='sec_clinician', password='p', role='CLINICIAN')
        self.patient = Patient.objects.create(name='Security Test', Age=40, assigned_clinician=self.clinician)
        
    def test_T44_submit_without_csrf(self):
        """T44: POST without CSRF token should be rejected (403)."""
        # Django's test Client handles CSRF by default, but we can bypass it to test
        client_no_csrf = Client(enforce_csrf_checks=True)
        resp = client_no_csrf.post(reverse('patient_create'), {'name': 'No CSRF'})
        self.assertEqual(resp.status_code, 403)

    def test_T46_manipulated_url_id_isolation(self):
        """T46: IDOR - Clinician cannot view another's patient by ID."""
        other_clinician = User.objects.create_user(username='other_doc', password='p', role='CLINICIAN')
        other_patient = Patient.objects.create(name='Other Patient', Age=30, assigned_clinician=other_clinician)
        
        self.client.force_login(self.clinician)
        url = reverse('patient_dashboard', args=[other_patient.patient_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404) # Not found in our scoped query

    def test_T45_sql_injection_sanitization(self):
        """T45: Input sanitization - SQLi attempt should be treated as literal string."""
        self.client.force_login(self.clinician)
        sqli_name = "Robert' OR '1'='1"
        data = {
            'name': sqli_name,
            'Age': 25,
            'Sex': 1,
            'Race': 1,
            'HIV': 4,
            'Clinical_Form': 1,
            'Chest_X_Ray': 2,
        }
        resp = self.client.post(reverse('patient_create'), data, follow=True)
        # Check if the name exists. We use contains because some systems might prefix 'Patient '
        p = Patient.objects.filter(name__contains=sqli_name).first()
        self.assertIsNotNone(p, f"SQLi input should be saved. Response code: {resp.status_code}")

    def test_T47_analyst_direct_prediction_api_call(self):
        """T47: Analyst cannot trigger prediction logic."""
        analyst = User.objects.create_user(username='analyst_hacker', password='p', role='ANALYST')
        self.client.force_login(analyst)
        url = reverse('generate_prediction', args=[self.patient.patient_id])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [302, 403])
