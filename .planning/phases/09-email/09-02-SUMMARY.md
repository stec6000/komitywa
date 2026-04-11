---
phase: 09-email
plan: 02
subsystem: email
tags: [email, brevo, smtp, spf, dkim, dns, production]
dependency_graph:
  requires: [09-01]
  provides: [production-smtp-delivery, sender-domain-auth]
  affects: [newsletter, shop, accounts]
tech_stack:
  added: []
  patterns: [brevo-smtp-relay, spf-dkim-dns]
key_files:
  created: []
  modified:
    - .env (production — not in repo)
decisions:
  - "DNS records (SPF/DKIM) added in OVHcloud (domain registrar), not MyDevil (hosting only)"
  - "Registration/password-reset email flows deferred — no HTML auth views on site (planned Phase 999.1)"
  - "Order confirmation email deferred to Phase 10 (P24 sandbox verification)"
metrics:
  duration: n/a (human configuration task)
  completed: "2026-04-11"
---

# Phase 09 Plan 02: Brevo SMTP Production Configuration Summary

Brevo SMTP configured on production. Newsletter double opt-in verified end-to-end. SPF/DKIM DNS records added at domain registrar (OVHcloud).

## One-liner

Production email delivery through Brevo SMTP working — newsletter confirmed, SPF/DKIM DNS configured, remaining flows deferred pending HTML auth views.

## What Was Done

### Task 1: Configure Brevo SMTP and DNS records

- Set `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` in production `.env`
- Configured `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` with Brevo SMTP credentials
- Restarted app via `touch tmp/restart.txt`
- Verified test email from Django shell arrives in inbox
- Added SPF and DKIM TXT records in OVHcloud (domain registrar for kuchennakomitywa.pl)
- Domain verified in Brevo Dashboard

### Task 2: Smoke test email flows

| Flow | Status | Notes |
|------|--------|-------|
| Newsletter double opt-in | ✓ Verified | Email arrives, confirmation link works, subscriber in Django admin |
| Registration verification | Deferred | No HTML auth views on site — Phase 999.1 |
| Password reset | Deferred | No HTML auth views on site — Phase 999.1 |
| Order confirmation | Deferred | Phase 10 (P24 sandbox) |

## Root Cause Fixed (debug session)

Newsletter emails were appearing in `error.log` instead of being delivered because `EMAIL_BACKEND` was not set in production `.env`, causing the default `console.EmailBackend` to write to stderr (captured by Passenger as error.log).

## Deviations from Plan

- Registration and password reset email flows not tested — no HTML login/registration pages exist on the site. This was discovered during testing and added to backlog as Phase 999.1 (Panel klienta z historią zamówień).
- OVHcloud used for DNS records instead of MyDevil — domain is registered at OVHcloud; MyDevil is hosting only.

## Known Stubs

- Registration/password-reset emails: templates are correct (Phase 01), but flows untestable until HTML auth views are built (Phase 999.1)
- Order confirmation email: deferred to Phase 10

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| debug | 6b499a0 | debug: resolve newsletter-email-not-sending |
| backlog | ed42231 | docs: add backlog item 999.1 — panel klienta z historią zamówień |
