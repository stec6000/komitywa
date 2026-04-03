from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from newsletter.models import Subscriber


class SubscriberModelTests(TestCase):

    def test_generate_token_length(self):
        token = Subscriber.generate_token()
        self.assertIsInstance(token, str)
        self.assertGreaterEqual(len(token), 32)

    def test_creation_defaults(self):
        sub = Subscriber.objects.create(
            email="test@example.com",
            confirmation_token=Subscriber.generate_token(),
            unsubscribe_token=Subscriber.generate_token(),
        )
        self.assertFalse(sub.is_confirmed)
        self.assertFalse(sub.is_unsubscribed)

    def test_str_returns_email(self):
        sub = Subscriber(email="hello@example.com")
        self.assertEqual(str(sub), "hello@example.com")

    def test_is_confirmation_expired_when_none(self):
        sub = Subscriber(
            email="x@example.com",
            confirmation_sent_at=None,
        )
        self.assertTrue(sub.is_confirmation_expired())

    def test_is_confirmation_expired_when_old(self):
        sub = Subscriber(
            email="x@example.com",
            confirmation_sent_at=timezone.now() - timedelta(hours=25),
        )
        self.assertTrue(sub.is_confirmation_expired())

    def test_is_confirmation_not_expired_when_recent(self):
        sub = Subscriber(
            email="x@example.com",
            confirmation_sent_at=timezone.now() - timedelta(hours=23),
        )
        self.assertFalse(sub.is_confirmation_expired())

    def test_email_unique_constraint(self):
        Subscriber.objects.create(
            email="dup@example.com",
            confirmation_token=Subscriber.generate_token(),
            unsubscribe_token=Subscriber.generate_token(),
        )
        with self.assertRaises(Exception):
            Subscriber.objects.create(
                email="dup@example.com",
                confirmation_token=Subscriber.generate_token(),
                unsubscribe_token=Subscriber.generate_token(),
            )
