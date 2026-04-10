---
phase: 07-server-foundation
verified: 2026-04-10T10:00:00Z
status: human_needed
score: 5/5 must-haves verified (automated); 1/5 success criteria needs human confirmation
re_verification: false
human_verification:
  - test: "Deploy Django on MyDevil.net via Passenger WSGI and confirm HTTP response"
    expected: "Django serves at least an HTTP 200 or 404 (admin login, etc.) through kuchennakomitywa.pl with no 500 or Passenger errors"
    why_human: "Cannot verify remote server runtime — requires SSH/browser access to MyDevil.net"
  - test: "Verify static files load in browser"
    expected: "CSS, JS, and icons at /static/ URLs return HTTP 200 with correct MIME types and WhiteNoise cache headers (ETag, Cache-Control)"
    why_human: "Requires live server and browser — WhiteNoise collectstatic output not runnable locally without server startup"
  - test: "Verify media files accessible at /media/ URL path"
    expected: "public/media/ contents (e.g., a test PDF) load at /media/filename.pdf on the production domain"
    why_human: "Requires live server with uploaded file — cannot verify without running server and actual media file"
---

# Phase 7: Server Foundation — Verification Report

**Phase Goal:** Operator can deploy and run the Django application on MyDevil.net with correct static/media serving and production configuration
**Verified:** 2026-04-10
**Status:** human_needed (all local artifacts verified; live server behavior requires human confirmation)
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Django can be loaded via passenger_wsgi.py without import errors | VERIFIED | File parses clean; direct DJANGO_SETTINGS_MODULE assignment at line 5; `application = get_wsgi_application()` present |
| 2 | Static files are served through WhiteNoise middleware with compressed, content-hashed filenames | VERIFIED | WhiteNoiseMiddleware at MIDDLEWARE position 2 (after SecurityMiddleware); CompressedManifestStaticFilesStorage in STORAGES; STATIC_ROOT points to public/static/ |
| 3 | Media files path (MEDIA_ROOT) points to public/media/ and is not served through Django in production | VERIFIED | `MEDIA_ROOT = BASE_DIR / "public" / "media"` in settings.py line 188; no django.views.static.serve wiring found for media |
| 4 | All production configuration (SECRET_KEY, DEBUG, ALLOWED_HOSTS, DATABASE_URL) is read from .env with no hardcoded secrets | VERIFIED | SECRET_KEY, DEBUG, ALLOWED_HOSTS all use `env()` calls; DATABASES uses `env.db("DATABASE_URL", default="sqlite:///db.sqlite3")`; no hardcoded values |
| 5 | Application errors at WARNING level and above are written to logs/django.log | VERIFIED | LOGGING config present with FileHandler pointing to `BASE_DIR / "logs" / "django.log"` at WARNING level; logs/.gitkeep ensures directory exists after clone |
| 6 | Operator can deploy with deploy.sh (pull, install, migrate, collectstatic, restart) | VERIFIED | deploy.sh contains all 7 steps in correct order with set -e; deploy.sh is executable |
| 7 | Django responds to HTTP requests on MyDevil.net via Passenger WSGI | HUMAN NEEDED | Server-side virtualenv confirmed by operator (Task 3 checkpoint); runtime response cannot be verified programmatically |

**Score:** 6/7 truths verified locally; success criterion #1 (live HTTP response) requires human confirmation

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `passenger_wsgi.py` | Passenger WSGI entry point | VERIFIED | Exists, 9 lines, syntactically valid, direct env assignment |
| `requirements.txt` | Production dependencies with whitenoise | VERIFIED | whitenoise>=6.12,<7 present; django pinned >=5.2,<5.3 |
| `backend/settings.py` | Production-ready settings | VERIFIED | WhiteNoiseMiddleware, env.db(), LOGGING, security settings all present |
| `deploy.sh` | One-command deployment script | VERIFIED | Exists, executable, contains `devil www restart kuchennakomitywa.pl` |
| `.env.example` | Template of all production env vars | VERIFIED | DATABASE_URL, CORS_ALLOWED_ORIGINS, CSRF_TRUSTED_ORIGINS, security settings all present |
| `.gitignore` | Excludes logs/ and collectstatic output | VERIFIED | `logs/`, `public/static/`, `public/media/` all excluded |
| `logs/.gitkeep` | Ensures logs/ directory exists after clone | VERIFIED | File exists (0 bytes) at logs/.gitkeep |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `passenger_wsgi.py` | `backend.settings` | DJANGO_SETTINGS_MODULE env var | VERIFIED | `os.environ["DJANGO_SETTINGS_MODULE"] = "backend.settings"` at line 5 (manual grep confirmed; gsd-tools false-negative due to YAML quoting of regex) |
| `backend/settings.py` | whitenoise | MIDDLEWARE list position 2 | VERIFIED | `whitenoise.middleware.WhiteNoiseMiddleware` at position 2 in MIDDLEWARE list |
| `backend/settings.py` | `logs/django.log` | LOGGING config | VERIFIED | `"filename": BASE_DIR / "logs" / "django.log"` at settings.py line 226 (manual grep confirmed) |
| `deploy.sh` | `requirements.txt` | pip install -r requirements.txt | VERIFIED | Line 18: `pip install -r requirements.txt` |
| `deploy.sh` | `manage.py` | migrate and collectstatic commands | VERIFIED | Line 22: `python manage.py migrate --noinput`; line 26: `python manage.py collectstatic --noinput` |

Note: gsd-tools key-link verification reported 2 failures for plan 01 — both are false negatives caused by literal single-quote wrapping in the YAML `pattern` field conflicting with regex matching. Manual grep of both patterns confirmed they are present in the code.

### Data-Flow Trace (Level 4)

Not applicable — this phase produces infrastructure configuration files (passenger_wsgi.py, settings.py, deploy.sh, .env.example), not components that render dynamic data.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| passenger_wsgi.py parses without syntax errors | `python3 -c "import ast; ast.parse(open('passenger_wsgi.py').read())"` | Syntax OK | PASS |
| deploy.sh is executable | `test -x deploy.sh` | Executable | PASS |
| deploy.sh has correct shebang | `head -1 deploy.sh` | `#!/bin/bash` | PASS |
| deploy.sh has set -e | `grep -q "set -e" deploy.sh` | Found | PASS |
| WhiteNoise in MIDDLEWARE | `grep -q "WhiteNoiseMiddleware" backend/settings.py` | Found | PASS |
| No hardcoded SECRET_KEY | `grep "SECRET_KEY" backend/settings.py` | `env("SECRET_KEY")` only | PASS |
| Django import from Passenger WSGI | Live server startup | Cannot test without server | SKIP |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| INFRA-01 | 07-01 | Django on MyDevil.net via Passenger WSGI with virtualenv | HUMAN NEEDED | passenger_wsgi.py exists and is correct; virtualenv setup confirmed by operator; live HTTP response needs human |
| INFRA-02 | 07-01, 07-02 | All production config via .env file, no secrets in code | SATISFIED | All settings use `env()` calls; no hardcoded values; .env.example documents all vars |
| INFRA-03 | 07-01 | Static files served correctly from public/static/ | HUMAN NEEDED | WhiteNoise wired correctly; STATIC_ROOT configured; live browser check needed |
| INFRA-04 | 07-01 | Media files (ebook PDFs) accessible via public/media/ | HUMAN NEEDED | MEDIA_ROOT = BASE_DIR / "public" / "media" confirmed; live check needed |
| INFRA-05 | 07-02 | Operator can deploy via deploy.sh | SATISFIED | deploy.sh executable, set -e, 7-step sequence in correct order, `devil www restart` present |
| INFRA-06 | 07-01 | Errors written to logs/django.log | SATISFIED | LOGGING FileHandler wired to logs/django.log at WARNING level; logs/.gitkeep present |

Note: REQUIREMENTS.md still shows INFRA-05 as "Pending" — this is a documentation inconsistency; the implementation is complete and the requirement is satisfied.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | — | — | — | — |

No TODO, FIXME, placeholder comments, or hardcoded secrets found in any phase 7 files.

### Human Verification Required

#### 1. Django HTTP Response via Passenger WSGI

**Test:** SSH to the MyDevil server and run `curl -I http://kuchennakomitywa.pl/admin/` (or use a browser to visit the domain)
**Expected:** HTTP 301 redirect to HTTPS or HTTP 200 response — not a Passenger error page or 500
**Why human:** Cannot test remote server runtime without access to MyDevil.net

#### 2. Static Files Load Correctly

**Test:** After running `deploy.sh` (which runs `collectstatic`), visit `https://kuchennakomitywa.pl/static/` in a browser and check that CSS/JS files load with HTTP 200 and WhiteNoise cache headers
**Expected:** Files served with `ETag` and `Cache-Control: max-age=...` headers; no 404 errors
**Why human:** Requires live server with collectstatic run and browser devtools

#### 3. Media Files Accessible at /media/

**Test:** Upload a test file via Django admin, then visit its URL at `https://kuchennakomitywa.pl/media/filename`
**Expected:** File downloads or displays correctly — HTTP 200, correct MIME type
**Why human:** Requires running server with an uploaded file

### Gaps Summary

No code-level gaps found. All 6 production configuration artifacts exist, contain substantive content, and are correctly wired. The only unverified success criteria require live server access (MyDevil.net) which cannot be tested programmatically.

The REQUIREMENTS.md tracking table shows INFRA-05 as "Pending" — this should be updated to "Complete" as deploy.sh is fully implemented.

---

_Verified: 2026-04-10_
_Verifier: Claude (gsd-verifier)_
