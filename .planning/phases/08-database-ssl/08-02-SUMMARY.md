---
phase: 08-database-ssl
plan: 02
subsystem: infra
tags: [ssl, https, letsencrypt, security, cron, mydevil, csrf, cookies]

# Dependency graph
requires:
  - phase: 08-database-ssl
    provides: "PostgreSQL database running on MyDevil.net with all migrations applied"
  - phase: 07-server-foundation
    provides: "Production Django app on MyDevil.net with Passenger WSGI and .env config"
provides:
  - "HTTPS-only access with valid Let's Encrypt certificate"
  - "HTTP to HTTPS 301 redirect at Apache level"
  - "Secure cookie flags (SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE)"
  - "CSRF_TRUSTED_ORIGINS configured for production domain"
  - "HSTS header enabled (3600s initial)"
  - "Keep-alive cron job pinging site every 12h"
affects: [09-email, 10-payments-verification]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Server-level sslonly redirect (Apache) with Django SECURE_PROXY_SSL_HEADER for detection", "HSTS starts at 3600s, increase after validation period"]

key-files:
  created: []
  modified: [".env (production, server-side only)"]

key-decisions:
  - "SECURE_SSL_REDIRECT=False -- Apache sslonly handles redirect, avoids redirect loop"
  - "SECURE_HSTS_SECONDS=3600 (1 hour) -- conservative start, increase after validation"
  - "psycopg2-binary replaces psycopg[binary] -- no binary wheel available on MyDevil platform"

patterns-established:
  - "Security env vars activated in production .env after HTTPS confirmed working"
  - "Apache-level SSL redirect preferred over Django-level to avoid double-redirect"

requirements-completed: [SSL-01, SSL-02, SSL-03, SSL-04, SSL-05]

# Metrics
duration: operator-driven
completed: 2026-04-10
---

# Phase 08 Plan 02: Let's Encrypt HTTPS, Security Settings, Keep-alive Cron Summary

**Let's Encrypt certificate on kuchennakomitywa.pl with HTTPS-only access, secure cookie flags, CSRF trusted origins, and 12h keep-alive cron**

## Performance

- **Duration:** Operator-driven (both tasks were human-action checkpoints)
- **Started:** 2026-04-10
- **Completed:** 2026-04-10
- **Tasks:** 2
- **Files modified:** 1 (production .env, server-side)

## Accomplishments
- Let's Encrypt certificate issued and installed on kuchennakomitywa.pl via MyDevil devil commands
- HTTPS-only mode enabled at Apache level -- all HTTP requests return 301 redirect to HTTPS
- Security env vars activated: SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE, SECURE_HSTS_SECONDS, CSRF_TRUSTED_ORIGINS
- Cookie Secure flags verified in browser DevTools
- Keep-alive cron job configured to ping site every 12 hours, preventing MyDevil auto-shutdown

## Task Commits

Both tasks were human-action checkpoints (server-side configuration only, no code commits):

1. **Task 1: Generate Let's Encrypt certificate and enable HTTPS-only on MyDevil** - Operator completed (no code commit -- MyDevil server configuration)
2. **Task 2: Activate security env vars, configure CSRF, set up keep-alive cron** - Operator completed (no code commit -- production .env and crontab changes)

**Bug fixes committed during execution:**
- `1c811c5` fix(settings): auto-create logs/ directory on startup
- `089e4f9` fix(deps): replace psycopg3[binary] with psycopg2-binary (no binary wheel for MyDevil platform)

## Files Created/Modified
- `.env` (production, server-side) - Added security env vars: SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE, SECURE_HSTS_SECONDS, SECURE_HSTS_INCLUDE_SUBDOMAINS, CSRF_TRUSTED_ORIGINS

## Decisions Made
- Set SECURE_SSL_REDIRECT=False because Apache sslonly handles the redirect at server level; Django-level redirect caused redirect loop
- Started HSTS at 3600 seconds (1 hour) rather than 31536000 (1 year) -- HSTS is cached by browsers and cannot be easily undone
- Replaced psycopg[binary] with psycopg2-binary after discovering no binary wheel exists for MyDevil's platform

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Auto-create logs/ directory on startup**
- **Found during:** Task 2 (security settings activation)
- **Issue:** Application failed to start because logs/ directory did not exist
- **Fix:** Added auto-creation of logs/ directory in settings.py
- **Files modified:** backend/settings.py
- **Committed in:** `1c811c5`

**2. [Rule 3 - Blocking] Replace psycopg[binary] with psycopg2-binary**
- **Found during:** Task 2 (application restart after config changes)
- **Issue:** psycopg[binary] (psycopg3) has no pre-built binary wheel for MyDevil's platform, causing pip install failure
- **Fix:** Replaced psycopg[binary] with psycopg2-binary in requirements.txt
- **Files modified:** requirements.txt
- **Committed in:** `089e4f9`

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes were necessary for the application to run. No scope creep.

## Issues Encountered
- psycopg3 binary wheel unavailability on MyDevil required falling back to psycopg2-binary -- this contradicts the earlier Phase 8 decision to use psycopg[binary] but was unavoidable given platform constraints

## User Setup Required

Both tasks were human-action checkpoints. The operator completed all server-side steps:
- Generated Let's Encrypt certificate via `devil ssl www add`
- Enabled HTTPS-only via `devil www options kuchennakomitywa.pl sslonly on`
- Updated production .env with security settings
- Restarted application
- Verified admin login, cookie flags, and CSRF behavior
- Set up crontab with curl ping every 12 hours

## Next Phase Readiness
- HTTPS is fully operational -- ready for Phase 9 (Email) which requires HTTPS for production email links
- All security headers active -- ready for Phase 10 payment webhook verification over HTTPS
- Keep-alive cron prevents the 24h shutdown that would break webhook delivery

## Self-Check: PASSED

- 08-02-SUMMARY.md: FOUND
- Commit 1c811c5 (fix settings logs dir): FOUND
- Commit 089e4f9 (fix deps psycopg2-binary): FOUND
- SSL-01 through SSL-05 marked complete in REQUIREMENTS.md: VERIFIED
- ROADMAP.md phase 8 marked complete: VERIFIED
- STATE.md updated to phase 08 complete: VERIFIED

---
*Phase: 08-database-ssl*
*Completed: 2026-04-10*
