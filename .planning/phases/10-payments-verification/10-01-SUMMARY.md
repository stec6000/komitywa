---
phase: 10-payments-verification
plan: "01"
subsystem: infra
tags: [django, settings, przelewy24, p24, deploy-check, hsts, mydevil]

# Dependency graph
requires:
  - phase: 08-database-ssl
    provides: HTTPS live, Apache reverse proxy, HSTS configured, production .env established
  - phase: 09-email
    provides: Brevo SMTP, production deployment workflow verified
provides:
  - SILENCED_SYSTEM_CHECKS silences W008 (Apache handles HTTP->HTTPS, not Django)
  - Deprecated allauth settings removed (ACCOUNT_USERNAME_REQUIRED, ACCOUNT_EMAIL_REQUIRED)
  - SECURE_HSTS_PRELOAD=True added to production .env
  - P24 sandbox credentials set in production .env
  - P24 sandbox panel IP set to % (MyDevil shared IP not fixed)
  - check --deploy passes with 0 warnings on production
affects: [10-payments-verification/10-02, payments, p24-webhook-flow]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Silence W008 via SILENCED_SYSTEM_CHECKS when reverse proxy handles HTTP->HTTPS"
    - "P24 sandbox panel: set IP to % for shared-hosting outbound IPs"
    - "SECURE_HSTS_PRELOAD=True required alongside SECURE_HSTS_INCLUDE_SUBDOMAINS for preload list eligibility"

key-files:
  created: []
  modified:
    - backend/settings.py
    - production .env (SECURE_HSTS_PRELOAD, P24_* vars)

key-decisions:
  - "SILENCED_SYSTEM_CHECKS = [\"security.W008\"] — Apache handles redirect; setting SECURE_SSL_REDIRECT=True would cause double-redirect loop on MyDevil"
  - "ACCOUNT_USERNAME_REQUIRED and ACCOUNT_EMAIL_REQUIRED removed — superseded by ACCOUNT_SIGNUP_FIELDS in allauth 0.61+"
  - "SECURE_HSTS_PRELOAD=True added to production .env after W021 surfaced during check --deploy"
  - "P24 sandbox panel IP set to % — MyDevil shared hosting does not have a fixed outbound IP"

patterns-established:
  - "Deploy check gate: run check --deploy on production before starting webhook integration work"

requirements-completed: [P24-01, VER-02]

# Metrics
duration: ~90min
completed: 2026-04-11
---

# Phase 10 Plan 01: Settings Patch & Deploy Check Summary

**settings.py patched (W008 silenced, deprecated allauth lines removed), SECURE_HSTS_PRELOAD=True + P24 sandbox credentials added to production .env — check --deploy passes with 0 warnings**

## Performance

- **Duration:** ~90 min
- **Started:** 2026-04-11
- **Completed:** 2026-04-11
- **Tasks:** 5
- **Files modified:** 2 (backend/settings.py, production .env)

## Accomplishments

- `backend/settings.py` patched with two edits: `SILENCED_SYSTEM_CHECKS = ["security.W008"]` added after `CSRF_TRUSTED_ORIGINS`, and the two deprecated allauth lines (`ACCOUNT_USERNAME_REQUIRED`, `ACCOUNT_EMAIL_REQUIRED`) removed
- `SECURE_HSTS_PRELOAD=True` added to production `.env` after W021 surfaced during `check --deploy` on production
- P24 sandbox credentials (`P24_MERCHANT_ID`, `P24_POS_ID`, `P24_CRC_KEY`, `P24_API_KEY`, `P24_SANDBOX=True`) set in production `.env`
- P24 sandbox panel IP field set to `%` to allow API calls from MyDevil shared hosting (outbound IP is not fixed)
- `python3 manage.py check --deploy` on production: **0 warnings** (1 silenced — W008, expected)

## Task Commits

Each task was committed atomically:

1. **Task 1: Patch settings.py** - `7c257e6` (fix)
2. **Task 2: Local tests** - no separate commit (verified clean against Task 1 commit)
3. **Task 3: Deploy to production** - `7c257e6` deployed via push + deploy.sh
4. **Task 4: Configure P24 sandbox credentials + set IP to % in P24 panel** - human action (production .env, P24 dashboard)
5. **Task 5: Run check --deploy on production** - human verify (0 warnings confirmed)

**Plan metadata:** (this commit)

## Files Created/Modified

- `backend/settings.py` — Added `SILENCED_SYSTEM_CHECKS = ["security.W008"]` after `CSRF_TRUSTED_ORIGINS`; removed `ACCOUNT_USERNAME_REQUIRED = False` and `ACCOUNT_EMAIL_REQUIRED = True`
- `production .env` (on MyDevil server) — Added `SECURE_HSTS_PRELOAD=True`, `P24_MERCHANT_ID`, `P24_POS_ID`, `P24_CRC_KEY`, `P24_API_KEY`, `P24_SANDBOX=True`

## Decisions Made

- **W008 silenced via SILENCED_SYSTEM_CHECKS:** `SECURE_SSL_REDIRECT=False` is intentional — Apache on MyDevil handles HTTP→HTTPS redirect. Enabling Django's redirect would cause a double-redirect loop. Django docs explicitly recommend silencing W008 when a reverse proxy handles the redirect.
- **Deprecated allauth lines removed:** `ACCOUNT_USERNAME_REQUIRED` and `ACCOUNT_EMAIL_REQUIRED` are superseded by `ACCOUNT_SIGNUP_FIELDS` (already present) since allauth 0.61+. Keeping them produced deprecation warnings in `check --deploy`.
- **SECURE_HSTS_PRELOAD=True:** W021 surfaced during production `check --deploy` — this setting is required alongside `SECURE_HSTS_INCLUDE_SUBDOMAINS` to be eligible for browser HSTS preload lists. Added to production `.env` (not hardcoded in settings.py, consistent with existing HTTPS-dependent settings pattern).
- **P24 panel IP set to %:** MyDevil shared hosting does not provide a fixed outbound IP address. The `%` wildcard allows API calls from any IP, which is required for the server-side P24 API calls in Plan 02.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] SECURE_HSTS_PRELOAD=True added to production .env**
- **Found during:** Task 5 (check --deploy on production)
- **Issue:** W021 warning surfaced: `SECURE_HSTS_PRELOAD` not set. The plan covered W008 (the known warning) but W021 appeared because `SECURE_HSTS_INCLUDE_SUBDOMAINS` was already True, making HSTS preload eligibility incomplete without the preload flag.
- **Fix:** Added `SECURE_HSTS_PRELOAD=True` to the production `.env` file. Not hardcoded in settings.py — consistent with the project pattern where HTTPS-dependent security settings are env-driven.
- **Files modified:** production `.env` (on MyDevil server)
- **Verification:** Re-ran `check --deploy` — W021 gone, 0 warnings total.
- **Committed in:** production .env edit (not a repo commit — .env is gitignored)

---

**Total deviations:** 1 auto-fixed (missing critical security setting)
**Impact on plan:** Fix was necessary to fully satisfy the plan's success criterion of 0 warnings. No scope creep — HSTS preload is part of the same security hardening goal.

## Issues Encountered

- W021 (SECURE_HSTS_PRELOAD) was not anticipated in the plan but appeared during the production `check --deploy` run. Resolved immediately by adding the env var. The plan's stated goal (0 warnings) was achieved.

## User Setup Required

None for ongoing work — all human actions in this plan (Tasks 4 and 5) were completed.

P24 sandbox credentials are now live in production. Plan 02 can proceed to webhook integration testing.

## Next Phase Readiness

- Production passes `check --deploy` with 0 warnings — baseline security posture confirmed
- P24 sandbox credentials are active in production `.env`
- P24 sandbox panel IP is set to `%` — server-side API calls will succeed
- Ready for Plan 02: end-to-end P24 sandbox webhook flow testing

---
*Phase: 10-payments-verification*
*Completed: 2026-04-11*
