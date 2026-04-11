# GSD Debug Knowledge Base

Resolved debug sessions. Used by `gsd-debugger` to surface known-pattern hypotheses at the start of new investigations.

---

## bootstrap-css-not-loading — Incorrect SRI integrity hash on Bootstrap CDN CSS link
- **Date:** 2026-04-07
- **Error patterns:** unstyled HTML, Bootstrap CSS not loading, SRI integrity hash mismatch, no layout no colors
- **Root cause:** The Bootstrap 5.3.3 CSS link tag in base.html had an incorrect SHA-384 integrity hash. The browser downloads the CSS but the SRI check fails, so it silently refuses to apply the stylesheet.
- **Fix:** Replace the incorrect integrity hash with the correct one (sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH) in templates/base.html
- **Files changed:** templates/base.html
---

## newsletter-email-not-sending — Newsletter emails printed to error.log instead of being sent via SMTP
- **Date:** 2026-04-11
- **Error patterns:** email not sent, email in error.log, console.EmailBackend, Passenger stderr, newsletter confirmation email not delivered, Brevo SMTP
- **Root cause:** Production .env did not set EMAIL_BACKEND to django.core.mail.backends.smtp.EmailBackend. The default in settings.py is console.EmailBackend, which writes email content to stderr. Passenger captures stderr as error.log. Phase 09 Plan 02 (production SMTP configuration) was never executed.
- **Fix:** Set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend and Brevo SMTP credentials (EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_USE_TLS) in production .env, then restart the app.
- **Files changed:** (none — configuration-only fix in production .env)
---
