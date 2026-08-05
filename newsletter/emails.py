from django.conf import settings
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils import timezone


def send_confirmation_email(subscriber, request):
    confirm_url = request.build_absolute_uri(
        reverse(
            "newsletter:confirm",
            args=[subscriber.confirmation_token],
        )
    )
    unsubscribe_url = request.build_absolute_uri(
        reverse(
            "newsletter:unsubscribe",
            args=[subscriber.unsubscribe_token],
        )
    )

    subscriber.confirmation_sent_at = timezone.now()
    subscriber.save(update_fields=["confirmation_sent_at"])

    body = (
        f"Cze\u015b\u0107!\n\n"
        f"Dzi\u0119kujemy za zapis na Listy z Komitywy.\n\n"
        f"Potwierd\u017a sw\u00f3j adres email klikaj\u0105c w poni\u017cszy link:\n"
        f"{confirm_url}\n\n"
        f"Link jest wa\u017cny przez 24 godziny.\n\n"
        f"Je\u015bli to nie Ty si\u0119 zapisa\u0142e\u015b/a\u015b, zignoruj "
        f"t\u0119 wiadomo\u015b\u0107.\n\n"
        f"--\n"
        f"Je\u015bli chcesz zrezygnowa\u0107 z List\u00f3w z Komitywy:\n"
        f"{unsubscribe_url}\n\n"
        f"- \n"
        f"Kuchenna Komitywa\n"
        f"https://kuchennakomitywa.pl"
    )

    email = EmailMessage(
        subject="Potwierd\u017a zapis na Listy z Komitywy",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[subscriber.email],
    )
    email.send(fail_silently=False)
