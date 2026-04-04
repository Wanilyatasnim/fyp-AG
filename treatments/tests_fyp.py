from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from patients.models import Patient
from treatments.models import Treatment

class FollowUpTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.clinician = User.objects.create_user(username='treatment_clinician', password='p', role='CLINICIAN')
        self.patient = Patient.objects.create(name='Follow-up Test', Age=40, assigned_clinician=self.clinician)
        
    def test_T19_record_month_1_follow_up(self):
        """T19: Recording month 1 follow-up saves data correctly."""
        self.client.force_login(self.clinician)
        url = reverse('add_monitoring_visit', args=[self.patient.patient_id])
        data = {
            'visit_month': 1,
            'bacilloscopy_result': 1, # Positive
            'weight': 65.5,
            'rifampicin': 1, # Yes
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302)
        # Check database
        treatment = Treatment.objects.filter(patient=self.patient, visit_month=1).first()
        self.assertIsNotNone(treatment)
        self.assertEqual(treatment.bacilloscopy_result, 1)

    def test_T20_invalid_follow_up_values(self):
        """T20: Negative weight should fail validation."""
        self.client.force_login(self.clinician)
        url = reverse('add_monitoring_visit', args=[self.patient.patient_id])
        data = {
            'visit_month': 1,
            'weight': -10.0, # INVALID
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200) # Form re-renders
        self.assertContains(resp, "greater than zero")

    def test_T21_duplicate_month_prevention(self):
        """T21: Prevent duplicate follow-up for same month."""
        Treatment.objects.create(patient=self.patient, visit_month=2)
        self.client.force_login(self.clinician)
        url = reverse('add_monitoring_visit', args=[self.patient.patient_id])
        data = {'visit_month': 2}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "already exists for this month")

    def test_T22_follow_up_appears_in_timeline(self):
        """T22: Recorded data is visible on patient detail page."""
        Treatment.objects.create(patient=self.patient, visit_month=3, bacilloscopy_result=2) # Negative
        self.client.force_login(self.clinician)
        url = reverse('patient_dashboard', args=[self.patient.patient_id])
        resp = self.client.get(url)
        self.assertContains(resp, "month") # Month chart data
        self.assertContains(resp, "3") # Month 3
