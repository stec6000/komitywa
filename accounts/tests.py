from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(
    ACCOUNT_EMAIL_VERIFICATION="none",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class AccountsAuthTests(TestCase):
    def setUp(self):
        self.register_url = reverse("rest_register")
        self.login_url = reverse("rest_login")
        self.user_model = get_user_model()

    def test_register_success(self):
        response = self.client.post(
            self.register_url,
            {
                "email": "user1@example.com",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
            },
        )
        self.assertIn(response.status_code, (201, 204))
        self.assertTrue(
            self.user_model.objects.filter(email__iexact="user1@example.com").exists()
        )

    def test_register_duplicate_email_returns_400(self):
        self.user_model.objects.create_user(
            email="dup@example.com",
            password="StrongPass123",
        )
        response = self.client.post(
            self.register_url,
            {
                "email": "dup@example.com",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_register_password_mismatch_returns_400(self):
        response = self.client.post(
            self.register_url,
            {
                "email": "user2@example.com",
                "password1": "StrongPass123",
                "password2": "DifferentPass123",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_login_success(self):
        self.user_model.objects.create_user(
            email="login@example.com",
            password="StrongPass123",
        )
        response = self.client.post(
            self.login_url,
            {
                "email": "login@example.com",
                "password": "StrongPass123",
            },
        )
        self.assertEqual(response.status_code, 200)
        if response.content:
            data = response.json()
            self.assertIn("key", data)

    def test_login_invalid_credentials_returns_400(self):
        self.user_model.objects.create_user(
            email="badlogin@example.com",
            password="StrongPass123",
        )
        response = self.client.post(
            self.login_url,
            {
                "email": "badlogin@example.com",
                "password": "WrongPass123",
            },
        )
        self.assertEqual(response.status_code, 400)
