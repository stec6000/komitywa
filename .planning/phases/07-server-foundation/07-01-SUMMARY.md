---
phase: 07-server-foundation
plan: 01
subsystem: infra
tags: [passenger-wsgi, whitenoise, django-environ, production-settings, mydevil]

# Dependency graph
requires:
  - phase: 06-newsletter
    provides: "Complete v1.0 MVP codebase with all Django apps"
provides:
  - "Passenger WSGI entry point (passenger_wsgi.py)"
  - "WhiteNoise static file serving with compressed, content-hashed filenames"
  - "DATABASE_URL support via env.db() (SQLite default, PostgreSQL-ready)"
  - "File-based error logging at WARNING level to logs/django.log"
  - "Pre-HTTPS security headers and env-driven HTTPS security settings"
  - "Production-pinned requirements.txt with whitenoise"
affects: [07-server-foundation, 08-database-ssl, 09-email, 10-payments-verify]

# Tech tracking
tech-stack:
  added: [whitenoise, Pillow]
  patterns: [passenger-wsgi-entry-point, env-driven-database, file-based-logging, env-driven-security-settings]

key-files:
  created: [passenger_wsgi.py, logs/.gitkeep]
  modified: [backend/settings.py, requirements.txt]

key-decisions:
  - "Direct os.environ assignment for DJANGO_SETTINGS_MODULE in passenger_wsgi.py (not setdefault)"
  - "WhiteNoise CompressedManifestStaticFilesStorage for cache-busting static files"
  - "Pre-HTTPS security settings enabled now; HTTPS-dependent settings env-driven with safe defaults"

patterns-established:
  - "Passenger WSGI: project root passenger_wsgi.py with sys.path insert and direct env assignment"
  - "Security: always-on headers vs env-driven HTTPS settings pattern"
  - "Database: env.db() with SQLite fallback for local dev"

requirements-completed: [INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-06]

# Metrics
duration: 3min
completed: 2026-04-10
---

# Phase 7 Plan 01: Server Foundation Summary

**Passenger WSGI entry point, WhiteNoise static serving, DATABASE_URL support, file logging, and production security settings for MyDevil.net deployment**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-10T07:44:17Z
- **Completed:** 2026-04-10T07:47:30Z
- **Tasks:** 3/3 (all complete, Task 3 confirmed by operator)
- **Files modified:** 4

## Accomplishments
- Created passenger_wsgi.py with direct DJANGO_SETTINGS_MODULE assignment for Passenger WSGI on MyDevil.net
- Configured WhiteNoise middleware and CompressedManifestStaticFilesStorage for production static files
- Replaced hardcoded SQLite database with env.db() supporting DATABASE_URL for PostgreSQL migration
- Added file-based LOGGING at WARNING level with django.request logger for HTTP error tracing
- Added pre-HTTPS security headers and env-driven HTTPS security settings
- Updated requirements.txt with pinned django>=5.2,<5.3, whitenoise>=6.12,<7, and Pillow

## Task Commits

Each task was committed atomically:

1. **Task 1: Create passenger_wsgi.py and update requirements.txt** - `85235e4` (feat)
2. **Task 2: Configure settings.py for production** - `73fc18b` (feat)
3. **Task 3: MyDevil server-side setup** - CONFIRMED (human-action, operator completed)

## Files Created/Modified
- `passenger_wsgi.py` - Passenger WSGI entry point for MyDevil.net
- `requirements.txt` - Production dependencies with pinned versions, added whitenoise and Pillow
- `backend/settings.py` - WhiteNoise middleware, DATABASE_URL, LOGGING, security settings
- `logs/.gitkeep` - Ensures logs/ directory exists after git clone

## Decisions Made
- Used direct `os.environ["DJANGO_SETTINGS_MODULE"]` assignment (not setdefault) per D-08 -- Passenger must always use backend.settings
- WhiteNoise at MIDDLEWARE position 2 (after SecurityMiddleware, before CorsMiddleware)
- Pre-HTTPS security headers (SECURE_CONTENT_TYPE_NOSNIFF, X_FRAME_OPTIONS=DENY) always-on; HTTPS-dependent settings (SSL redirect, HSTS, secure cookies) are env-driven with safe defaults (off)
- LOGGING threshold at WARNING (not ERROR) for more visibility during initial launch

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

**Task 3 (checkpoint:human-action)** -- COMPLETED by operator (2026-04-10):
1. Website created in MyDevil panel (Python/Passenger type)
2. Virtualenv created: `~/.virtualenvs/komitywa/`
3. Python interpreter path set in panel to `~/.virtualenvs/komitywa/bin/python`

## Known Stubs

None - all configuration is complete and functional.

## Next Phase Readiness
- passenger_wsgi.py and settings.py are production-ready
- Server-side virtualenv is configured and ready for deploy.sh
- Plan 07-02 (deploy.sh + .env.example) is already complete -- Phase 7 is fully done
- Phase 8 (Database and SSL) can proceed: DATABASE_URL is wired, security env vars are prepared

## Self-Check: PASSED

- All 4 created/modified files verified present on disk
- Both task commit hashes (85235e4, 73fc18b) verified in git log

---
*Phase: 07-server-foundation*
*Completed: 2026-04-10*
