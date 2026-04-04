import time
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from accounts.models import User
from patients.models import Patient

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.clinician_pwd = 'testpassword123'
        self.clinician = User.objects.create_user(
            username='testclinician', 
            password=self.clinician_pwd, 
            role='CLINICIAN'
        )
        self.analyst = User.objects.create_user(
            username='testanalyst',
            password='analystpassword',
            role='ANALYST'
        )

    def test_T01_login_valid_credentials(self):
        """T01: Login with valid credentials redirects to correct dashboard."""
        resp = self.client.post(reverse('login'), {
            'username': 'testclinician', 
            'password': self.clinician_pwd
        }, follow=True)
        # Check redirect to patient list (default for clinician)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(reverse('patient_list'), [r[0] for r in resp.redirect_chain])

    def test_T02_login_wrong_password(self):
        """T02: Login with wrong password shows error."""
        resp = self.client.post(reverse('login'), {
            'username': 'testclinician', 
            'password': 'wrongpassword'
        }, follow=True)
        self.assertEqual(resp.status_code, 200) # Re-renders login page or redirected back to login
        self.assertContains(resp, "Incorrect username or password. Please try again.")

    def test_T03_access_protected_page_without_login(self):
        """T03: Access protected page without login redirects to login."""
        resp = self.client.get(reverse('patient_list'))
        self.assertRedirects(resp, f"{reverse('login')}?next={reverse('patient_list')}")

    @override_settings(SESSION_COOKIE_AGE=2) # 2 seconds for aggressive testing
    def test_T04_session_expiry(self):
        """T04: Session expires after inactivity (5-second trick simulated with 2s)."""
        self.client.login(username='testclinician', password=self.clinician_pwd)
        # Verify we are logged in
        resp = self.client.get(reverse('patient_list'))
        self.assertEqual(resp.status_code, 200)
        
        # Wait for expiry
        time.sleep(3)
        
        # Try again - should be logged out
        resp = self.client.get(reverse('patient_list'))
        self.assertEqual(resp.status_code, 302) # Redirect to login
        self.assertIn(reverse('login'), resp['Location'])

    def test_T05_logout_button(self):
        """T05: Logout button clears session and redirects."""
        self.client.login(username='testclinician', password=self.clinician_pwd)
        resp = self.client.post(reverse('logout'))
        self.assertRedirects(resp, reverse('login'))
        # Verify access is now denied
        resp = self.client.get(reverse('patient_list'))
        self.assertEqual(resp.status_code, 302)

class RBACTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.clinician = User.objects.create_user(username='c1', password='p', role='CLINICIAN')
        self.analyst = User.objects.create_user(username='a1', password='p', role='ANALYST')
        # Create a patient for testing
        self.patient = Patient.objects.create(
            name="Test Patient", 
            Age=30, 
            Sex=1, 
            assigned_clinician=self.clinician
        )

    def test_T06_clinician_accesses_analytics_directly(self):
        """T06: Clinician accessing analyst dashboard results in redirect/denial."""
        self.client.force_login(self.clinician)
        resp = self.client.get(reverse('analyst_dashboard'))
        # user_passes_test usually redirects to login or clinician_dashboard if fails
        self.assertIn(resp.status_code, [302, 403])

    def test_T07_analyst_accesses_registry_directly(self):
        """T07: Analyst accessing patient registry results in denial."""
        self.client.force_login(self.analyst)
        resp = self.client.get(reverse('patient_list'))
        self.assertIn(resp.status_code, [302, 403])

    def test_T08_analyst_accesses_patient_detail_directly(self):
        """T08: Analyst accessing specific patient detail is denied."""
        self.client.force_login(self.analyst)
        url = reverse('patient_dashboard', args=[self.patient.patient_id])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [302, 403])

    def test_T09_clinician_accesses_export_directly(self):
        """T09: Clinician accessing anonymized export is denied."""
        self.client.force_login(self.clinician)
        resp = self.client.get(reverse('export_anonymized_data'))
        self.assertIn(resp.status_code, [302, 403])
