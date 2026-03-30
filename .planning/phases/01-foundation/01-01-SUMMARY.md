---
phase: 01-foundation
plan: 01
subsystem: core-infrastructure
tags: [settings, environ, static-files, media, routing, i18n]
dependency_graph:
  requires: []
  provides: [env-config, static-serving, media-serving, home-route, core-app]
  affects: [backend/settings.py, backend/urls.py]
tech_stack:
  added: [django-environ]
  removed: [python-dotenv]
  patterns: [environ.Env, read_env, env.list]
key_files:
  created:
    - core/__init__.py
    - core/apps.py
    - core/views.py
    - core/urls.py
    - core/tests.py
    - templates/pages/home.html
    - .env
    - .env.example
    - static/css/.gitkeep
    - static/js/.gitkeep
    - static/images/.gitkeep
    - media/.gitkeep
  modified:
    - backend/settings.py
    - backend/urls.py
    - requirements.txt
    - .gitignore
decisions:
  - Replaced python-dotenv with django-environ for typed env var parsing
  - Fixed .gitignore to whitelist .env.example and media/.gitkeep
metrics:
  duration: 3m 13s
  completed: "2026-03-30T21:26:41Z"
  tasks_completed: 2
  tasks_total: 2
  tests_added: 10
  tests_passing: 10
---

# Phase 01 Plan 01: Django Environment and Core App Summary

Django-environ config with .env loading, static/media directories, Polish locale, and core app with home view at /

## What Was Done

### Task 1: Migrate settings.py to django-environ and configure static/media
- Replaced `python-dotenv` with `django-environ` in requirements.txt
- Rewrote `backend/settings.py` to load SECRET_KEY, DEBUG, ALLOWED_HOSTS from `.env` via `environ.Env`
- Created `.env` (gitignored) and `.env.example` (tracked) with configuration template
- Configured `STATICFILES_DIRS`, `STATIC_ROOT`, `MEDIA_URL`, `MEDIA_ROOT`
- Set `LANGUAGE_CODE = "pl"` and `TIME_ZONE = "Europe/Warsaw"`
- Refactored CORS config from raw `os.environ.get()` to `env.list()`
- Added `templates` directory to TEMPLATES DIRS setting
- Added `"core"` to INSTALLED_APPS
- Normalized all string quotes to double quotes per project convention
- Created `static/css/`, `static/js/`, `static/images/`, `media/` with `.gitkeep`
- **Commit:** `1d0399e`

### Task 2: Create core app with home view and URL routing
- Created `core/` Django app with `__init__.py`, `apps.py`, `views.py`, `urls.py`, `tests.py`
- Home view renders `templates/pages/home.html` (placeholder for Plan 02)
- Updated `backend/urls.py` to include `core.urls` and serve media files in DEBUG mode
- Created `templates/pages/home.html` with minimal Polish-language placeholder
- Added 10 foundation tests covering env config, static files, media config, and home view
- **Commit:** `7d22c60`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed .gitignore blocking .env.example and media/.gitkeep**
- **Found during:** Task 1
- **Issue:** `.gitignore` pattern `.env.*` blocked `.env.example`; `media/` blocked `media/.gitkeep`
- **Fix:** Added `!.env.example` exception and changed `media/` to `media/*` with `!media/.gitkeep`
- **Files modified:** `.gitignore`
- **Commit:** `1d0399e`

## Verification Results

- `python manage.py check` -- passes (2 deprecation warnings from allauth, not errors)
- `python manage.py test core.tests -v2` -- 10 tests, all pass
- No `django-insecure` string in `backend/settings.py`
- `.env` and `.env.example` both exist
- Settings load correctly: `LANGUAGE_CODE=pl`, `MEDIA_URL=/media/`, `STATIC_URL=/static/`

## Known Stubs

- `templates/pages/home.html` -- minimal placeholder, will be replaced in Plan 02 with branded base.html extension

## Decisions Made

1. **django-environ over python-dotenv**: django-environ provides typed casting (bool, list) and cleaner integration with Django settings
2. **.gitignore whitelist pattern**: Used negation patterns (`!.env.example`, `!media/.gitkeep`) to keep essential files tracked while ignoring secrets and uploads

## Self-Check: PASSED

All 14 created/modified files verified present. Both commit hashes (1d0399e, 7d22c60) found in git log.
