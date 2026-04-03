# Phase 6: Newsletter - Research

**Researched:** 2026-04-03
**Domain:** Django newsletter subscription with double opt-in and unsubscribe
**Confidence:** HIGH

## Summary

Phase 6 implements a self-contained newsletter subscription system as a new `newsletter` Django app. The scope is narrow: a signup form with RODO consent, double opt-in email confirmation via tokenized links, and one-click unsubscribe. No bulk sending, campaigns, or segmentation (those are v2).

The implementation is straightforward Django: a `Subscriber` model, three views (subscribe POST handler, confirm GET, unsubscribe GET), two email templates (confirmation), and a form rendered above the footer in `base.html`. The project already has a working email backend (console in dev, SMTP config ready via django-environ), plain-text email patterns in `shop/emails.py`, Bootstrap 5 form styling, and POST-redirect-GET patterns in `shop/views.py`. No new dependencies are needed.

**Primary recommendation:** Build everything with Django stdlib -- `secrets.token_urlsafe()` for tokens, `django.core.mail.EmailMessage` for emails, standard model/view/template pattern. No third-party newsletter library needed for this scope.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Newsletter signup form is a distinct section above the footer, not inside `.kk-footer`. It sits between page content and the existing footer bar -- visually separated, more prominent.
- **D-02:** Form fields: email input + RODO consent checkbox ("Wyrazam zgode na otrzymywanie newslettera" with link to polityka prywatnosci). Checkbox is required before submission.
- **D-03:** Form submission: standard Django full-page POST (no AJAX/JS). On success, redirect to `/newsletter/sprawdz-email/` -- a page saying "Wyslalismy link potwierdzajacy na [email]. Kliknij go, zeby dokonczyc zapis."
- **D-04:** After form submission, send confirmation email with a tokenized link. User must click to activate subscription (RODO compliance). Claude's discretion on token implementation and expiry (24h is standard).
- **D-05:** If user submits the form with an already-subscribed email (confirmed), silently redirect to the "sprawdz email" page -- do not reveal subscription status (privacy). If pending (unconfirmed), resend the confirmation email.
- **D-06:** One-click immediate unsubscribe -- `GET /newsletter/wypisz/<token>/` immediately marks subscriber as unsubscribed, then renders "Zostales wypisany z newslettera" page. No confirmation step.
- **D-07:** Unsubscribe is idempotent -- clicking the same token a second time renders "Zostales juz wypisany" without errors.
- **D-08:** Unsubscribe token included in: the double opt-in confirmation email. Future newsletter emails should also include the same unsubscribe URL pattern.

### Claude's Discretion
- App structure: new `newsletter` Django app (separate from `core`)
- Subscriber model fields: email, confirmed (bool), confirmation_token, unsubscribe_token, created_at
- Token generation: `secrets.token_urlsafe()` or UUID4
- Confirmation token expiry: 24h standard; expired token shows "link wygasl" with option to re-enter email
- Admin interface: standard Django admin with subscriber list (email, confirmed status, date)
- Email copy: warm Polish tone per Phase 5 D-13; subject lines in Polish

### Deferred Ideas (OUT OF SCOPE)
None raised during discussion. Also explicitly out of scope per CONTEXT.md domain boundary: bulk newsletter sending, campaign management, subscriber segmentation, admin send UI (NEWS-V2-01, NEWS-V2-02).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| NEWS-01 | Uzytkownik moze zapisac sie na newsletter przez formularz w stopce strony | Form placement above footer (D-01), email + RODO checkbox (D-02), POST-redirect-GET (D-03), privacy-preserving duplicate handling (D-05) |
| NEWS-02 | Uzytkownik otrzymuje email z potwierdzeniem zapisu (double opt-in) | Tokenized confirmation link (D-04), `secrets.token_urlsafe()` generation, 24h expiry, plain-text email via `EmailMessage` |
| NEWS-03 | Uzytkownik moze wypisac sie z newslettera | One-click GET unsubscribe (D-06), idempotent (D-07), token in all emails (D-08) |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django | 5.2.12 | Web framework (already installed) | Project stack |
| `secrets` | stdlib | Token generation (`token_urlsafe`) | Cryptographically secure, no deps |
| `django.core.mail` | built-in | Email sending (`EmailMessage`) | Already used in `shop/emails.py` |
| `django.utils.timezone` | built-in | Token expiry timestamps | Standard Django time handling |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Bootstrap 5.3 | CDN (already loaded) | Form styling, newsletter section layout | All templates |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom subscriber model | django-newsletter | Overkill for v1 scope (subscribe/confirm/unsubscribe only); adds complexity for campaign features we explicitly defer |
| Custom subscriber model | mailchimp/sendinblue API | External dependency, GDPR concerns with data leaving EU, not needed for v1 |
| `secrets.token_urlsafe()` | `uuid.uuid4()` | Both work; `secrets` produces shorter URL-safe tokens (32 chars vs 36) and is designed for security tokens |

**Installation:**
```bash
# No new packages needed -- all stdlib/Django built-in
```

## Architecture Patterns

### Recommended Project Structure
```
newsletter/
    __init__.py
    admin.py
    apps.py
    emails.py          # send_confirmation_email()
    forms.py           # NewsletterSignupForm (email + consent checkbox)
    models.py          # Subscriber model
    migrations/
        __init__.py
        0001_initial.py
    tests/
        __init__.py
        test_models.py
        test_views.py
        test_emails.py
    urls.py            # newsletter/ URL patterns
    views.py           # subscribe, confirm, unsubscribe views
templates/
    newsletter/
        check_email.html       # "Sprawdz email" page after signup
        confirmed.html         # "Zapis potwierdzony" after clicking confirm link
        unsubscribed.html      # "Wypisano" after clicking unsubscribe
        link_expired.html      # "Link wygasl" for expired confirmation token
    includes/
        _newsletter_signup.html  # Newsletter section (included in base.html)
```

### Pattern 1: Subscriber Model with Dual Tokens
**What:** Single model with separate confirmation and unsubscribe tokens. Confirmation token has expiry; unsubscribe token is permanent.
**When to use:** Always -- this is the core data model.
**Example:**
```python
# Source: Project conventions (shop/models.py pattern)
import secrets
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
        if not self.confirmation_sent_at:
            return True
        return timezone.now() - self.confirmation_sent_at > timezone.timedelta(hours=24)
```

### Pattern 2: POST-Redirect-GET for Subscription
**What:** Form POST creates/updates subscriber, sends email, redirects to confirmation page. Follows existing `shop/views.py` checkout pattern.
**When to use:** Subscribe view.
**Example:**
```python
# Source: shop/views.py checkout pattern
from django.shortcuts import redirect, render
from .forms import NewsletterSignupForm
from .models import Subscriber
from .emails import send_confirmation_email


def subscribe(request):
    if request.method == "POST":
        form = NewsletterSignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            # Privacy: same response regardless of subscription state (D-05)
            subscriber, created = Subscriber.objects.get_or_create(
                email=email,
                defaults={
                    "confirmation_token": Subscriber.generate_token(),
                    "unsubscribe_token": Subscriber.generate_token(),
                },
            )
            if not created and not subscriber.is_confirmed:
                # Resend confirmation for pending subscriber
                subscriber.confirmation_token = Subscriber.generate_token()
                subscriber.save(update_fields=["confirmation_token", "confirmation_sent_at"])
            if not subscriber.is_confirmed:
                send_confirmation_email(subscriber, request)
            # Always redirect -- privacy (D-05)
            return redirect("newsletter:check_email")
    # GET requests to the subscribe URL redirect home (form is in footer)
    return redirect("home")
```

### Pattern 3: Newsletter Section as Include Template
**What:** Newsletter signup section as a reusable `{% include %}` in `base.html`, placed between `</main>` and the footer include.
**When to use:** Global site layout.
**Example:**
```html
{# base.html modification #}
    </main>

    {% include "includes/_newsletter_signup.html" %}

    {% include "includes/_footer.html" %}
```

### Anti-Patterns to Avoid
- **Revealing subscription status:** Never show "this email is already subscribed" -- always redirect to the same "check your email" page (D-05, privacy).
- **Confirmation on GET without token:** The subscribe form MUST be POST only. GET to `/newsletter/` should redirect home.
- **Mutable unsubscribe tokens:** The unsubscribe token is generated once and never changes. It must remain stable across re-subscriptions (if ever allowed).
- **JavaScript form submission:** D-03 explicitly requires standard Django full-page POST. No AJAX.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Secure tokens | Custom random strings | `secrets.token_urlsafe(32)` | Cryptographically secure, URL-safe, stdlib |
| Email sending | Raw SMTP | `django.core.mail.EmailMessage` | Already configured, handles settings |
| CSRF protection | Manual token checking | Django `{% csrf_token %}` + middleware | Already enabled in middleware |
| Form validation | Manual field checking | Django `forms.Form` with field validators | Consistent with `shop/forms.py` pattern |

**Key insight:** This phase has no deceptively complex problems. The entire feature is standard Django CRUD + email, following established project patterns.

## Common Pitfalls

### Pitfall 1: Email Uniqueness Race Condition
**What goes wrong:** Two simultaneous form submissions with the same email cause IntegrityError on the unique email constraint.
**Why it happens:** `get_or_create` is not fully atomic under high concurrency.
**How to avoid:** Wrap in try/except IntegrityError -- if it fires, fetch the existing subscriber and proceed with the resend logic.
**Warning signs:** 500 errors on form submission in production.

### Pitfall 2: CSRF Token Missing in Newsletter Form
**What goes wrong:** The newsletter form is in an include template that might not be inside a `<form>` tag with `{% csrf_token %}`.
**Why it happens:** Include templates can be tricky -- the form must POST to the newsletter subscribe URL and include CSRF.
**How to avoid:** The include template must contain the complete `<form>` tag with `{% csrf_token %}`, `method="POST"`, and `action="{% url 'newsletter:subscribe' %}"`.
**Warning signs:** 403 Forbidden on form submission.

### Pitfall 3: Token Collision
**What goes wrong:** Two subscribers get the same token (astronomically unlikely with `token_urlsafe(32)` but the unique constraint will catch it).
**Why it happens:** Random generation.
**How to avoid:** Model has `unique=True` on both token fields. If `IntegrityError` on creation, regenerate token and retry.
**Warning signs:** IntegrityError during subscriber creation.

### Pitfall 4: Expired Token UX Dead End
**What goes wrong:** User clicks expired confirmation link and sees an error with no way forward.
**Why it happens:** 24h expiry passed, no re-subscribe option presented.
**How to avoid:** The "link expired" page must include a clear message and a way to re-enter email (link back to home or inline form).
**Warning signs:** User complaints about inability to subscribe.

### Pitfall 5: Newsletter Form Action URL Not Available
**What goes wrong:** The `{% url 'newsletter:subscribe' %}` tag fails because the newsletter app URLs are not yet registered.
**Why it happens:** Forgetting to add the newsletter URL include to `backend/urls.py` and `"newsletter"` to `INSTALLED_APPS`.
**How to avoid:** Checklist: (1) add to INSTALLED_APPS, (2) add URL include, (3) run migrations.
**Warning signs:** `NoReverseMatch` error on any page (since the form is in base.html).

### Pitfall 6: Unsubscribed Subscriber Re-subscribing
**What goes wrong:** A user who unsubscribed tries to sign up again. The email already exists with `is_unsubscribed=True`.
**Why it happens:** `get_or_create` finds existing record.
**How to avoid:** Handle the re-subscribe case explicitly: if unsubscribed, reset `is_unsubscribed=False`, `is_confirmed=False`, generate new confirmation token, send confirmation email.
**Warning signs:** Unsubscribed users cannot re-subscribe.

## Code Examples

### Newsletter Signup Form
```python
# Source: shop/forms.py pattern
from django import forms


class NewsletterSignupForm(forms.Form):
    email = forms.EmailField(
        label="Adres email",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Twoj adres email",
        }),
    )
    consent_newsletter = forms.BooleanField(
        label='Wyrazam zgode na otrzymywanie newslettera. '
              '<a href="/polityka-prywatnosci/" target="_blank">'
              'Polityka prywatnosci</a>',
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
```

### Confirmation Email (Plain Text)
```python
# Source: shop/emails.py pattern
from django.conf import settings
from django.core.mail import EmailMessage


def send_confirmation_email(subscriber, request):
    confirm_url = request.build_absolute_uri(
        f"/newsletter/potwierdz/{subscriber.confirmation_token}/"
    )
    unsubscribe_url = request.build_absolute_uri(
        f"/newsletter/wypisz/{subscriber.unsubscribe_token}/"
    )

    body = (
        "Czesc!\n\n"
        "Dziekujemy za zapis do newslettera Kuchennej Komitywy!\n\n"
        "Kliknij ponizszy link, zeby potwierdzic subskrypcje:\n"
        f"{confirm_url}\n\n"
        "Link jest wazny przez 24 godziny.\n\n"
        "Jesli nie zapisywales/as sie na newsletter, zignoruj ta wiadomosc.\n\n"
        "Pozdrawiamy,\n"
        "Kuchenna Komitywa\n\n"
        "---\n"
        f"Wypisz sie z newslettera: {unsubscribe_url}"
    )

    email = EmailMessage(
        subject="Potwierdz zapis do newslettera -- Kuchenna Komitywa",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[subscriber.email],
    )
    subscriber.confirmation_sent_at = timezone.now()
    subscriber.save(update_fields=["confirmation_sent_at"])
    email.send(fail_silently=False)
```

### Admin Registration
```python
# Source: shop/admin.py pattern
from django.contrib import admin
from .models import Subscriber


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ["email", "is_confirmed", "is_unsubscribed", "created_at"]
    list_filter = ["is_confirmed", "is_unsubscribed"]
    search_fields = ["email"]
    readonly_fields = [
        "confirmation_token",
        "unsubscribe_token",
        "confirmation_sent_at",
        "created_at",
    ]
```

### URL Configuration
```python
# newsletter/urls.py
from django.urls import path
from . import views

app_name = "newsletter"

urlpatterns = [
    path("newsletter/zapisz/", views.subscribe, name="subscribe"),
    path("newsletter/sprawdz-email/", views.check_email, name="check_email"),
    path("newsletter/potwierdz/<str:token>/", views.confirm, name="confirm"),
    path("newsletter/wypisz/<str:token>/", views.unsubscribe, name="unsubscribe"),
]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| django-newsletter package | Custom model for simple subscribe/unsubscribe | N/A | django-newsletter is for full campaign management; overkill for subscribe-only v1 |
| UUID4 tokens | `secrets.token_urlsafe()` | Python 3.6+ | Shorter, URL-safe, cryptographically intended for tokens |
| HTML email templates | Plain text emails | Project decision (Phase 5 D-13) | Simpler, matches existing email pattern |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Django TestCase (unittest-based) |
| Config file | None (Django default test runner) |
| Quick run command | `python3 manage.py test newsletter -v2` |
| Full suite command | `python3 manage.py test -v2` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NEWS-01 | Subscribe form POST creates subscriber, redirects to check-email page | unit | `python3 manage.py test newsletter.tests.test_views::TestSubscribe -v2` | Wave 0 |
| NEWS-01 | Duplicate email (confirmed) silently redirects, no status reveal | unit | `python3 manage.py test newsletter.tests.test_views::TestSubscribeDuplicate -v2` | Wave 0 |
| NEWS-01 | Duplicate email (pending) resends confirmation, redirects | unit | `python3 manage.py test newsletter.tests.test_views::TestSubscribeResend -v2` | Wave 0 |
| NEWS-02 | Confirmation email sent with correct token URL | unit | `python3 manage.py test newsletter.tests.test_emails -v2` | Wave 0 |
| NEWS-02 | Clicking valid confirm token sets is_confirmed=True | unit | `python3 manage.py test newsletter.tests.test_views::TestConfirm -v2` | Wave 0 |
| NEWS-02 | Expired confirm token shows "link expired" page | unit | `python3 manage.py test newsletter.tests.test_views::TestConfirmExpired -v2` | Wave 0 |
| NEWS-03 | Clicking unsubscribe token sets is_unsubscribed=True | unit | `python3 manage.py test newsletter.tests.test_views::TestUnsubscribe -v2` | Wave 0 |
| NEWS-03 | Re-clicking unsubscribe token shows "already unsubscribed" | unit | `python3 manage.py test newsletter.tests.test_views::TestUnsubscribeIdempotent -v2` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python3 manage.py test newsletter -v2`
- **Per wave merge:** `python3 manage.py test -v2`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `newsletter/tests/__init__.py` -- package init
- [ ] `newsletter/tests/test_models.py` -- model creation, token generation, expiry check
- [ ] `newsletter/tests/test_views.py` -- all view tests (subscribe, confirm, unsubscribe flows)
- [ ] `newsletter/tests/test_emails.py` -- confirmation email content and sending

## Open Questions

1. **Re-subscription after unsubscribe**
   - What we know: D-05 handles duplicate confirmed/pending emails. Context does not explicitly address re-subscription after unsubscribe.
   - What's unclear: Should an unsubscribed user be able to re-subscribe by filling the form again?
   - Recommendation: YES -- treat as new subscription flow. Reset `is_unsubscribed=False`, `is_confirmed=False`, generate new confirmation token. This is standard RODO practice (user explicitly opts in again).

2. **Newsletter form on every page vs specific pages**
   - What we know: D-01 says "above the footer" -- base.html includes footer on every page.
   - What's unclear: Should the form appear on checkout, confirmation, or error pages?
   - Recommendation: Include on all pages via base.html. Simple, consistent, matches D-01.

## Sources

### Primary (HIGH confidence)
- Project codebase: `shop/views.py`, `shop/emails.py`, `shop/forms.py`, `shop/admin.py` -- established patterns
- Project codebase: `backend/settings.py` -- email config, installed apps pattern
- Project codebase: `templates/base.html`, `templates/includes/_footer.html` -- template structure
- CONTEXT.md -- all locked decisions D-01 through D-08

### Secondary (MEDIUM confidence)
- Django 5.2 `secrets` module -- standard library, stable API
- Django 5.2 `django.core.mail.EmailMessage` -- stable API, used in project

### Tertiary (LOW confidence)
- None. All research is based on project code and Django stdlib.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all Django stdlib
- Architecture: HIGH -- follows established project patterns (shop app structure)
- Pitfalls: HIGH -- common Django patterns, well-understood edge cases

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (stable -- no external dependencies or fast-moving libraries)
