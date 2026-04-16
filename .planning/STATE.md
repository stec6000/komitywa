---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Infrastruktura & Bezpieczeństwo
current_plan: 0
status: planning
stopped_at: ~
last_updated: "2026-04-16T00:00:00.000Z"
last_activity: 2026-04-16 -- Milestone v1.2 started
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-16)

**Core value:** Klienci mogą przeglądać przepisy, kupować ebooki i zamawiać gotowe wegańskie produkty z odbiorem osobistym — w jednym miejscu.
**Current focus:** Defining requirements for v1.2

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-04-16 — Milestone v1.2 started

## Milestone Status

**v1.2 Infrastruktura & Bezpieczeństwo** — In Progress

Previous:

- v1.0 MVP shipped — 2026-04-04 (archive: `.planning/milestones/v1.0-ROADMAP.md`)
- v1.1 Wdrożenie Produkcyjne shipped — 2026-04-16

## Current Phase

**Phase:** Not started
**Status:** Defining requirements

🔄 **v1.2 Infrastruktura & Bezpieczeństwo — starting**

- Target: HTTPS, SPF/DKIM, cron keep-alive

## Accumulated Context

### Decisions

- Direct os.environ assignment for DJANGO_SETTINGS_MODULE in passenger_wsgi.py (not setdefault)
- WhiteNoise CompressedManifestStaticFilesStorage for cache-busting static files
- Pre-HTTPS security settings always-on; HTTPS-dependent settings env-driven with safe defaults
- LOGGING at WARNING level for initial launch visibility
- deploy.sh uses set -e for fail-fast on errors
- Security env vars commented out in .env.example (Phase 8 activates after HTTPS)
- DATABASE_URL commented out in .env.example (SQLite default until Phase 8)

v1.1 key decisions:

- MyDevil.net as hosting (shared hosting with Passenger WSGI)
- Brevo as email provider (SMTP key, not API key)
- PostgreSQL as production database (fresh DB, no SQLite migration needed)
- psycopg[binary] >=3.3 (not psycopg2) — Django 5.2 preference, binary needed on shared hosting
- whitenoise for static file serving behind Passenger
- P24 sandbox on production for now (prod credentials pending seller verification)
- [Phase 08-database-ssl]: psycopg[binary] initially chosen, then replaced with psycopg2-binary -- no binary wheel for MyDevil platform
- [Phase 08-database-ssl]: SECURE_SSL_REDIRECT=False (Apache sslonly handles redirect), HSTS starts at 3600s

### Pending Todos

None for Phase 7.

### Blockers/Concerns

- P24 production credentials not yet obtained (seller verification pending)
- Brevo SPF/DKIM DNS propagation can take up to 48h — set up DNS records early
- MyDevil PostgreSQL host address only known after SSH login (pgsqlX.mydevil.net)

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260412-g5k | Zaktualizuj stronę kontakt: adres ul. Bukowa 14 15-796 Białystok, telefon 511562100, usuń godziny otwarcia | 2026-04-12 | ffff1d3 | [260412-g5k-zaktualizuj-stron-kontakt-adres-ul-bukow](.planning/quick/260412-g5k-zaktualizuj-stron-kontakt-adres-ul-bukow/) |
| 260412-gkc | Przepisz sekcję Nasza historia na stronie O nas — luźny ton, bez Warszawy, prosta historia prostego chłopaka | 2026-04-12 | b4964a0 | [260412-gkc-przepisz-sekcj-nasza-historia-na-stronie](.planning/quick/260412-gkc-przepisz-sekcj-nasza-historia-na-stronie/) |

## Session Continuity

Last session: 2026-04-10T18:00:00.000Z
Stopped at: Completed 08-02-PLAN.md — Phase 08 (Database & SSL) fully complete
Resume file: None
