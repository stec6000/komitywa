# Research Summary — v1.1 Wdrożenie Produkcyjne

**Researched:** 2026-04-10
**Confidence:** HIGH

## Stack Additions

- **psycopg[binary] >=3.3,<3.4** — PostgreSQL adapter required for production DB. The `[binary]` variant bundles pre-compiled libpq, which is essential on MyDevil shared hosting where you cannot install system packages. Django 5.2 prefers psycopg3 over legacy psycopg2.
- **whitenoise >=6.12,<7** — WSGI middleware that serves compressed, cache-busted static files directly from the Django/Passenger process. Adds gzip/brotli and content-hashed filenames on top of MyDevil's native static serving from `public/`. Zero server configuration required.

Note: ARCHITECTURE.md mentions `psycopg2-binary` in one place but STACK.md explicitly recommends `psycopg[binary]` (psycopg3) with detailed rationale. **Use psycopg3.** PITFALLS.md is neutral on version but confirms binary variant is required on shared hosting.

## Feature Categories

### Must Have (Table Stakes)

- `passenger_wsgi.py` created at project root with correct `sys.path` and `DJANGO_SETTINGS_MODULE`
- Python virtualenv created on server, all requirements installed inside it
- Production `.env` deployed on server (not in git) with correct values for all vars
- `settings.py` updated: `DATABASE_URL` via `env.db()`, WhiteNoise middleware, security settings via env
- PostgreSQL database created on MyDevil (`devil pgsql db add komitywa`)
- Django migrations run against fresh PostgreSQL database
- Initial data seeded: superuser created, products uploaded through admin
- `collectstatic` run to populate `public/static/`
- Let's Encrypt SSL certificate configured on MyDevil
- `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS` enabled via `.env`
- `CSRF_TRUSTED_ORIGINS` set to production domain(s) — required for all POST forms under HTTPS
- `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` — required so Passenger behind Apache generates correct `https://` URLs
- `ALLOWED_HOSTS` set to production domain + www variant
- Brevo SMTP credentials in `.env` (SMTP key, not API key)
- Brevo sender domain authenticated via SPF/DKIM DNS records
- All email flows tested end-to-end: registration, password reset, order confirmation, ebook delivery, newsletter double opt-in
- P24 sandbox credentials in production `.env`
- P24 webhook URL updated in sandbox panel to `https://kuchennakomitywa.pl/zamowienie/webhook/p24/`
- Ebook PDFs uploaded through production admin (not copied from dev)

### Nice to Have

- `manage.py check --deploy` run and all warnings resolved before go-live
- `.env.example` committed to git with all required var names (no values)
- Custom `404.html` and `500.html` templates with site branding
- `deploy.sh` script on server (pull, clear pyc, pip install, migrate, collectstatic, restart)
- Django `LOGGING` dict writing errors to file in `logs/django.log`
- Keep-alive cron job pinging site every 12h to prevent 24h auto-shutdown
- `clearsessions` cron job to prevent `django_session` table bloat on PostgreSQL
- Database backup cron job (`pg_dump`) scheduled for first week post-launch

### Out of Scope

- Production P24 credentials (client has not provided them yet; env var swap when ready)
- CI/CD pipeline — manual SSH deployment is correct for this hosting setup
- Docker, nginx config, gunicorn — none are available or needed on MyDevil shared hosting
- Sentry error tracking — defer to v1.2 once there is real traffic
- CDN, Redis, Celery — premature optimization at this traffic level
- Split settings files (base/dev/prod) — django-environ + single `.env` per environment is the right pattern here

## Architecture Changes

**New file: `passenger_wsgi.py`** (project root, alongside `manage.py`)

```python
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Passenger reads this file automatically. Verify with `python passenger_wsgi.py` over SSH — no output means success.

**Modified: `settings.py`** (additive changes only, no rewrite)
1. Database: replace hardcoded SQLite block with `env.db("DATABASE_URL", default="sqlite:///db.sqlite3")` — dev keeps SQLite, prod uses PostgreSQL via env var
2. Middleware: insert `whitenoise.middleware.WhiteNoiseMiddleware` immediately after `SecurityMiddleware`
3. Storages: add `STORAGES = {"staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}}`
4. Security: add `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_*`, `CSRF_TRUSTED_ORIGINS`, `SECURE_PROXY_SSL_HEADER` — all driven by env vars with `False`/`0` defaults so dev is unaffected

**New file: `.env` (production, not in git)** — full template in ARCHITECTURE.md. Key vars: `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `DATABASE_URL`, `EMAIL_*`, `P24_*`, security settings, `CSRF_TRUSTED_ORIGINS`

**Existing `STATIC_ROOT` and `MEDIA_ROOT`** already point to `public/static/` and `public/media/` — these align perfectly with MyDevil's convention that `public_python/public/` is served directly by Apache. No changes needed.

**`requirements.txt`**: add `psycopg[binary]>=3.3,<3.4` and `whitenoise>=6.12,<7`

**No changes to**: `backend/wsgi.py`, `backend/urls.py`, any app code (accounts, core, recipes, shop, newsletter)

## Watch Out For

1. **Static files invisible when DEBUG=False** — run `collectstatic` before first test; check browser Network tab for 404s on `/static/`; if admin panel is unstyled, this is the cause
2. **CSRF 403 on all forms** — `CSRF_TRUSTED_ORIGINS` must be set to production domain before any form (login, checkout, newsletter) is tested; missing this makes every POST fail with 403
3. **`.env` silently not found** — `django-environ`'s `read_env()` does not raise if the file is missing; consequence is `SECRET_KEY` crash OR silent fallback to console email and empty P24 credentials; verify with `cat public_python/.env` after deployment
4. **Brevo SMTP key vs API key** — these are different credentials in Brevo dashboard; using the API key as `EMAIL_HOST_PASSWORD` causes authentication failure; SMTP key starts with `xsmtpsib-`; also add SPF/DKIM DNS records or Brevo rewrites sender to `@brevosend.com`
5. **P24 webhook generates localhost URL** — `build_absolute_uri()` in `shop/views.py` uses the request `Host` header; if `SECURE_PROXY_SSL_HEADER` is missing, it generates `http://localhost/...`; set this header AND verify after first sandbox transaction that the webhook URL in P24 panel is `https://kuchennakomitywa.pl/...`

## Deployment Order

1. DNS: point A record for `kuchennakomitywa.pl` to MyDevil server IP; remove AAAA record if present (blocks Let's Encrypt)
2. MyDevil panel: add domain, configure Python website type with virtualenv path
3. SSH: create virtualenv at `~/.virtualenvs/komitywa`, activate, `pip install -r requirements.txt`
4. SSH: `devil pgsql db add komitywa`, note exact host (pgsqlX.mydevil.net), user, and set password
5. Upload code: `git clone` (or rsync) into `public_python/`
6. Create `.env` at project root with all production values
7. Create `passenger_wsgi.py` at project root
8. SSH: `python manage.py migrate` (creates schema in PostgreSQL)
9. SSH: `python manage.py createsuperuser`
10. SSH: `python manage.py collectstatic --noinput`
11. SSL: configure Let's Encrypt via DevilWEB panel or `devil ssl www add IP le le kuchennakomitywa.pl`
12. Enable HTTPS security settings in `.env` (`SECURE_SSL_REDIRECT=True`, cookie secure flags, HSTS) — only after SSL is confirmed working
13. `devil www restart kuchennakomitywa.pl` — test site loads at `https://`
14. Run `python manage.py check --deploy` — resolve all warnings
15. Brevo: add SPF/DKIM DNS records; configure SMTP credentials in `.env`; test with `manage.py shell` send_mail
16. Upload ebook PDFs through Django admin on production
17. P24: update webhook URL in sandbox panel to production domain, test sandbox purchase end-to-end
18. End-to-end verification: browse, register, order, pay (sandbox), receive email with ebook attachment

## Open Questions

1. **PostgreSQL host address**: MyDevil uses `pgsqlX.mydevil.net` where X matches the server number (e.g., server `s5` uses `pgsql5`). The exact number is only known after logging in — confirm before writing `DATABASE_URL` in `.env`.
2. **Brevo domain verification timing**: SPF/DKIM DNS records can take up to 48h to propagate. If not done before deployment day, emails will send with `@brevosend.com` as sender. Plan DNS setup at least 2 days before go-live.
3. **Production P24 credentials**: The client has not yet provided production merchant credentials. Deployment proceeds with sandbox. Confirm whether switching to production P24 is a single `.env` edit + restart (it is), and agree with the client on timing so there is no gap between credential handoff and the switch.
