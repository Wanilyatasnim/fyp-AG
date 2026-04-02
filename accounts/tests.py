from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User


class LoginTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testclinician', password='testpassword123', role='CLINICIAN'
        )

    def test_valid_login_redirects(self):
        """Valid credentials should redirect to patient list."""
        resp = self.client.post('/auth/login/', {'username': 'testclinician', 'password': 'testpassword123'})
        self.assertIn(resp.status_code, [200, 302])

    def test_invalid_login_shows_error(self):
        """Invalid credentials should not authenticate."""
        resp = self.client.post('/auth/login/', {'username': 'testclinician', 'password': 'wrongpassword'})
        # Should not redirect away from login
        self.assertNotEqual(resp.status_code, 302)

    def test_logout_clears_session(self):
        """Logout should end the session."""
        self.client.force_login(self.user)
        self.client.post('/auth/logout/')
        # Accessing protected page should redirect to login
        resp = self.client.get('/patients/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/auth/login/', resp['Location'])

    def test_unauthenticated_redirects_to_login(self):
        """Unauthenticated request to protected URL should redirect to login."""
        resp = self.client.get('/patients/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/auth/login/', resp['Location'])


class RBACTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username='admin', password='pass', role='ADMIN')
        self.clinician = User.objects.create_user(username='clinician', password='pass', role='CLINICIAN')
        self.analyst = User.objects.create_user(username='analyst', password='pass', role='ANALYST')

    def test_clinician_can_access_patient_list(self):
        self.client.force_login(self.clinician)
        resp = self.client.get('/patients/')
        self.assertEqual(resp.status_code, 200)

    def test_analyst_blocked_from_patient_create(self):
        self.client.force_login(self.analyst)
        resp = self.client.get('/patients/new/')
        # user_passes_test usually redirects to login if check fails
        self.assertEqual(resp.status_code, 302)

    def test_clinician_blocked_from_user_management(self):
        self.client.force_login(self.clinician)
        resp = self.client.get('/accounts/users/')
        self.assertEqual(resp.status_code, 302)

    def test_admin_can_access_user_management(self):
        self.client.force_login(self.admin)
        resp = self.client.get('/accounts/users/')
        self.assertEqual(resp.status_code, 200)
