# Phase 7: Server Foundation - Context

**Gathered:** 2026-04-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Deploy Django on MyDevil.net shared hosting via Passenger WSGI with production
configuration — the server infrastructure that Phases 8-10 (DB, email, payments)
build on. Delivers: Passenger WSGI entry point, virtualenv, production .env
configuration, WhiteNoise static serving, Apache-served media files, a
deployment script, and file-based error logging.

</domain>

<decisions>
## Implementation Decisions

### deploy.sh
- **D-01:** Script uses `set -e` — stops immediately on first error. If `migrate`
  fails, no `collectstatic` or `devil www restart` runs on a broken state.
- **D-02:** Script deletes all `__pycache__` directories before restarting
  (`find . -name "__pycache__" -type d -exec rm -rf {} +`). Prevents Passenger
  from serving stale bytecode after a `git pull`.
- **D-03:** Script runs `mkdir -p logs/` at the start — idempotent, works on
  first deploy and every subsequent deploy without manual SSH setup.

Full deploy sequence:
```
set -e
mkdir -p logs/
git pull origin main
source ~/.virtualenvs/komitywa/bin/activate
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
devil www restart kuchennakomitywa.pl
```

### Logging
- **D-04:** Log threshold is WARNING and above — captures errors, unhandled
  exceptions, invalid ALLOWED_HOSTS rejections, deprecation warnings, and
  permission denials. More visibility than ERROR-only during initial launch.
- **D-05:** Include `django.request` logger in addition to root logger. This
  adds request URL and method to HTTP 500 error entries — makes it easy to
  trace which URL triggered an error.
- Log file: `BASE_DIR / "logs" / "django.log"` (INFRA-06 requirement).

Logging config:
```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["file"],
            "level": "WARNING",
            "propagate": True,
        },
    },
    "root": {
        "handlers": ["file"],
        "level": "WARNING",
    },
}
```

### Static Files
- **D-06:** WhiteNoise serves static files (decided in STATE.md). Add
  `whitenoise>=6.12,<7` to `requirements.txt`. Add
  `"whitenoise.middleware.WhiteNoiseMiddleware"` to MIDDLEWARE directly after
  `SecurityMiddleware`. Use `WhiteNoiseStorage` or `ManifestStaticFilesStorage`
  for content-hashed filenames (cache-busting on deploy).

### Media Files
- **D-07:** Media files (ebook PDFs, product images) are served directly by
  Apache from `public/media/` — no Django involvement. `MEDIA_ROOT` is already
  set to `BASE_DIR / "public" / "media"`. `backend/urls.py` needs no changes
  (the `if settings.DEBUG` guard is fine — Apache handles media in production).

### Passenger WSGI
- **D-08:** `passenger_wsgi.py` lives at project root. Activates virtualenv
  from `~/.virtualenvs/komitywa/`, adds project to `sys.path`, sets
  `DJANGO_SETTINGS_MODULE=backend.settings`.

### Production .env Variables
- **D-09:** Phase 7 requires these .env values to be set on the server:
  - `SECRET_KEY` — unique secret (no default acceptable)
  - `DEBUG=False`
  - `ALLOWED_HOSTS=kuchennakomitywa.pl,www.kuchennakomitywa.pl`
  - `DATABASE_URL=sqlite:///db.sqlite3` (still SQLite until Phase 8)
  - Other existing vars (P24, email) remain at dev defaults until their phases

### Security Settings Scope
### Claude's Discretion
- Which security settings land in Phase 7 (pre-HTTPS) vs Phase 8 (with HTTPS).
  Safe to add now: `SECURE_PROXY_SSL_HEADER`, `SECURE_CONTENT_TYPE_NOSNIFF`,
  `X_FRAME_OPTIONS`. Defer until HTTPS active: `SECURE_SSL_REDIRECT`,
  `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `CSRF_TRUSTED_ORIGINS`,
  `SECURE_HSTS_*`. Claude should add the pre-HTTPS settings now and leave
  HTTPS-only settings commented out (or add them in Phase 8 plan).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Deployment Research
- `.planning/research/PITFALLS.md` — Comprehensive deployment pitfalls for
  MyDevil.net. Covers static file 404s on DEBUG=False, .pyc stale cache,
  ALLOWED_HOSTS, .env not found, Passenger misconfiguration. Read before
  writing any deployment code.
- `.planning/research/STACK.md` — Package decisions: WhiteNoise version,
  psycopg[binary] (Phase 8), Passenger as sole WSGI option, static file
  serving strategy.
- `.planning/research/ARCHITECTURE.md` — Directory layout on MyDevil.net,
  exact file locations (`public_python/`, virtualenv at `~/.virtualenvs/`),
  list of new files to create and files to modify.

### Project State
- `.planning/STATE.md` §Decisions — Key v1.1 decisions: WhiteNoise, Brevo,
  psycopg[binary], P24 sandbox on prod.

### Current Codebase
- `backend/settings.py` — Current settings to be modified (WhiteNoise
  middleware, logging, security settings). Read before making changes.
- `requirements.txt` — Add whitenoise, read before modifying.
- `backend/urls.py` — Media serving guard (`if settings.DEBUG`) — NO changes
  needed; Apache serves public/media/ directly.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/wsgi.py` — Existing WSGI app (`backend.wsgi.application`). The new
  `passenger_wsgi.py` imports from this.
- `backend/settings.py` — Already uses `django-environ` with `.env` loading
  at line 24. `STATIC_ROOT`, `MEDIA_ROOT`, `STATICFILES_DIRS` all configured.

### Established Patterns
- `django-environ` pattern: `env("VAR_NAME")` with no default = required
  (crashes fast if missing — intentional for `SECRET_KEY`).
- `environ.Env.read_env(BASE_DIR / ".env")` — .env must be in project root.

### Integration Points
- WhiteNoise: Insert middleware at position 2 in MIDDLEWARE list (after
  SecurityMiddleware, before SessionMiddleware).
- LOGGING: New top-level key in settings.py.
- `passenger_wsgi.py`: New file at project root alongside `manage.py`.

</code_context>

<specifics>
## Specific Ideas

- Virtualenv path on server: `~/.virtualenvs/komitywa/` (from ARCHITECTURE.md)
- Domain: `kuchennakomitywa.pl` (and `www.kuchennakomitywa.pl`)
- MyDevil restart command: `devil www restart kuchennakomitywa.pl`
- INFRA-06 log path: `BASE_DIR / "logs" / "django.log"` — `logs/` directory
  not committed to git (add to .gitignore), created by deploy.sh at first run

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-server-foundation*
*Context gathered: 2026-04-10*
