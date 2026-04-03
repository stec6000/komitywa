from datetime import timedelta

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from newsletter.models import Subscriber


class SubscribeViewTests(TestCase):

    def test_get_redirects_to_home(self):
        response = self.client.get(reverse("newsletter:subscribe"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))

    def test_post_valid_creates_subscriber_and_redirects(self):
        response = self.client.post(
            reverse("newsletter:subscribe"),
            {"email": "new@example.com", "consent_newsletter": "on"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("newsletter:check_email"), response.url,
        )
        self.assertTrue(
            Subscriber.objects.filter(email="new@example.com").exists()
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_post_confirmed_email_redirects_silently(self):
        Subscriber.objects.create(
            email="confirmed@example.com",
            confirmation_token=Subscriber.generate_token(),
            unsubscribe_token=Subscriber.generate_token(),
            is_confirmed=True,
        )
        response = self.client.post(
            reverse("newsletter:subscribe"),
            {"email": "confirmed@example.com", "consent_newsletter": "on"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Subscriber.objects.count(), 1)

    def test_post_pending_email_resends_confirmation(self):
        Subscriber.objects.create(
            email="pending@example.com",
            confirmation_token=Subscriber.generate_token(),
            unsubscribe_token=Subscriber.generate_token(),
            is_confirmed=False,
            confirmation_sent_at=timezone.now() - timedelta(hours=25),
        )
        response = self.client.post(
            reverse("newsletter:subscribe"),
            {"email": "pending@example.com", "consent_newsletter": "on"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)

    def test_post_unsubscribed_email_resubscribes(self):
        sub = Subscriber.objects.create(
            email="unsub@example.com",
            confirmation_token=Subscriber.generate_token(),
            unsubscribe_token=Subscriber.generate_token(),
            is_confirmed=True,
            is_unsubscribed=True,
        )
        response = self.client.post(
            reverse("newsletter:subscribe"),
            {"email": "unsub@example.com", "consent_newsletter": "on"},
        )
        self.assertEqual(response.status_code, 302)
        sub.refresh_from_db()
        self.assertFalse(sub.is_unsubscribed)
        self.assertFalse(sub.is_confirmed)
        self.assertEqual(len(mail.outbox), 1)


class ConfirmViewTests(TestCase):

    def test_valid_unexpired_token_confirms(self):
        sub = Subscriber.objects.create(
            email="c@example.com",
            confirmation_token="valid-token-123",
            unsubscribe_token=Subscriber.generate_token(),
            confirmation_sent_at=timezone.now(),
        )
        response = self.client.get(
            reverse("newsletter:confirm", args=["valid-token-123"])
        )
        self.assertEqual(response.status_code, 200)
        sub.refresh_from_db()
        self.assertTrue(sub.is_confirmed)

    def test_expired_token_shows_expired(self):
        Subscriber.objects.create(
            email="exp@example.com",
            confirmation_token="expired-token-123",
            unsubscribe_token=Subscriber.generate_token(),
            confirmation_sent_at=timezone.now() - timedelta(hours=25),
        )
        response = self.client.get(
            reverse("newsletter:confirm", args=["expired-token-123"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "newsletter/link_expired.html")

    def test_invalid_token_returns_404(self):
        response = self.client.get(
            reverse("newsletter:confirm", args=["nonexistent"])
        )
        self.assertEqual(response.status_code, 404)


class UnsubscribeViewTests(TestCase):

    def test_valid_token_unsubscribes(self):
        sub = Subscriber.objects.create(
            email="u@example.com",
            confirmation_token=Subscriber.generate_token(),
            unsubscribe_token="unsub-token-123",
            is_confirmed=True,
        )
        response = self.client.get(
            reverse("newsletter:unsubscribe", args=["unsub-token-123"])
        )
        self.assertEqual(response.status_code, 200)
        sub.refresh_from_db()
        self.assertTrue(sub.is_unsubscribed)

    def test_already_unsubscribed_renders_message(self):
        Subscriber.objects.create(
            email="au@example.com",
            confirmation_token=Subscriber.generate_token(),
            unsubscribe_token="already-unsub-token",
            is_confirmed=True,
            is_unsubscribed=True,
        )
        response = self.client.get(
            reverse("newsletter:unsubscribe", args=["already-unsub-token"])
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_token_returns_404(self):
        response = self.client.get(
            reverse("newsletter:unsubscribe", args=["nonexistent"])
        )
        self.assertEqual(response.status_code, 404)
