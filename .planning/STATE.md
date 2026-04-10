---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Wdrożenie Produkcyjne
status: in_progress
stopped_at: "07-01 Tasks 1-2 complete; Task 3 checkpoint:human-action pending (MyDevil virtualenv setup)"
last_updated: "2026-04-10T07:47:30Z"
last_activity: 2026-04-10
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 2
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-10)

**Core value:** Klienci mogą przeglądać przepisy, kupować ebooki i zamawiać gotowe wegańskie produkty z odbiorem osobistym — w jednym miejscu.
**Current focus:** Phase 7 — Server Foundation (Passenger WSGI, virtualenv, production settings on MyDevil.net)

## Current Position

Phase: 7 of 10 (Server Foundation)
Plan: 07-01 (Task 3 checkpoint pending), 07-02 (complete)
Status: In progress — waiting on human-action checkpoint
Last activity: 2026-04-10 — Tasks 1-2 complete (passenger_wsgi.py, settings.py, requirements.txt, deploy.sh)

Progress: [░░░░░░░░░░] 0%

## Milestone Status

**v1.1 Production Deployment** — In Progress

- Phase 7: Server Foundation — Plan 01 tasks 1-2 complete, Task 3 checkpoint pending
- Phase 8: Database & SSL — Not started
- Phase 9: Email — Not started
- Phase 10: Payments & Verify — Not started

Previous:
- v1.0 MVP shipped — 2026-04-04 (archive: `.planning/milestones/v1.0-ROADMAP.md`)

## Current Phase

**Phase:** 07-server-foundation
**Current Plan:** 01 of 2
**Status:** Task 3 checkpoint:human-action (MyDevil virtualenv setup)

🔄 **v1.1 Wdrożenie Produkcyjne — in progress**
- 4 phases (7-10), 24 requirements
- Target: MyDevil.net, PostgreSQL, Brevo SMTP, HTTPS, P24 sandbox on prod

## Accumulated Context

### Decisions

- Direct os.environ assignment for DJANGO_SETTINGS_MODULE in passenger_wsgi.py (not setdefault)
- WhiteNoise CompressedManifestStaticFilesStorage for cache-busting static files
- Pre-HTTPS security settings always-on; HTTPS-dependent settings env-driven with safe defaults
- LOGGING at WARNING level for initial launch visibility

v1.1 key decisions:
- MyDevil.net as hosting (shared hosting with Passenger WSGI)
- Brevo as email provider (SMTP key, not API key)
- PostgreSQL as production database (fresh DB, no SQLite migration needed)
- psycopg[binary] >=3.3 (not psycopg2) — Django 5.2 preference, binary needed on shared hosting
- whitenoise for static file serving behind Passenger
- P24 sandbox on production for now (prod credentials pending seller verification)

### Pending Todos

- Task 3 checkpoint: Operator must create MyDevil virtualenv and configure panel interpreter

### Blockers/Concerns

- MyDevil server-side virtualenv not yet created (Task 3 checkpoint — blocking phase completion)
- P24 production credentials not yet obtained (seller verification pending)
- Brevo SPF/DKIM DNS propagation can take up to 48h — set up DNS records early
- MyDevil PostgreSQL host address only known after SSH login (pgsqlX.mydevil.net)

## Session Continuity

Last session: 2026-04-10
Stopped at: Phase 7 executing — 07-01 Tasks 1-2 done, Task 3 checkpoint pending; 07-02 complete
Resume file: None
