---
phase: 09-email
plan: 01
subsystem: email
tags: [email, allauth, brevo, polish, templates]
dependency_graph:
  requires: [08-database-ssl]
  provides: [production-email-templates, site-object-migration, brevo-smtp-config]
  affects: [accounts, shop, newsletter, backend-settings]
tech_stack:
  added: []
  patterns: [D-05-footer, unicode-polish-diacritics, data-migration-for-site]
key_files:
  created:
    - accounts/migrations/0002_update_site_object.py
  modified:
    - accounts/templates/account/email/email_confirmation_subject.txt
    - accounts/templates/account/email/email_confirmation_message.txt
    - accounts/templates/account/email/password_reset_key_subject.txt
    - accounts/templates/account/email/password_reset_key_message.txt
    - shop/emails.py
    - newsletter/emails.py
    - backend/settings.py
    - .env.example
decisions:
  - "Hardcoded brand name in email subjects instead of current_site.name for reliability"
  - "ACCOUNT_EMAIL_VERIFICATION set to mandatory (ebook delivery depends on valid email)"
  - "Unicode escape sequences used for Polish diacritics in Python files (functionally equivalent to literal UTF-8)"
metrics:
  duration: 89s
  completed: "2026-04-10"
---

# Phase 09 Plan 01: Email Templates and Configuration Summary

Fixed all email templates for production-quality Polish emails with proper diacritics, standardized D-05 footer, Site object migration, and Brevo SMTP documentation.

## One-liner

Polish email templates with diacritics, D-05 footer, Site object data migration, and mandatory email verification for production Brevo SMTP.

## What Was Done

### Task 1: Fix allauth email templates and add Site object migration (2273aaa)

- Rewrote all four allauth email templates (confirmation subject/body, password reset subject/body)
- Removed all `{{ user.get_username }}` references (email-only model has no username)
- Removed all `{{ current_site.name }}` from subjects, hardcoded "Kuchenna Komitywa"
- Added proper Polish diacritics throughout all templates
- Added standardized D-05 footer (`-- \nKuchenna Komitywa\nhttps://kuchennakomitywa.pl`)
- Created data migration `0002_update_site_object.py` setting Site(id=1) to kuchennakomitywa.pl

### Task 2: Update shop/newsletter email footers and settings (ed8b180)

- Added D-05 standardized footer to `send_order_confirmation()` in shop/emails.py
- Added D-05 standardized footer to `send_ebook_delivery()` in shop/emails.py
- Fixed all missing Polish diacritics in newsletter confirmation email
- Fixed newsletter email subject to use proper diacritics and em-dash
- Added `ACCOUNT_EMAIL_VERIFICATION = "mandatory"` to settings.py
- Updated .env.example with commented Brevo SMTP configuration examples

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None - all templates and code produce complete, production-ready output.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 2273aaa | Fix allauth email templates and add Site object migration |
| 2 | ed8b180 | Update shop/newsletter email footers and email settings |
