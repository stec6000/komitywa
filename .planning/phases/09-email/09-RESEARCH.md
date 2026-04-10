# Phase 9: Email - Research

**Researched:** 2026-04-10
**Domain:** Django email configuration, Brevo SMTP, allauth email templates, DNS authentication
**Confidence:** HIGH

## Summary

Phase 9 configures production email delivery via Brevo SMTP and ensures all four email flows work end-to-end: allauth account verification, allauth password reset, shop order confirmation with ebook PDF attachment, and newsletter double opt-in. The Django email infrastructure is already fully env-driven in `backend/settings.py` (lines 204-217) with console backend as the safe default. Polish plaintext allauth templates already exist in `accounts/templates/account/email/` but need quality improvements (missing Polish diacritics, missing footer, `user.get_username` returns empty string for this email-only user model). Shop and newsletter email functions are already implemented and tested.

The primary work is: (1) fix existing allauth templates, (2) set Brevo SMTP env vars on production, (3) configure SPF/DKIM DNS records on MyDevil, (4) verify all four email flows on production.

**Primary recommendation:** This is mostly a configuration and template-fix phase, not a code-architecture phase. The settings infrastructure is done -- focus on template correctness, DNS verification, and production smoke testing.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: Emaile allauth po polsku
- D-02: Stworzyc `templates/account/email/` z plikami `.txt` dla kazdego przeplywu allauth
- D-03: Brak wersji HTML -- tylko plaintext, z polska stopka zawierajaca nazwe firmy
- D-04: Wszystkie transakcyjne emaile -- plaintext, nie HTML
- D-05: Stopka: `-- \nKuchenna Komitywa\nhttps://kuchennakomitywa.pl`
- D-06: Emaile allauth trzymaja sie standardowej struktury allauth (temat + tresc) ale z polskim tekstem
- D-07: Uzytkownik ma juz konto Brevo -- poda SMTP credentials podczas wykonania
- D-08: Adres nadawcy: `noreply@kuchennakomitywa.pl` (juz skonfigurowany w `DEFAULT_FROM_EMAIL`)
- D-09: W Brevo zweryfikowac domene `kuchennakomitywa.pl` przez rekordy SPF i DKIM w DNS MyDevil
- D-10 to D-16: Env vars for SMTP configuration (see CONTEXT.md for full list)

### Claude's Discretion
- Dokladna tresc polskich emaili allauth (standardowe allauth tlumaczenia jako baza)
- Kolejnosc krokow weryfikacji DNS

### Deferred Ideas (OUT OF SCOPE)
None
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EMAIL-01 | Aplikacja wysyla emaile przez Brevo SMTP (nie console backend) | Settings already env-driven; set 6 env vars on production server |
| EMAIL-02 | Domena nadawcy zweryfikowana w Brevo przez SPF/DKIM w DNS | DNS records on MyDevil, verification in Brevo dashboard |
| EMAIL-03 | Email rejestracji + weryfikacji email dziala na produkcji | Allauth templates exist but need fixes (diacritics, footer, username issue) |
| EMAIL-04 | Email resetowania hasla dziala na produkcji | Allauth template exists, same fixes needed |
| EMAIL-05 | Email potwierdzenia zamowienia z zalaczonym eBookiem PDF dziala na produkcji | `shop/emails.py` already implemented with PDF attachment logic |
| EMAIL-06 | Email double opt-in dla newslettera dziala na produkcji | `newsletter/emails.py` already implemented |
</phase_requirements>

## Architecture Patterns

### Current Email Infrastructure

All email settings are already in `backend/settings.py` lines 204-217, fully env-driven:

```python
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Kuchenna Komitywa <noreply@kuchennakomitywa.pl>")
```

No code changes needed for SMTP configuration -- only `.env` on the production server.

### Allauth Template Structure

**Location:** Templates should be at `templates/account/email/` (project-level TEMPLATES DIRS) -- currently they are at `accounts/templates/account/email/` which also works via APP_DIRS.

CONTEXT.md D-02 says `templates/account/email/` but the existing templates are in `accounts/templates/account/email/`. Both paths work -- `APP_DIRS: True` picks up app-level templates, and `DIRS: [BASE_DIR / "templates"]` picks up project-level. Keep the existing location (`accounts/templates/account/email/`) since templates are already there.

**Template naming convention (allauth):**
- `{template_name}_subject.txt` -- single line, no newline
- `{template_name}_message.txt` -- email body

**Required allauth email templates for this project:**
1. `email_confirmation_subject.txt` + `email_confirmation_message.txt` -- EXISTS, needs fixes
2. `password_reset_key_subject.txt` + `password_reset_key_message.txt` -- EXISTS, needs fixes

### Email Senders Already Implemented

| Flow | File | Function | Status |
|------|------|----------|--------|
| Account verification | allauth built-in | Uses templates | Templates need fixes |
| Password reset | allauth built-in | Uses templates | Templates need fixes |
| Order confirmation | `shop/emails.py` | `send_order_confirmation()` | Complete, tested |
| Ebook delivery | `shop/emails.py` | `send_ebook_delivery()` | Complete, tested (PDF attach) |
| Newsletter double opt-in | `newsletter/emails.py` | `send_confirmation_email()` | Complete, tested |

### Pattern: Consistent Polish Footer

Per D-05, all emails should end with:
```
-- 
Kuchenna Komitywa
https://kuchennakomitywa.pl
```

The allauth templates currently lack this footer. Shop emails (`shop/emails.py`) end with "Kuchenna Komitywa" but not the full footer. Newsletter email has "Pozdrawiamy,\nKuchenna Komitywa" but not the standardized footer. The planner should decide whether to also update shop/newsletter email footers for consistency, or leave them as-is since D-05 mentions "stopka" generically.

## Common Pitfalls

### Pitfall 1: `user.get_username` Returns Empty String
**What goes wrong:** Current allauth templates use `{{ user.get_username }}` which returns `""` because this project has `username = None` on the User model (email-only auth).
**Why it happens:** Custom User model removed the username field entirely.
**How to avoid:** Use `{{ user.email }}` or just "Witaj!" without username in allauth email templates.
**Warning signs:** Emails start with "Witaj ," (with trailing comma and space before nothing).

### Pitfall 2: Missing Polish Diacritics in Templates
**What goes wrong:** Current templates use ASCII-only Polish ("Prosze" instead of "Prosze", "Dziekujemy" instead of "Dziekujemy"). Actually: "Prosze" vs "Prosze" -- the templates already lack diacritics. Let me be precise: the existing templates have words like "potwierdzic" (missing c-acute), "klikajac" (missing a-ogonek), "wiadomosc" (missing s-acute).
**Why it happens:** Templates were likely written without proper encoding or as ASCII placeholders.
**How to avoid:** Use proper UTF-8 Polish characters: "Prosze", "klikajac" -> "klikajac", "potwierdzic" -> "potwierdzic", "wiadomosc" -> "wiadomosc".

### Pitfall 3: Brevo SMTP Attachment Size Limits
**What goes wrong:** Brevo has a 20MB attachment limit per email. Large ebook PDFs could fail silently or error.
**Why it happens:** Ebook PDFs attached via `email.attach_file()` in `shop/emails.py`.
**How to avoid:** Ensure ebook PDFs are under 20MB. The existing code already has error handling (`try/except` with logging) for attachment failures.
**Warning signs:** `Failed to attach ebook` or `Failed to send ebook email` in `logs/django.log`.

### Pitfall 4: SPF/DKIM DNS Propagation Delay
**What goes wrong:** DNS record changes can take up to 48 hours to propagate. Brevo domain verification may not work immediately.
**Why it happens:** DNS TTL and propagation across nameservers.
**How to avoid:** Set up DNS records as the FIRST step, then work on templates while waiting. Use Brevo dashboard to check verification status.
**Warning signs:** Brevo dashboard shows "Pending" for domain verification.

### Pitfall 5: Brevo SMTP Rate Limiting
**What goes wrong:** Brevo free plan limits to 300 emails/day. Testing multiple flows could eat into the limit.
**Why it happens:** Brevo enforces daily sending limits on free/starter plans.
**How to avoid:** Test each flow once or twice, not repeatedly. Check Brevo dashboard for remaining quota.

### Pitfall 6: `ACCOUNT_EMAIL_VERIFICATION` Not Explicitly Set
**What goes wrong:** The setting `ACCOUNT_EMAIL_VERIFICATION` is not set in `backend/settings.py`. Allauth defaults to `"optional"` which means users CAN verify but are not required to. If the project expects mandatory verification, this should be set to `"mandatory"`.
**Why it happens:** Setting was never added during initial allauth configuration.
**How to avoid:** Decide if email verification should be mandatory or optional. For a shop where emails deliver ebooks, mandatory verification is recommended. Add `ACCOUNT_EMAIL_VERIFICATION = "mandatory"` to settings if needed.

### Pitfall 7: `current_site.name` Shows "example.com"
**What goes wrong:** Allauth email templates use `{{ current_site.name }}` which defaults to "example.com" in the Django Sites framework unless the Site object is updated.
**Why it happens:** `SITE_ID = 1` is set but the corresponding `django.contrib.sites` Site object may have the default "example.com" values.
**How to avoid:** Run `python manage.py shell` on production and update the Site object: `Site.objects.filter(id=1).update(domain="kuchennakomitywa.pl", name="Kuchenna Komitywa")`. Or add a data migration.
**Warning signs:** Email subjects say "Potwierdzenie adresu email w example.com".

## Code Examples

### Allauth Email Template with Correct Polish Text (email_confirmation_message.txt)

```
Czesc!

Prosimy o potwierdzenie adresu email klikajac w ponizszy link:
{{ activate_url }}

Jesli to nie Ty, zignoruj te wiadomosc.

-- 
Kuchenna Komitywa
https://kuchennakomitywa.pl
```

Note: Do NOT extend `base_message.txt` -- write standalone templates to avoid the English "Hello from..." and "Thank you for using..." strings from allauth's base template.

### Allauth Email Template (email_confirmation_subject.txt)

```
Potwierdzenie adresu email -- Kuchenna Komitywa
```

Note: Subject templates must be a single line, no trailing newline. Do NOT use `{{ current_site.name }}` in subject unless the Site object is correctly configured.

### Production .env SMTP Configuration

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=<Brevo SMTP login>
EMAIL_HOST_PASSWORD=<Brevo SMTP key>
```

### Django Management Command to Test Email

```python
# Quick smoke test from production shell
python manage.py shell -c "
from django.core.mail import send_mail
from django.conf import settings
send_mail('Test email', 'Test body', settings.DEFAULT_FROM_EMAIL, ['owner@example.com'])
"
```

### Update Django Sites Object

```python
# Run on production after deploy
python manage.py shell -c "
from django.contrib.sites.models import Site
Site.objects.filter(id=1).update(domain='kuchennakomitywa.pl', name='Kuchenna Komitywa')
"
```

Or as a data migration in `accounts/migrations/`:

```python
from django.db import migrations

def update_site(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    Site.objects.filter(id=1).update(
        domain="kuchennakomitywa.pl",
        name="Kuchenna Komitywa",
    )

class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "XXXX_previous"),
        ("sites", "0002_alter_domain_unique"),
    ]
    operations = [
        migrations.RunPython(update_site, migrations.RunPython.noop),
    ]
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Email verification flow | Custom verification views/tokens | allauth built-in email verification | Already configured, handles tokens, rate limiting, expiry |
| Password reset flow | Custom reset views/tokens | allauth built-in password reset | Handles token generation, expiry, security |
| SMTP connection management | Custom SMTP wrapper | Django's built-in `EmailMessage` / `send_mail` | Already handles TLS, connection pooling, error handling |
| Email templating for allauth | Custom email sending function | allauth template override system | Just override `.txt` files in the right directory |

## Standard Stack

No new libraries needed. Everything is already installed:

| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| django-allauth | 65.15.1 | Email verification, password reset | Installed |
| Django (email) | 5.2.x | `django.core.mail` SMTP backend | Built-in |
| django-environ | installed | Env-driven email settings | Already configured |

No `pip install` needed for this phase.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Django TestCase (unittest) |
| Config file | `backend/settings.py` (test runner built into Django) |
| Quick run command | `python manage.py test --parallel` |
| Full suite command | `python manage.py test --parallel` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EMAIL-01 | SMTP backend sends email | unit | `python manage.py test accounts.tests::EmailSMTPConfigTest -x` | No - Wave 0 |
| EMAIL-02 | SPF/DKIM DNS verified in Brevo | manual-only | Check Brevo dashboard | N/A |
| EMAIL-03 | Registration verification email arrives | smoke (prod) | Manual: register on prod, check inbox | N/A |
| EMAIL-04 | Password reset email arrives | smoke (prod) | Manual: reset password on prod, check inbox | N/A |
| EMAIL-05 | Order confirmation + ebook email | unit | `python manage.py test shop.tests.test_emails -x` | Yes |
| EMAIL-06 | Newsletter double opt-in email | unit | `python manage.py test newsletter.tests.test_emails -x` | Yes |

### Sampling Rate
- **Per task commit:** `python manage.py test --parallel`
- **Per wave merge:** `python manage.py test --parallel`
- **Phase gate:** Full suite green + manual production smoke tests for EMAIL-03, EMAIL-04, EMAIL-05, EMAIL-06

### Wave 0 Gaps
- [ ] Allauth email template rendering test -- verify templates render without errors and contain expected Polish text
- [ ] Site object configuration test -- verify Site(id=1) has correct domain/name

Note: EMAIL-02 through EMAIL-06 ultimately require production smoke testing (real emails through Brevo). Unit tests verify template rendering and function calls but cannot verify actual delivery.

## Open Questions

1. **ACCOUNT_EMAIL_VERIFICATION setting**
   - What we know: Not set in settings.py. Allauth defaults to `"optional"`.
   - What's unclear: Should email verification be mandatory for this shop? Mandatory means users must verify before they can log in.
   - Recommendation: Set to `"mandatory"` since ebook delivery depends on valid email addresses. But this is Claude's discretion per CONTEXT.md.

2. **Footer consistency across all email types**
   - What we know: D-05 specifies the footer format. Allauth templates need it. Shop/newsletter emails have informal footers.
   - What's unclear: Should shop and newsletter email footers also be updated to match exactly?
   - Recommendation: Update all email footers to the D-05 format for consistency.

3. **django.contrib.sites in INSTALLED_APPS**
   - What we know: `SITE_ID = 1` is set. Allauth requires `django.contrib.sites`.
   - What's unclear: Whether `django.contrib.sites` is in INSTALLED_APPS (not visible in the current apps list).
   - Recommendation: Verify during planning. If missing, allauth would have failed already, so it's likely present via allauth's dependencies.

## Sources

### Primary (HIGH confidence)
- `backend/settings.py` -- direct code inspection of email configuration (lines 204-217)
- `accounts/templates/account/email/` -- direct inspection of existing allauth templates
- `shop/emails.py` -- direct inspection of order confirmation and ebook delivery code
- `newsletter/emails.py` -- direct inspection of newsletter confirmation email code
- allauth 65.15.1 installed templates at `.venv/lib/python3.10/site-packages/allauth/templates/account/email/`

### Secondary (MEDIUM confidence)
- Brevo SMTP configuration (smtp-relay.brevo.com:587 with TLS) -- standard Brevo documentation, verified by CONTEXT.md decisions
- Brevo 20MB attachment limit -- general knowledge of Brevo platform limits

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new libraries needed, all already installed and configured
- Architecture: HIGH - all email code exists, only template fixes and env vars needed
- Pitfalls: HIGH - identified from direct code inspection (username issue, diacritics, Site object)

**Research date:** 2026-04-10
**Valid until:** 2026-05-10 (stable domain, no fast-moving dependencies)
