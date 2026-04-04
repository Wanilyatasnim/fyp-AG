import csv
import io
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from patients.models import Patient

class AnalystAnonymizationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.analyst = User.objects.create_user(username='analyst_user', password='p', role='ANALYST')
        self.clinician = User.objects.create_user(username='clinician_user', password='p', role='CLINICIAN')
        self.patient = Patient.objects.create(
            name='Sensitive Patient Name',
            Age=45,
            Sex=1,
            assigned_clinician=self.clinician
        )

    def test_T34_no_patient_names_visible_on_analyst_dashboard(self):
        """T34: Identify no patient names on analyst dashboard."""
        self.client.force_login(self.analyst)
        resp = self.client.get(reverse('analyst_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'Sensitive Patient Name')
        self.assertNotContains(resp, 'clinician_user')

    def test_T37_export_contains_no_names_or_ids(self):
        """T37: Exported CSV must be anonymized (No Names/ID)."""
        self.client.force_login(self.analyst)
        resp = self.client.get(reverse('export_anonymized_data'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/csv')
        
        content = resp.content.decode('utf-8')
        # Check header
        self.assertIn('Age', content)
        self.assertIn('Sex', content)
        # Check absence of PII
        self.assertNotIn('name', content.lower())
        self.assertNotIn('Sensitive Patient Name', content)
        
        # Verify data count
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        # Header + 1 patient row
        self.assertEqual(len(rows), 2)

    def test_T38_correct_anonymized_fields(self):
        """T38: Export contains only demographics and risk outcome."""
        self.client.force_login(self.analyst)
        resp = self.client.get(reverse('export_anonymized_data'))
        content = resp.content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))
        row = next(reader)
        
        # Check for allowed keys
        # The view should use .values('Age', 'Sex', 'Race', 'HIV', 'Clinical_Form', 'Chest_X_Ray', 'predictions__risk_score')
        allowed_keys = ['Age', 'Sex', 'Race', 'HIV', 'Clinical_Form', 'Chest_X_Ray', 'risk_score', 'risk_category']
        for key in row.keys():
            # Check for partial matches to ignore casing or Prediction prefix
            self.assertTrue(any(ak in key for ak in allowed_keys), f"Identify leaked field: {key}")
            
    def test_T31_analyst_dashboard_loads(self):
        """T31: Analytics dashboard loads correctly with charts."""
        self.client.force_login(self.analyst)
        resp = self.client.get(reverse('analyst_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Population Analytics")
        self.assertContains(resp, "riskPieChart") # Check for Chart.js canvases
