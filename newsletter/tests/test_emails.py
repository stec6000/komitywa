from django.core import mail
from django.test import TestCase, RequestFactory
from django.utils import timezone

from newsletter.emails import send_confirmation_email
from newsletter.models import Subscriber


class SendConfirmationEmailTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.META["SERVER_NAME"] = "testserver"
        self.request.META["SERVER_PORT"] = "80"
        self.subscriber = Subscriber.objects.create(
            email="sub@example.com",
            confirmation_token=Subscriber.generate_token(),
            unsubscribe_token=Subscriber.generate_token(),
        )

    def test_sends_one_email(self):
        send_confirmation_email(self.subscriber, self.request)
        self.assertEqual(len(mail.outbox), 1)

    def test_subject_contains_potwierdz_zapis(self):
        send_confirmation_email(self.subscriber, self.request)
        self.assertIn("Potwierdź zapis", mail.outbox[0].subject)

    def test_body_contains_confirmation_url(self):
        send_confirmation_email(self.subscriber, self.request)
        body = mail.outbox[0].body
        self.assertIn(self.subscriber.confirmation_token, body)
        self.assertIn("/newsletter/potwierdz/", body)

    def test_body_contains_unsubscribe_url(self):
        send_confirmation_email(self.subscriber, self.request)
        body = mail.outbox[0].body
        self.assertIn(self.subscriber.unsubscribe_token, body)
        self.assertIn("/newsletter/wypisz/", body)

    def test_updates_confirmation_sent_at(self):
        self.assertIsNone(self.subscriber.confirmation_sent_at)
        send_confirmation_email(self.subscriber, self.request)
        self.subscriber.refresh_from_db()
        self.assertIsNotNone(self.subscriber.confirmation_sent_at)
