# Architecture: Production Deployment on MyDevil.net

**Domain:** Django production deployment (Passenger WSGI + PostgreSQL + Brevo SMTP)
**Researched:** 2026-04-10
**Confidence:** HIGH

## System Overview: Dev vs Prod

```
DEV (current)                          PROD (MyDevil.net)
──────────────                         ──────────────────
manage.py runserver                    Passenger WSGI (Phusion)
    |                                      |
backend/wsgi.py                        passenger_wsgi.py
    |                                      |
SQLite (db.sqlite3)                    PostgreSQL (pgsqlX.mydevil.net:5432)
    |                                      |
console email backend                 Brevo SMTP (smtp-relay.brevo.com:587)
    |                                      |
Django dev static serving              WhiteNoise middleware (static)
    |                                      |
local /media/ via urlpatterns          /public/media/ (Apache direct-serve)
    |                                      |
http://localhost:8000                   https://kuchennakomitywa.pl (Let's Encrypt)
```

## MyDevil.net Directory Layout

MyDevil expects a specific directory structure. The project lives inside `public_python/` under the domain directory.

```
/usr/home/LOGIN/
├── .virtualenvs/
│   └── komitywa/                  # Python virtualenv
│       └── bin/python             # Interpreter path for DevilWEB panel
│
└── domains/
    └── kuchennakomitywa.pl/
        ├── logs/
        │   └── error.log          # Passenger error log
        │
        └── public_python/         # <-- This IS the project root (BASE_DIR)
            ├── passenger_wsgi.py   # NEW — Passenger entry point
            ├── manage.py
            ├── .env                # NEW — production environment variables
            ├── backend/
            │   ├── settings.py     # MODIFIED — env-driven, no hardcoded values
            │   ├── wsgi.py         # Unchanged
            │   └── urls.py         # Unchanged (static serving handled by WhiteNoise)
            ├── accounts/
            ├── core/
            ├── recipes/
            ├── shop/
            ├── newsletter/
            ├── templates/
            ├── static/             # Source static files (STATICFILES_DIRS)
            └── public/             # Served directly by Apache, bypasses Python
                ├── static/         # STATIC_ROOT (collectstatic output)
                └── media/          # MEDIA_ROOT (ebook PDFs, product images)
```

**Critical:** Files inside `public_python/public/` are served directly by Apache without passing through Python/Passenger. This is the key to efficient static/media serving on MyDevil.

## Component Boundaries

### New Files (to create)

| File | Purpose | Location |
|------|---------|----------|
| `passenger_wsgi.py` | Passenger WSGI entry point | Project root |
| `.env` (production) | Production secrets and config | Project root (NOT in git) |
| `.env.example` | Updated template with all prod vars | Project root (in git) |

### Modified Files

| File | Changes Needed | Why |
|------|----------------|-----|
| `backend/settings.py` | Add DATABASE_URL support, WhiteNoise, security settings | Production-ready configuration |
| `requirements.txt` | Add psycopg2-binary, whitenoise | New production dependencies |
| `backend/urls.py` | No changes needed | WhiteNoise handles static; Apache handles media via /public/ |

### Unchanged Files

| File | Reason |
|------|--------|
| `backend/wsgi.py` | passenger_wsgi.py imports from it |
| All app code (accounts, core, recipes, shop, newsletter) | No app-level changes for deployment |
| `templates/` | No changes needed |

## Component Details

### 1. passenger_wsgi.py (NEW)

The Passenger entry point. Placed at project root alongside `manage.py`.

```python
import sys
import os

# Add project directory to Python path
sys.path.append(os.getcwd())

# Point to Django settings
os.environ["DJANGO_SETTINGS_MODULE"] = "backend.settings"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**Verification:** Run `python passenger_wsgi.py` via SSH. No output = success. Any ImportError or config error will print.

**Restart after changes:** `devil www restart kuchennakomitywa.pl`

### 2. settings.py (MODIFIED)

The current settings.py is already well-structured with django-environ. The changes are additive, not a rewrite.

**Database — switch from hardcoded SQLite to DATABASE_URL:**

```python
# Current (remove):
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# New (replace with):
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="sqlite:///db.sqlite3",
    )
}
```

This lets dev keep using SQLite (no DATABASE_URL in .env) while prod uses PostgreSQL via env var.

**WhiteNoise middleware — add after SecurityMiddleware:**

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # NEW — must be second
    "corsheaders.middleware.CorsMiddleware",
    # ... rest unchanged
]
```

**WhiteNoise storage backend:**

```python
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
```

**Security settings — add at bottom, driven by env:**

```python
# Security (enabled in production via .env)
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=["http://localhost:8000"],
)
```

**STATIC_URL and MEDIA_URL — already correct.** The current `STATIC_ROOT = BASE_DIR / "public" / "static"` and `MEDIA_ROOT = BASE_DIR / "public" / "media"` align perfectly with MyDevil's convention that `/public_python/public/` is served directly by Apache.

### 3. Production .env File

```bash
# Django Core
SECRET_KEY=<generate-50-char-random-string>
DEBUG=False
ALLOWED_HOSTS=kuchennakomitywa.pl,www.kuchennakomitywa.pl

# Database (PostgreSQL on MyDevil)
DATABASE_URL=postgres://DB_USER:DB_PASSWORD@pgsqlX.mydevil.net:5432/DB_NAME

# Email (Brevo SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_HOST_USER=<brevo-smtp-login-email>
EMAIL_HOST_PASSWORD=<brevo-smtp-key>
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Kuchenna Komitywa <noreply@kuchennakomitywa.pl>

# Przelewy24 (sandbox initially)
P24_MERCHANT_ID=<sandbox-merchant-id>
P24_POS_ID=<sandbox-pos-id>
P24_CRC_KEY=<sandbox-crc-key>
P24_API_KEY=<sandbox-api-key>
P24_SANDBOX=True

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
CSRF_TRUSTED_ORIGINS=https://kuchennakomitywa.pl,https://www.kuchennakomitywa.pl

# CORS (may not be needed if no SPA, but keep for API)
CORS_ALLOWED_ORIGINS=https://kuchennakomitywa.pl,https://www.kuchennakomitywa.pl
```

**Important:** Brevo SMTP uses an SMTP key (not an API key). The SMTP login is a unique email address provided by Brevo, not the account email.

### 4. requirements.txt (MODIFIED)

Add production dependencies:

```
django
django-cors-headers
django-environ
djangorestframework
django-allauth
dj-rest-auth
drf-spectacular
requests
Pillow
psycopg2-binary
whitenoise
```

`psycopg2-binary` is the PostgreSQL adapter. Use `-binary` on shared hosting because compiling `psycopg2` from source requires `libpq-dev` headers which may not be available.

## Data Flow Changes

### Request Flow (Dev vs Prod)

**Dev:**
```
Browser → localhost:8000 → Django dev server → views → SQLite → response
Static:  Django staticfiles finders serve from /static/ dirs
Media:   Django urlpatterns serve from /media/ dir
```

**Prod:**
```
Browser → HTTPS → Apache (MyDevil) → Passenger → passenger_wsgi.py
    → Django (WhiteNoise for static) → views → PostgreSQL → response

Static:  WhiteNoise serves from STATIC_ROOT (/public/static/)
         OR Apache serves directly from /public/static/ (bypasses Python)
Media:   Apache serves directly from /public/media/ (bypasses Python)
```

### Static Files Flow

```
Development:
  /static/ (source files) → Django staticfiles finders → served by runserver

Production:
  /static/ (source files) → collectstatic → /public/static/ (compiled)
  Request for /static/css/style.css →
    1. Apache checks /public_python/public/static/css/style.css
    2. If found → served directly (fast, no Python)
    3. If not → Passenger → WhiteNoise serves from STATIC_ROOT (fallback)
```

WhiteNoise adds gzip/brotli compression and far-future cache headers. It also serves as a reliable fallback if Apache direct-serve is not configured for the static path.

### Email Flow

```
Dev:
  Django send_mail() → console.EmailBackend → prints to terminal

Prod:
  Django send_mail() → smtp.EmailBackend → smtp-relay.brevo.com:587 (TLS)
    → Brevo delivers email

Used for:
  - Ebook PDF delivery (attachment)
  - Order confirmation
  - Newsletter double opt-in confirmation
  - Password reset
  - Email verification (allauth)
```

### Database Flow

```
Dev:
  Django ORM → sqlite3 backend → db.sqlite3 file

Prod:
  Django ORM → postgresql backend → pgsqlX.mydevil.net:5432
    Connection: psycopg2-binary adapter
    Pool: Django default (new connection per request, persistent if CONN_MAX_AGE set)
```

## Integration Points

### MyDevil Panel Configuration

| Setting | Value | Where |
|---------|-------|-------|
| Website type | Python | DevilWEB panel → WWW |
| Python interpreter | `/usr/home/LOGIN/.virtualenvs/komitywa/bin/python` | DevilWEB panel → WWW |
| Domain | kuchennakomitywa.pl | DevilWEB panel → Domains |
| SSL | Let's Encrypt | DevilWEB panel → SSL |
| PostgreSQL database | Create via `devil pgsql db add komitywa` | SSH |
| Process limit | Start with default, increase if needed | `devil www options kuchennakomitywa.pl processes N` |

### PostgreSQL on MyDevil

```bash
# Create database (auto-creates user with same name)
devil pgsql db add komitywa

# Note the connection details:
# Host: pgsqlX.mydevil.net (X = server number, e.g., pgsql17.mydevil.net)
# Port: 5432
# Database: komitywa (or LOGIN_komitywa — check with `devil pgsql list`)
# User: komitywa (same as database name)
# Password: set during creation

# Resulting DATABASE_URL for .env:
# DATABASE_URL=postgres://komitywa:PASSWORD@pgsqlX.mydevil.net:5432/komitywa
```

### Brevo SMTP Integration

| Setting | Value |
|---------|-------|
| Host | `smtp-relay.brevo.com` |
| Port | 587 (TLS) or 465 (SSL) |
| Login | Brevo SMTP login email (from Brevo dashboard, NOT account email) |
| Password | Brevo SMTP key (from Brevo dashboard, NOT API key) |
| Encryption | TLS (port 587) |

**DNS setup required:** Add SPF, DKIM, and DMARC records for `kuchennakomitywa.pl` in MyDevil DNS panel to ensure email deliverability. Brevo provides these records in their dashboard.

## Deployment Workflow

### Initial Deployment Order

This order respects dependencies — each step requires the previous ones.

```
1. MyDevil Panel Setup
   ├── Add domain
   ├── Configure SSL (Let's Encrypt)
   └── Add Python website type with virtualenv path

2. Virtualenv + Dependencies
   ├── SSH into server
   ├── Create virtualenv: virtualenv ~/.virtualenvs/komitywa -p /usr/local/bin/python3.12
   ├── Activate: source ~/.virtualenvs/komitywa/bin/activate
   └── pip install -r requirements.txt

3. Database
   ├── devil pgsql db add komitywa
   ├── Note connection details
   └── Test connection from Python shell

4. Upload Project Code
   ├── git clone (or rsync) into /usr/home/LOGIN/domains/kuchennakomitywa.pl/public_python/
   ├── Create .env with production values
   └── Create passenger_wsgi.py

5. Django Setup
   ├── python manage.py migrate (creates all tables in PostgreSQL)
   ├── python manage.py createsuperuser
   ├── python manage.py collectstatic --noinput
   └── python passenger_wsgi.py (verify no errors)

6. Start Application
   ├── devil www restart kuchennakomitywa.pl
   └── Test: visit https://kuchennakomitywa.pl

7. Email Setup
   ├── Configure Brevo SMTP credentials in .env
   ├── Add DNS records (SPF, DKIM, DMARC)
   └── Test: trigger password reset email

8. Przelewy24 (sandbox)
   ├── Configure P24 sandbox credentials in .env
   ├── Set P24 webhook URL to production domain
   └── Test: complete sandbox purchase
```

### Ongoing Deployment (code updates)

```bash
# SSH into server
ssh LOGIN@sX.mydevil.net

# Navigate to project
cd ~/domains/kuchennakomitywa.pl/public_python

# Pull changes
git pull origin main

# Activate virtualenv
source ~/.virtualenvs/komitywa/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Run migrations if needed
python manage.py migrate

# Collect static files if changed
python manage.py collectstatic --noinput

# Restart application
devil www restart kuchennakomitywa.pl
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Splitting settings into base/dev/prod modules
**Why bad for this project:** Adds complexity for a single-developer project. django-environ already handles the dev/prod split via .env file — same settings.py, different env vars.
**Instead:** Single settings.py with `env()` calls and sensible defaults for dev.

### Anti-Pattern 2: Using Gunicorn or systemd on MyDevil
**Why bad:** MyDevil uses Passenger, not systemd. You cannot run persistent background processes. Gunicorn is irrelevant here.
**Instead:** Passenger reads `passenger_wsgi.py` automatically. Use `devil www restart` to reload.

### Anti-Pattern 3: Serving media files through Django in production
**Why bad:** Every media request (product image, ebook PDF) hits Python, wasting Passenger process slots.
**Instead:** Media files in `/public/media/` are served directly by Apache, bypassing Python entirely. This is automatic on MyDevil for anything in the `public/` subdirectory.

### Anti-Pattern 4: Using SECURE_SSL_REDIRECT without checking MyDevil's SSL setup
**Why bad:** If Let's Encrypt is not yet configured, SSL redirect creates an infinite redirect loop.
**Instead:** Configure SSL first in MyDevil panel, verify HTTPS works, THEN enable SECURE_SSL_REDIRECT in .env.

### Anti-Pattern 5: Compiling psycopg2 from source on shared hosting
**Why bad:** Requires `libpq-dev` headers and a C compiler, which may not be available on MyDevil shared hosting.
**Instead:** Use `psycopg2-binary` which includes pre-compiled PostgreSQL client libraries.

## Scalability Considerations

| Concern | Current (dev) | Production (MyDevil) | If outgrows shared hosting |
|---------|---------------|----------------------|---------------------------|
| Concurrent requests | 1 (runserver) | 1-N Passenger processes (configurable) | VPS with Gunicorn + Nginx |
| Database | SQLite (single writer) | PostgreSQL (concurrent reads/writes) | Same PostgreSQL, add connection pooling |
| Static files | Django serves | WhiteNoise + Apache direct-serve | CDN (CloudFlare) |
| Background tasks | None (synchronous) | None (synchronous, acceptable for MVP) | Celery + Redis on VPS |
| Email volume | Console only | Brevo free tier (300/day) | Brevo paid plan |

**Note on background tasks:** The current app sends emails synchronously (ebook delivery, order confirmation, newsletter). This is acceptable for low traffic. If email sending becomes slow under load, consider Brevo's API (async) instead of SMTP, or a cron-based email queue.

## Sources

- [MyDevil.net Django Documentation](https://pomoc.mydevil.net/Django/) — passenger_wsgi.py structure, directory layout, static files, restart commands
- [MyDevil.net Python Documentation](https://pomoc.mydevil.net/Python/) — virtualenv setup, Python version paths, interpreter configuration
- [MyDevil.net PostgreSQL Documentation](https://pomoc.mydevil.net/PostgreSQL/) — devil pgsql commands, connection host pattern, database creation
- [WhiteNoise 6.12 Documentation](https://whitenoise.readthedocs.io/en/stable/django.html) — Django integration, middleware placement, storage backend
- [Brevo SMTP Integration](https://developers.brevo.com/docs/smtp-integration) — smtp-relay.brevo.com, port 587, SMTP key vs API key distinction
- [Brevo SMTP Key Management](https://help.brevo.com/hc/en-us/articles/7959631848850-Create-and-manage-your-SMTP-keys) — SMTP login vs account email
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) — security settings for production
- [django-environ Quick Start](https://django-environ.readthedocs.io/en/latest/quickstart.html) — DATABASE_URL format, env.db() usage

---
*Architecture research for: v1.1 Production Deployment on MyDevil.net*
*Researched: 2026-04-10*
