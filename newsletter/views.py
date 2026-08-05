import logging

from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .captcha import get_client_ip, verify_turnstile
from .emails import send_confirmation_email
from .forms import NewsletterSignupForm
from .models import Subscriber


log = logging.getLogger("newsletter.security")


def subscribe(request):
    if request.method != "POST":
        return redirect("home")

    form = NewsletterSignupForm(request.POST)
    if not form.is_valid():
        # Honeypot triggers form error on `website`; silent reject.
        if "website" in form.errors:
            log.info(
                "Newsletter signup rejected: honeypot ip=%s",
                get_client_ip(request),
            )
        else:
            messages.error(
                request,
                "Nie udało się zapisać na Listy z Komitywy. "
                "Sprawdź adres e-mail i zaznacz zgodę.",
            )
        return redirect("home")

    # Cloudflare Turnstile verification (graceful skip when not configured).
    turnstile_token = request.POST.get("cf-turnstile-response", "")
    ok, reason = verify_turnstile(turnstile_token, get_client_ip(request))
    if not ok:
        log.info(
            "Newsletter signup rejected: turnstile=%s ip=%s",
            reason,
            get_client_ip(request),
        )
        messages.error(
            request,
            "Nie udało się potwierdzić, że formularz wysyła człowiek. "
            "Spróbuj ponownie za chwilę.",
        )
        return redirect("home")

    email = form.cleaned_data["email"]

    try:
        existing = Subscriber.objects.filter(email=email).first()

        if existing:
            if existing.is_confirmed and not existing.is_unsubscribed:
                # Already confirmed - silent redirect
                return redirect(reverse("newsletter:check_email"))

            if existing.is_unsubscribed:
                # Re-subscribe: reset state, send new confirmation
                existing.is_unsubscribed = False
                existing.is_confirmed = False
                existing.confirmation_token = Subscriber.generate_token()
                existing.save(
                    update_fields=[
                        "is_unsubscribed",
                        "is_confirmed",
                        "confirmation_token",
                    ]
                )
                send_confirmation_email(existing, request)
                return redirect(reverse("newsletter:check_email"))

            # Pending (unconfirmed) - resend confirmation
            send_confirmation_email(existing, request)
            return redirect(reverse("newsletter:check_email"))

        # New subscriber
        subscriber = Subscriber.objects.create(
            email=email,
            confirmation_token=Subscriber.generate_token(),
            unsubscribe_token=Subscriber.generate_token(),
        )
        send_confirmation_email(subscriber, request)
        return redirect(reverse("newsletter:check_email"))

    except IntegrityError:
        # Race condition: another request created the same email
        return redirect(reverse("newsletter:check_email"))


def check_email(request):
    return render(
        request,
        "newsletter/check_email.html",
        {"hide_newsletter": True},
    )


def confirm(request, token):
    subscriber = get_object_or_404(
        Subscriber, confirmation_token=token,
    )

    if subscriber.is_confirmation_expired():
        return render(
            request,
            "newsletter/link_expired.html",
            {"hide_newsletter": True},
        )

    subscriber.is_confirmed = True
    subscriber.save(update_fields=["is_confirmed"])
    return render(
        request,
        "newsletter/confirmed.html",
        {"hide_newsletter": True},
    )


def unsubscribe(request, token):
    subscriber = get_object_or_404(
        Subscriber, unsubscribe_token=token,
    )

    if subscriber.is_unsubscribed:
        return render(
            request,
            "newsletter/unsubscribed.html",
            {
                "already_unsubscribed": True,
                "hide_newsletter": True,
            },
        )

    subscriber.is_unsubscribed = True
    subscriber.save(update_fields=["is_unsubscribed"])
    return render(
        request,
        "newsletter/unsubscribed.html",
        {"hide_newsletter": True},
    )
