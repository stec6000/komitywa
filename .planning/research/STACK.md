# Technology Stack

**Project:** Kuchenna Komitywa - v1.1 Production Deployment
**Researched:** 2026-04-10
**Scope:** Production deployment on MyDevil.net shared hosting
**Overall confidence:** HIGH

## Context

The application is fully built (v1.0 complete). This research covers ONLY the packages and configuration changes needed to go from local dev (SQLite, console email, `runserver`) to production on MyDevil.net (PostgreSQL, Brevo SMTP, Passenger WSGI, HTTPS).

The existing stack (Django 5.2, django-environ, Bootstrap 5, allauth, DRF, etc.) is validated and unchanged.

## New Production Dependencies

### Database Adapter

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| psycopg[binary] | 3.3.3 | PostgreSQL adapter for Django 5.2 | Django 5.2 prefers psycopg3 over psycopg2. The `[binary]` extra bundles libpq so no system-level PostgreSQL client libraries are needed on MyDevil -- critical for shared hosting where you cannot install system packages. New project = use the modern driver. |

**Install:** `pip install "psycopg[binary]>=3.3,<3.4"`

**Why not psycopg2-binary:** psycopg2 is maintenance-only (no new features). Django 5.2 tries to import `psycopg` (v3) first, falling back to `psycopg2` only if missing. psycopg3 also enables connection pooling via `psycopg-pool` if needed later.

**Confidence:** HIGH -- verified via Django Forum and PyPI (psycopg 3.3.3, released 2026-02-18).

### Static File Serving

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| whitenoise | 6.12.0 | Serve static files from Django/Passenger | On MyDevil, files in `/public_python/public/` are served statically. WhiteNoise adds gzip/brotli compression, cache headers, and `ManifestStaticFilesStorage` (content-hashed filenames for cache busting). Works as WSGI middleware -- perfect for Passenger. |

**Install:** `pip install "whitenoise>=6.12,<7"`

**Why WhiteNoise over just using the public/ directory:**
- MyDevil's Passenger does serve `/public/` statically, but WhiteNoise adds compression, forever-caching headers, and content-hashed filenames automatically
- With `collectstatic` + WhiteNoise, CSS/JS changes get new filenames = no stale cache issues
- Zero additional server config needed -- it is pure WSGI middleware
- Alternative: rely on MyDevil's native static serving from `/public/` and skip WhiteNoise. This works but loses compression and cache-busting. For a low-traffic site this is acceptable but WhiteNoise costs nothing to add.

**Important note on static + WhiteNoise on MyDevil:** Both can coexist. Passenger serves files from `/public_python/public/` directly (bypassing Python). WhiteNoise handles anything that reaches the WSGI app. Run `collectstatic` to `/public_python/public/static/` and both paths work. WhiteNoise is the safety net.

**Confidence:** HIGH -- verified via WhiteNoise docs and PyPI.

### Security

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| (none needed) | - | Django has built-in security settings | `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` are all built-in Django settings. No extra package required. |

## No New Dependencies Needed For

| Concern | Why No Package | What to Do Instead |
|---------|----------------|--------------------|
| WSGI server | MyDevil runs Passenger natively | Create `passenger_wsgi.py` (see ARCHITECTURE.md) |
| Email/SMTP (Brevo) | Django's built-in `django.core.mail.backends.smtp.EmailBackend` handles SMTP | Configure via env vars: `EMAIL_HOST`, `EMAIL_PORT`, etc. |
| SSL/HTTPS | MyDevil provides free Let's Encrypt via `devil www options DOMAIN sslonly on` | No package, just panel/CLI config |
| Process management | Passenger handles worker processes | `devil www options DOMAIN processes N` |
| Environment variables | django-environ already installed and configured | Just update `.env` file for production values |

## Existing Dependencies -- Production Configuration Changes

### django-environ (already installed)

**DATABASE_URL support:** django-environ's `env.db()` parses `DATABASE_URL` env var into Django's DATABASES dict. Current settings.py hardcodes SQLite -- change to:

```python
DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3"),
}
```

**Production .env example:**
```
DATABASE_URL=postgres://DB_USER:DB_PASS@pgsqlX.mydevil.net:5432/DB_NAME
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-brevo-login@email.com
EMAIL_HOST_PASSWORD=your-brevo-smtp-key
DEBUG=False
ALLOWED_HOSTS=kuchennakomitywa.pl,www.kuchennakomitywa.pl
SECRET_KEY=<generate-new-production-key>
```

## Updated requirements.txt

```
django>=5.2,<5.3
django-cors-headers
django-environ
djangorestframework
django-allauth
dj-rest-auth
drf-spectacular
requests
Pillow
psycopg[binary]>=3.3,<3.4
whitenoise>=6.12,<7
```

**Note:** Pin django to `>=5.2,<5.3` for production stability. All other packages keep loose pins since they are already working.

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| PostgreSQL adapter | psycopg[binary] 3.x | psycopg2-binary | psycopg2 is maintenance-only; Django 5.2 prefers psycopg3; no benefit to using the older driver |
| Static files | whitenoise | Manual collectstatic + MyDevil public/ | Loses compression and cache-busting; WhiteNoise is trivial to add |
| Email | Django built-in SMTP backend | django-anymail (Brevo API) | Anymail adds API-based sending, tracking, webhooks -- overkill for transactional email volume of this site. Standard SMTP works fine with Brevo. Revisit if email volume exceeds Brevo SMTP free tier (300/day). |
| WSGI server | Passenger (MyDevil native) | gunicorn | Cannot run gunicorn on MyDevil shared hosting -- Passenger is the only option |
| Database | PostgreSQL (MyDevil native) | MySQL/MariaDB | PostgreSQL is better supported by Django, has better JSON support, and MyDevil offers both -- PostgreSQL is the right choice |

## What NOT to Add (Overkill for Shared Hosting)

| Package | Why Skip |
|---------|----------|
| gunicorn | MyDevil uses Passenger exclusively -- gunicorn cannot replace it |
| nginx config | Passenger handles request proxying; no nginx access on shared hosting |
| docker / docker-compose | No Docker support on MyDevil shared hosting |
| celery + redis | No persistent daemon processes on MyDevil (apps auto-shutdown after 24h idle). Use synchronous email sending for now; volume is low enough. |
| django-storages + S3 | Media files stored on local filesystem (`/public/media/`). No need for cloud storage at this traffic level. |
| sentry-sdk | Nice to have but not essential for launch. Add in v1.2 if needed. |
| django-anymail | Standard SMTP backend is sufficient for Brevo integration at current volume |
| psycopg-pool | Connection pooling is unnecessary at shared hosting scale |
| collectstatic automation (CI/CD) | Run manually via SSH during deployment; no CI/CD on MyDevil |

## MyDevil.net Platform Specifics

### Available Python Versions
Default: **3.11**. Also available: 3.8, 3.9, 3.10, 3.12.

**Recommendation:** Use Python 3.11 (the default). It is well-tested with Django 5.2 and avoids edge-case compatibility issues with newer 3.12. If 3.12 is needed later, it is available.

### PostgreSQL on MyDevil
- Server address: `pgsqlX.mydevil.net` (X = your server number, e.g., `pgsql5.mydevil.net` for `s5.mydevil.net`)
- Create database: `devil pgsql db add DB_NAME` (auto-creates matching user)
- Set password: `devil pgsql passwd DB_NAME`
- Extensions available: pg_trgm, hstore, uuid-ossp, pgcrypto, and more via `devil pgsql extensions DB_NAME EXTENSION`
- Management UI: phpPgAdmin at `pga.mydevil.net`

### Compilation Flags for pip install
Before installing packages with C extensions (like psycopg[c] if used instead of binary):
```bash
export CFLAGS="-I/usr/local/include"
export CXXFLAGS="-I/usr/local/include"
export MAX_CONCURRENCY=1 CPUCOUNT=1 MAKEFLAGS="-j1"
```

Not needed with `psycopg[binary]` since it bundles pre-compiled libpq.

### Environment Variables for Passenger
**Critical:** Set persistent env vars in `~/.bash_profile` only. Passenger does NOT read `.bashrc` or `.shrc`. However, since django-environ reads from `.env` file, this is only relevant for `DJANGO_SETTINGS_MODULE` if not set in `passenger_wsgi.py`.

### Application Restart
```bash
devil www restart DOMAIN
```
Apps auto-shutdown after 24h without requests and auto-restart on next access.

### Process Limits
```bash
devil www options DOMAIN processes N
```
Range: 1 to 80% of account's system processes. Start with 2-3 for a low-traffic site.

## Brevo SMTP Configuration

| Setting | Value |
|---------|-------|
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | `smtp-relay.brevo.com` |
| `EMAIL_PORT` | `587` |
| `EMAIL_USE_TLS` | `True` |
| `EMAIL_HOST_USER` | Brevo account email |
| `EMAIL_HOST_PASSWORD` | Brevo **SMTP key** (not API key) |

**Important:** Use an SMTP key from Brevo dashboard, NOT the API key. They are different credentials.

**Free tier:** 300 emails/day -- more than sufficient for order confirmations, ebook delivery, newsletter confirmation, and password resets at launch scale.

## Sources

- [MyDevil.net Django docs](https://pomoc.mydevil.net/Django/) -- official deployment guide
- [MyDevil.net Python docs](https://pomoc.mydevil.net/Python/) -- available versions, virtualenv, pip
- [MyDevil.net PostgreSQL docs](https://pomoc.mydevil.net/PostgreSQL/) -- database setup and management
- [MyDevil.net Website docs](https://pomoc.mydevil.net/Strona_WWW/) -- SSL, site types, process management
- [psycopg 3.3.3 on PyPI](https://pypi.org/project/psycopg/) -- latest version, binary extras
- [Django Forum: psycopg2 support in 5.2](https://forum.djangoproject.com/t/is-psycopg2-still-supported-in-django-5-2/41032) -- Django's preference for psycopg3
- [WhiteNoise 6.12.0 docs](https://whitenoise.readthedocs.io/en/stable/django.html) -- Django integration
- [Brevo SMTP relay docs](https://help.brevo.com/hc/en-us/articles/7924908994450-Send-transactional-emails-using-Brevo-SMTP) -- SMTP configuration
- [django-environ docs](https://django-environ.readthedocs.io/en/latest/types.html) -- DATABASE_URL format
- [Blog: Django on MyDevil](https://blog.joanna-siwiec.pl/aplikacja-django-na-serwerze-mydevil/1849/) -- real-world deployment walkthrough

---
*Stack research for: v1.1 Production Deployment on MyDevil.net*
*Researched: 2026-04-10*
