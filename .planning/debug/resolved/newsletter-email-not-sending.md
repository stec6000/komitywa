---
status: resolved
trigger: "Newsletter confirmation emails are not being delivered — email content is showing up in the Passenger error.log instead of being sent via Brevo SMTP."
created: 2026-04-11T00:00:00Z
updated: 2026-04-11T00:00:00Z
---

## Current Focus

hypothesis: Production .env file does not set EMAIL_BACKEND to smtp — Django falls back to console.EmailBackend default, which writes emails to stderr (captured by Passenger as error.log)
test: Verified settings.py reads EMAIL_BACKEND from env with console backend as default
expecting: If .env on production lacks EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend, all emails go to console/stderr
next_action: User must set EMAIL_BACKEND and other Brevo SMTP vars in production .env and restart app

## Symptoms

expected: After signing up for newsletter, user receives confirmation email via Brevo SMTP
actual: Email content appears in ~/domains/kuchennakomitywa.pl/logs/error.log — user receives nothing
errors: The error.log shows the raw email text (subject, body with confirmation link) — this is typical Django console/filebased email backend behavior printing to stderr/stdout which Passenger captures as error.log
reproduction: Sign up for newsletter on https://kuchennakomitywa.pl/newsletter/
started: Production deployment is new (v1.1 milestone). Phase 09 plan 01 was executed but plan 02 (production SMTP configuration) has no SUMMARY yet.

## Eliminated

(none — root cause found on first hypothesis)

## Evidence

- timestamp: 2026-04-11T00:00:00Z
  checked: backend/settings.py lines 206-209 — EMAIL_BACKEND setting
  found: EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend") — if the production .env does not explicitly set EMAIL_BACKEND, Django uses the console backend which writes email content to stdout/stderr
  implication: This is the direct mechanism. Console backend writes to stderr, Passenger captures stderr as error.log. This matches the symptom exactly.

- timestamp: 2026-04-11T00:00:00Z
  checked: .env.example — the template for production .env
  found: The active line is EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend. The SMTP config lines are all commented out with instructions "Na produkcji ustaw:..."
  implication: If the production .env was created by copying .env.example without uncommenting the SMTP lines, it would keep the console backend.

- timestamp: 2026-04-11T00:00:00Z
  checked: Phase 09 plans and summary
  found: Plan 01 (executed, has SUMMARY) prepared templates, footers, settings, and .env.example docs. Plan 02 (production SMTP config + DNS) has NO SUMMARY — it was never executed. Plan 02 Task 1 is a human-action checkpoint requiring the user to set 6 Brevo SMTP env vars in production .env.
  implication: The production configuration step was planned but never completed. The code is correct; the deployment configuration is missing.

- timestamp: 2026-04-11T00:00:00Z
  checked: newsletter/emails.py — how emails are sent
  found: Uses standard Django EmailMessage.send(fail_silently=False) with settings.DEFAULT_FROM_EMAIL. No custom backend override. Relies entirely on the EMAIL_BACKEND setting.
  implication: The email sending code is correct. It will use whatever backend settings.py provides.

## Resolution

root_cause: Production .env file does not have EMAIL_BACKEND set to django.core.mail.backends.smtp.EmailBackend (and likely missing EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD for Brevo SMTP). The default in settings.py is console.EmailBackend, which writes email content to stderr. Passenger captures stderr as error.log. Phase 09 Plan 02 (production SMTP configuration) was never executed.
fix: Set the following 6 environment variables in the production .env file at ~/domains/kuchennakomitywa.pl/public_python/.env (or wherever the production .env lives), then restart the app.
verification: User confirmed fixed — newsletter confirmation email arrived after setting EMAIL_BACKEND and Brevo SMTP variables in production .env and restarting the app.
files_changed: []
