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
        f"Czesc!\n\n"
        f"Dziekujemy za zapis do newslettera Kuchennej Komitywy.\n\n"
        f"Potwierdz swoj adres email klikajac w ponizszy link:\n"
        f"{confirm_url}\n\n"
        f"Link jest wazny przez 24 godziny.\n\n"
        f"Jesli to nie Ty sie zapisales/as, zignoruj "
        f"ta wiadomosc.\n\n"
        f"---\n"
        f"Jesli chcesz zrezygnowac z newslettera:\n"
        f"{unsubscribe_url}\n\n"
        f"Pozdrawiamy,\n"
        f"Kuchenna Komitywa"
    )

    email = EmailMessage(
        subject="Potwierdz zapis do newslettera"
        " -- Kuchenna Komitywa",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[subscriber.email],
    )
    email.send(fail_silently=False)
