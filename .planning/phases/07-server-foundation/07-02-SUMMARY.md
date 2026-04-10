---
phase: 07-server-foundation
plan: 02
subsystem: infra
tags: [deploy, mydevil, bash, env-config, gitignore]

# Dependency graph
requires:
  - phase: 07-server-foundation
    provides: "Passenger WSGI entry point, WhiteNoise, production settings"
provides:
  - "deploy.sh one-command deployment script"
  - ".env.example with all production variables documented"
  - ".gitignore excludes logs/ and collectstatic output"
affects: [08-database, 09-email, 10-payments]

# Tech tracking
tech-stack:
  added: []
  patterns: ["deploy.sh with set -e fail-fast", "commented env vars for future phases"]

key-files:
  created: [deploy.sh]
  modified: [.env.example, .gitignore]

key-decisions:
  - "deploy.sh uses set -e for fail-fast on errors"
  - "Security env vars commented out in .env.example (Phase 8 activates after HTTPS)"
  - "DATABASE_URL commented out (SQLite default until Phase 8)"

patterns-established:
  - "deploy.sh sequence: pull, venv, install, migrate, collectstatic, clear cache, restart"
  - ".env.example as single source of truth for all production env vars"

requirements-completed: [INFRA-05, INFRA-02]

# Metrics
duration: 1min
completed: 2026-04-10
---

# Phase 7 Plan 02: Deploy Script & Environment Summary

**One-command deploy.sh with set -e fail-fast, cache clearing, and .env.example documenting all production variables**

## Performance

- **Duration:** 1 min 24s
- **Started:** 2026-04-10T07:44:38Z
- **Completed:** 2026-04-10T07:46:02Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- deploy.sh with full deployment sequence: pull, venv, deps, migrate, collectstatic, cache clear, restart
- .env.example extended with DATABASE_URL, CORS, and security settings for all future phases
- .gitignore updated to exclude logs/ directory and collectstatic output (public/static/, public/media/)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create deploy.sh deployment script** - `1c1f365` (feat)
2. **Task 2: Update .env.example and .gitignore for production** - `c4166b5` (chore)

## Files Created/Modified
- `deploy.sh` - One-command deployment script for MyDevil (executable, set -e, 7-step sequence)
- `.env.example` - Extended with DATABASE_URL, CORS_ALLOWED_ORIGINS, and commented security settings
- `.gitignore` - Added logs/, public/static/, public/media/ exclusions

## Decisions Made
- deploy.sh uses set -e so failed migrations stop before restart (D-01 from context)
- __pycache__ clearing before restart prevents stale bytecode on Passenger (D-02)
- Security settings in .env.example are commented out -- Phase 8 activates them after HTTPS
- DATABASE_URL commented out with postgres example -- SQLite remains default until Phase 8

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- deploy.sh ready to use once server has virtualenv at ~/.virtualenvs/komitywa/
- .env.example documents all vars needed -- operator copies to .env and fills values
- Phase 8 (database) can uncomment DATABASE_URL and security settings

---
*Phase: 07-server-foundation*
*Completed: 2026-04-10*
