import secrets
from datetime import timedelta

from django.db import models
from django.utils import timezone


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    is_confirmed = models.BooleanField(default=False)
    confirmation_token = models.CharField(max_length=64, unique=True)
    confirmation_sent_at = models.DateTimeField(null=True, blank=True)
    unsubscribe_token = models.CharField(max_length=64, unique=True)
    is_unsubscribed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Subskrybent"
        verbose_name_plural = "Subskrybenci"

    def __str__(self):
        return self.email

    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(32)

    def is_confirmation_expired(self):
        if self.confirmation_sent_at is None:
            return True
        return timezone.now() - self.confirmation_sent_at > timedelta(hours=24)
