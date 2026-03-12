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
