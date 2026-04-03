---
phase: 06-newsletter
plan: 01
subsystem: newsletter
tags: [django, email, forms, double-opt-in, gdpr]

requires:
  - phase: 01-foundation
    provides: "Django project structure, base template, email settings"
  - phase: 02-landing
    provides: "Base template with navbar and footer, privacy policy page"
provides:
  - "Subscriber model with dual-token confirmation and unsubscribe"
  - "Newsletter signup form with RODO consent"
  - "Confirmation email sending with 24h expiry"
  - "Subscribe, confirm, unsubscribe views"
  - "Admin interface for subscriber management"
  - "Global newsletter signup section in base template"
affects: [06-newsletter]

tech-stack:
  added: []
  patterns: [double-opt-in email confirmation, token-based unsubscribe, POST-redirect-GET newsletter flow]

key-files:
  created:
    - newsletter/models.py
    - newsletter/views.py
    - newsletter/emails.py
    - newsletter/forms.py
    - newsletter/admin.py
    - newsletter/urls.py
    - newsletter/tests/test_models.py
    - newsletter/tests/test_views.py
    - newsletter/tests/test_emails.py
    - templates/includes/_newsletter_signup.html
    - templates/newsletter/check_email.html
    - templates/newsletter/confirmed.html
    - templates/newsletter/link_expired.html
    - templates/newsletter/unsubscribed.html
  modified:
    - backend/settings.py
    - backend/urls.py
    - templates/base.html
    - static/css/main.css

key-decisions:
  - "Double opt-in with 24h token expiry for RODO compliance"
  - "Unsubscribed users can re-subscribe by resetting confirmation state"
  - "IntegrityError catch for race condition on duplicate email submissions"

patterns-established:
  - "Token-based email actions: confirmation_token and unsubscribe_token as separate URL-safe tokens"
  - "Newsletter signup section as global include between main content and footer"

requirements-completed: [NEWS-01, NEWS-02, NEWS-03]

duration: 3min
completed: 2026-04-03
---

# Phase 6 Plan 1: Newsletter App Scaffold Summary

**Double opt-in newsletter with Subscriber model, confirmation emails, token-based confirm/unsubscribe views, and global signup form on every page**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-03T20:32:30Z
- **Completed:** 2026-04-03T20:35:41Z
- **Tasks:** 2
- **Files modified:** 23

## Accomplishments
- Subscriber model with dual tokens (confirmation + unsubscribe), confirmation expiry, and unsubscribe flag
- Full view logic: subscribe (POST-redirect-GET with duplicate/resend/resubscribe handling), confirm, unsubscribe
- Confirmation email with 24h validity, warm Polish tone, and unsubscribe link
- Newsletter signup section visible on every page between content and footer
- 23 newsletter-specific tests, 147 total tests passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Newsletter app scaffold** - `8a46d8a` (feat)
2. **Task 2: Newsletter signup section template and base.html integration** - `7fc3290` (feat)

## Files Created/Modified
- `newsletter/models.py` - Subscriber model with dual tokens and confirmation expiry
- `newsletter/views.py` - Subscribe, check_email, confirm, unsubscribe views
- `newsletter/emails.py` - Confirmation email sending with token URLs
- `newsletter/forms.py` - Newsletter signup form with RODO consent
- `newsletter/admin.py` - Subscriber admin with filtering and search
- `newsletter/urls.py` - Newsletter URL patterns (zapisz, sprawdz-email, potwierdz, wypisz)
- `newsletter/tests/test_models.py` - 7 tests for Subscriber model
- `newsletter/tests/test_views.py` - 11 tests for all view behaviors
- `newsletter/tests/test_emails.py` - 5 tests for confirmation email
- `templates/includes/_newsletter_signup.html` - Global signup section
- `templates/newsletter/*.html` - check_email, confirmed, link_expired, unsubscribed pages
- `backend/settings.py` - Added "newsletter" to INSTALLED_APPS
- `backend/urls.py` - Added newsletter URL include before core catch-all
- `templates/base.html` - Included newsletter signup between main and footer
- `static/css/main.css` - Newsletter section styles with brand variables

## Decisions Made
- Double opt-in with 24h token expiry for RODO compliance
- Unsubscribed users can re-subscribe by resetting confirmation state and sending new confirmation
- IntegrityError catch for race condition on duplicate email submissions

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created .env file from .env.example for local development**
- **Found during:** Task 1 (migration creation)
- **Issue:** Worktree did not have .env file, Django settings require SECRET_KEY
- **Fix:** Copied .env.example to .env with valid P24 defaults
- **Files modified:** .env (gitignored)
- **Verification:** manage.py commands run successfully

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minimal -- .env is gitignored, needed for local development only.

## Issues Encountered
None beyond the .env setup.

## Known Stubs
None -- all views render real templates with full logic.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Newsletter app fully functional, ready for Plan 02 (page templates and polish)
- All URL patterns resolvable, all views implemented with full logic

---
*Phase: 06-newsletter*
*Completed: 2026-04-03*
