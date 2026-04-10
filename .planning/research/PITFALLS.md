# Deployment Pitfalls: Django on MyDevil.net

**Domain:** Production deployment of existing Django app to shared hosting
**Researched:** 2026-04-10
**Confidence:** HIGH (MyDevil docs verified, Django deployment checklist cross-referenced)

---

## Critical Pitfalls

Mistakes that cause outages, data loss, or security breaches on launch day.

---

### Pitfall 1: Static and Media Files Vanish When DEBUG=False

**What goes wrong:**
The site deploys, HTML loads, but every page is unstyled -- no CSS, no images, no JavaScript. The admin panel is bare HTML. Product images show broken links.

**Why it happens:**
In `backend/urls.py` lines 21-23, static and media file serving is wrapped in `if settings.DEBUG`. When `DEBUG=False` in production, Django stops serving these files entirely. Passenger/Nginx on MyDevil does not automatically know where static files live.

**Consequences:**
- Completely broken UI on first deployment
- Admin panel unusable (no styles)
- Product images, ebook covers, recipe photos all missing
- Panic-driven "set DEBUG=True in production" which exposes tracebacks and secrets

**Prevention:**
1. Run `python manage.py collectstatic` to copy all static files into `STATIC_ROOT` (currently `public/static/`)
2. On MyDevil, the `public_python/public/` directory is served directly by Nginx. The current `STATIC_ROOT = BASE_DIR / "public" / "static"` aligns with this -- verify the physical path resolves to `/usr/home/LOGIN/domains/DOMENA/public_python/public/static/`
3. For media files: ensure `MEDIA_ROOT` points to a directory Nginx can serve (same `public/` tree)
4. Do NOT add WhiteNoise -- MyDevil's Nginx handles static serving natively from the `public/` directory
5. Remove the `if settings.DEBUG` guard from `urls.py` for media files OR configure Nginx aliases (MyDevil panel)

**Detection:**
- Page loads but is unstyled
- Browser dev tools show 404 for `/static/` and `/media/` URLs
- `manage.py check --deploy` warns about `STATIC_ROOT`

**Phase to address:** Phase 1 (Server configuration) -- must be first thing tested after initial deployment

---

### Pitfall 2: Missing HTTPS Security Settings

**What goes wrong:**
Site works on HTTPS but session cookies and CSRF tokens are sent over plain HTTP. Mixed content warnings appear. CSRF verification fails on form submissions because `CSRF_TRUSTED_ORIGINS` is not set for the production domain.

**Why it happens:**
The current `settings.py` has zero HTTPS-related security settings. No `CSRF_TRUSTED_ORIGINS`, no `SECURE_SSL_REDIRECT`, no `SESSION_COOKIE_SECURE`, no `CSRF_COOKIE_SECURE`. These are invisible in development but cause real failures in production behind HTTPS.

**Consequences:**
- CSRF verification fails on all POST forms (checkout, newsletter signup, login) with a 403 Forbidden error
- Session hijacking possible if cookies leak over HTTP
- Search engines may index HTTP version, splitting SEO authority

**Prevention:**
Add these settings to production `.env` / settings:
```python
# Required for Django 4+ behind HTTPS
CSRF_TRUSTED_ORIGINS = ["https://kuchennakomitywa.pl", "https://www.kuchennakomitywa.pl"]

# Cookie security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HTTPS enforcement
SECURE_SSL_REDIRECT = True  # Only if MyDevil doesn't handle this at Nginx level
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Proxy header (Passenger behind Nginx)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
```

**Detection:**
- 403 Forbidden on any form submission (checkout, login, newsletter)
- Django logs show "CSRF verification failed. Origin checking failed"
- `manage.py check --deploy` flags missing security settings

**Phase to address:** Phase 1 (Server configuration) -- immediately after HTTPS/SSL cert is active

---

### Pitfall 3: SQLite-to-PostgreSQL Data Migration Breaks on Type Strictness

**What goes wrong:**
Migrations run successfully on empty PostgreSQL, but `loaddata` from SQLite dump fails with type errors, integrity constraint violations, or truncated data.

**Why it happens:**
SQLite is dynamically typed -- it silently stores a string in an IntegerField, or a 200-character string in a `CharField(max_length=50)`. PostgreSQL enforces types strictly. Also, Django's `contenttypes` framework auto-generates records that conflict with fixture data.

**Consequences:**
- Data migration fails midway, leaving PostgreSQL in an inconsistent state
- Some data silently truncated or corrupted
- Foreign key references break if content types don't match

**Prevention:**
1. Use `dumpdata` with explicit exclusions:
   ```bash
   python manage.py dumpdata \
     --exclude contenttypes \
     --exclude auth.permission \
     --exclude admin.logentry \
     --exclude sessions \
     --natural-foreign --natural-primary \
     --indent 2 > data.json
   ```
2. Create a fresh PostgreSQL database, run `migrate` (creates clean schema)
3. Load data: `python manage.py loaddata data.json`
4. If the SQLite database is small (which it likely is for a pre-launch app), consider skipping data migration entirely -- just recreate admin user and re-enter any products via admin panel
5. Test the dump/load cycle on a local PostgreSQL BEFORE doing it on the server

**Detection:**
- `loaddata` throws `IntegrityError` or `DataError`
- Model counts differ between SQLite and PostgreSQL after migration
- Some model fields contain `None` where they shouldn't

**Phase to address:** Phase 2 (Database migration) -- do a dry run locally first

---

### Pitfall 4: passenger_wsgi.py Misconfiguration

**What goes wrong:**
Site shows generic 500 error or "Application Error" page. No Django error page at all -- Passenger itself fails before Django even starts.

**Why it happens:**
MyDevil requires a specific `passenger_wsgi.py` at the root of `public_python/`. Common mistakes:
- Wrong `DJANGO_SETTINGS_MODULE` value
- Not adding the project directory to `sys.path`
- virtualenv Python not activated in the Passenger context
- `.env` file not found because Passenger's working directory differs from expectation

**Consequences:**
- Complete site outage with unhelpful error
- Debugging is blind -- errors go to `/usr/home/LOGIN/domains/DOMENA/logs/error.log`, not Django's debug page

**Prevention:**
Create `passenger_wsgi.py` in the project root:
```python
import sys
import os

# Ensure project directory is on the Python path
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Verify it works by running `python passenger_wsgi.py` over SSH -- if it produces no output/errors, it's correct.

**Detection:**
- Site shows "Application Error" or blank 500 page
- Check `/usr/home/LOGIN/domains/DOMENA/logs/error.log` for Python tracebacks
- SSH in and run `python passenger_wsgi.py` manually

**Phase to address:** Phase 1 (Server configuration) -- the very first deployment step

---

### Pitfall 5: .env File Not Found by Passenger

**What goes wrong:**
Passenger starts Django, but `django-environ` cannot find the `.env` file. All env vars resolve to defaults: `DEBUG=False` (good), but `SECRET_KEY` raises `ImproperlyConfigured`, or worse, P24 credentials are empty, email backend falls back to console (emails silently lost).

**Why it happens:**
In `settings.py` line 24: `environ.Env.read_env(BASE_DIR / ".env")`. `BASE_DIR` is `Path(__file__).resolve().parent.parent` -- this resolves to the project root. But if Passenger's working directory is different, or the `.env` file is placed in the wrong directory on the server, it silently fails. `django-environ`'s `read_env()` does NOT raise an error if the file is missing -- it just skips it.

**Consequences:**
- `SECRET_KEY` may raise an error (good -- fails fast) or fall back to some default (bad -- insecure)
- P24 credentials default to empty strings/zeros -- payment registration silently fails
- Email backend defaults to console -- order confirmations and ebook deliveries vanish into server logs
- `ALLOWED_HOSTS` defaults to `["localhost", "127.0.0.1"]` -- site returns 400 Bad Request

**Prevention:**
1. Place `.env` file in the same directory as `manage.py` on the server
2. After deploying, SSH in and verify: `cat /usr/home/LOGIN/domains/DOMENA/public_python/.env`
3. Test env loading: `python -c "import environ; env = environ.Env(); environ.Env.read_env('.env'); print(env('SECRET_KEY'))"`
4. Make `SECRET_KEY` have no default in settings (it already doesn't -- `env("SECRET_KEY")` will crash if missing, which is correct)
5. Consider adding an explicit check: `if not (BASE_DIR / ".env").exists(): raise ...`

**Detection:**
- Site crashes with `ImproperlyConfigured: Set the SECRET_KEY environment variable`
- Site works but payments fail silently (P24 credentials empty)
- Emails don't arrive (console backend active)
- `ALLOWED_HOSTS` error in logs

**Phase to address:** Phase 1 (Server configuration) -- immediately after file deployment

---

### Pitfall 6: Brevo SMTP Key vs API Key Confusion

**What goes wrong:**
Email sending fails with authentication errors. Or worse, it silently fails and emails are never delivered.

**Why it happens:**
Brevo provides two types of keys: API keys (for REST API) and SMTP keys (for SMTP relay). Using the API key as `EMAIL_HOST_PASSWORD` causes SMTP authentication to fail. The error message from Brevo's SMTP server may be cryptic ("Authentication failed" or connection timeout).

**Consequences:**
- All transactional emails fail: order confirmations, ebook deliveries, newsletter confirmations, password resets
- Customers pay but never receive ebook PDFs
- Newsletter double opt-in flow is completely broken

**Prevention:**
Correct Brevo SMTP configuration:
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-brevo-login@email.com
EMAIL_HOST_PASSWORD=xsmtpsib-XXXXXXXX  # SMTP key, NOT API key
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Kuchenna Komitywa <noreply@kuchennakomitywa.pl>
```

Additionally:
1. Authenticate your sending domain in Brevo dashboard (DKIM/SPF records in DNS)
2. Without domain authentication, Brevo replaces your sender address with `@brevosend.com` since Feb 2024 policy change
3. The `DEFAULT_FROM_EMAIL` domain must match the authenticated domain in Brevo
4. Test with `python manage.py shell -c "from django.core.mail import send_mail; send_mail('Test', 'Body', None, ['your@email.com'])"`

**Detection:**
- `SMTPAuthenticationError` in logs
- Emails sent but never arrive (check Brevo dashboard for delivery logs)
- Sender address shows as `@brevosend.com` instead of your domain

**Phase to address:** Phase 3 (Email configuration) -- test before any email-dependent feature goes live

---

### Pitfall 7: P24 Webhook URL Points to Localhost

**What goes wrong:**
Payments process on Przelewy24's side, but the webhook notification never reaches the production server. Orders stay in "pending" status forever. Ebooks are never delivered.

**Why it happens:**
In `shop/views.py` line 153-154, the webhook URL is built with `request.build_absolute_uri("/zamowienie/webhook/p24/")`. This generates the URL based on the incoming request's `Host` header. If the server is misconfigured (wrong `ALLOWED_HOSTS`, missing `SECURE_PROXY_SSL_HEADER`), this can generate `http://localhost/zamowienie/webhook/p24/` instead of the production URL.

Also: P24 sandbox and production are separate systems. Sandbox webhook URLs registered with sandbox credentials won't work with production credentials.

**Consequences:**
- Orders stuck in "pending" -- customers see "Payment being processed" indefinitely
- Ebook delivery never triggered (depends on webhook setting order status to "paid")
- Order confirmation emails never sent

**Prevention:**
1. Ensure `ALLOWED_HOSTS` includes the production domain
2. Set `SECURE_PROXY_SSL_HEADER` so `build_absolute_uri()` generates `https://` URLs
3. After first real P24 transaction, check the P24 merchant panel to see what webhook URL was registered
4. Test the webhook endpoint is reachable from outside: `curl -X POST https://kuchennakomitywa.pl/zamowienie/webhook/p24/` (should return 400, not 404 or connection refused)
5. Remember: P24 sandbox credentials and production credentials are completely separate. Update all four values: `P24_MERCHANT_ID`, `P24_POS_ID`, `P24_CRC_KEY`, `P24_API_KEY`

**Detection:**
- Payment succeeds on P24 page but order status stays "pending"
- No webhook entries in Django logs
- P24 merchant panel shows webhook delivery failures

**Phase to address:** Phase 4 (Payments configuration) -- test end-to-end with sandbox on production URL

---

### Pitfall 8: Ebook PDF Attachment Fails on Production File Paths

**What goes wrong:**
Ebook delivery emails send successfully but without the PDF attachment, or `send_ebook_delivery()` crashes with `FileNotFoundError`.

**Why it happens:**
In `shop/emails.py` line 76, ebook files are attached via `product.ebook_file.path`. This returns the absolute filesystem path based on `MEDIA_ROOT`. If `MEDIA_ROOT` on production differs from development, or if ebook files weren't uploaded/migrated to the production server, the path doesn't exist.

**Consequences:**
- Customer pays for ebook, receives email without PDF
- The function has a try/except (line 77-81) that logs the error but still sends the email -- so the customer gets a "Here are your ebooks" email with zero attachments
- Silent failure: no crash, no user-visible error, just missing attachment

**Prevention:**
1. After deploying, upload ebook PDFs through the Django admin on the production server
2. Verify `MEDIA_ROOT` path exists and is writable: `ls -la /usr/home/LOGIN/domains/DOMENA/public_python/public/media/`
3. Test ebook delivery end-to-end with a real order in sandbox mode
4. Consider adding a check: if no ebook files were attached, don't send the email (or send a different error notification to admin)
5. Do NOT copy ebook files from dev SQLite's media directory blindly -- upload fresh through admin

**Detection:**
- Ebook delivery email arrives but has no attachment
- Error logs show "Failed to attach ebook for order X, product Y: FileNotFoundError"
- `MEDIA_ROOT` directory is empty on production

**Phase to address:** Phase 4 (Payments) -- after products are recreated in production DB

---

## Moderate Pitfalls

---

### Pitfall 9: PostgreSQL Requires psycopg2 (Not in requirements.txt)

**What goes wrong:**
Django crashes on startup with `ModuleNotFoundError: No module named 'psycopg2'` or the database engine error.

**Why it happens:**
The current `requirements.txt` only has SQLite-compatible packages. PostgreSQL requires either `psycopg2-binary` (for development/shared hosting) or `psycopg2` (compiled, for production). Neither is listed.

**Prevention:**
Add `psycopg2-binary` to `requirements.txt`. On MyDevil shared hosting, `psycopg2-binary` is preferred because compiling `psycopg2` from source requires `libpq-dev` headers which may not be available.

Update database config in `.env`:
```env
DATABASE_URL=postgres://user:password@pgsql.mydevil.net:5432/dbname
```

And in settings.py, use `django-environ`'s database URL parser:
```python
DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3"),
}
```

**Detection:**
- Django fails to start with import error
- `pip install psycopg2` fails with compilation errors (use `psycopg2-binary` instead)

**Phase to address:** Phase 2 (Database migration) -- before changing database engine

---

### Pitfall 10: MyDevil Auto-Shutdown After 24h Idle

**What goes wrong:**
Site goes down after a period of inactivity. First visitor after idle gets a 502 or slow response while Passenger cold-starts.

**Why it happens:**
MyDevil automatically disables Passenger applications that have been idle for 24 hours. This is a shared hosting resource management feature.

**Prevention:**
1. Set up a cron job to ping the site every 12 hours: `devil cron add "0 */12 * * * curl -s https://kuchennakomitywa.pl > /dev/null"`
2. Accept that cold-start delay (2-5 seconds) exists for very first request
3. Configure `devil www options DOMENA processes 2` to keep at least 2 worker processes

**Detection:**
- First request after long idle takes 5-10 seconds
- Site returns 502 briefly, then works on refresh

**Phase to address:** Phase 1 (Server configuration) -- after initial deployment is verified

---

### Pitfall 11: Stale .pyc Files After Code Update

**What goes wrong:**
You deploy new code via git pull or rsync, but the site keeps running the old logic. Passenger uses cached `.pyc` bytecode files.

**Why it happens:**
Passenger doesn't clear Python bytecode cache on deploy. Old `.pyc` files in `__pycache__` directories take precedence.

**Prevention:**
Create a deployment script that:
```bash
#!/bin/bash
cd /usr/home/LOGIN/domains/DOMENA/public_python
git pull origin main
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -delete
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
devil www restart DOMENA
```

**Detection:**
- New feature not visible after deploy
- Old bug persists despite fix being in the code
- `python -c "import py_compile"` shows old timestamps on `.pyc` files

**Phase to address:** Phase 1 (Server configuration) -- create deploy script as part of initial setup

---

### Pitfall 12: ALLOWED_HOSTS Missing Production Domain

**What goes wrong:**
Every request returns "400 Bad Request" with no additional information. Site is completely inaccessible.

**Why it happens:**
Current default is `ALLOWED_HOSTS = ["localhost", "127.0.0.1"]`. If the `.env` file doesn't include the production domain, Django rejects all requests from the real domain.

**Prevention:**
In production `.env`:
```env
ALLOWED_HOSTS=kuchennakomitywa.pl,www.kuchennakomitywa.pl
```

**Detection:**
- Blank "400 Bad Request" page (no Django debug info because `DEBUG=False`)
- Error log shows "Invalid HTTP_HOST header"

**Phase to address:** Phase 1 (Server configuration) -- must be set before first test

---

### Pitfall 13: Email Attachments Exceed Brevo Size Limits

**What goes wrong:**
Ebook delivery emails fail for large PDFs. Brevo rejects the message.

**Why it happens:**
Brevo has a 20MB message size limit. Ebook PDFs, especially recipe books with high-quality images, can easily exceed this. The current code (`shop/emails.py`) attaches the raw PDF file with no size check.

**Prevention:**
1. Keep ebook PDFs under 15MB (leave margin for email encoding overhead -- base64 increases size by ~33%)
2. Practically: any PDF over 10MB is risky for email attachment
3. Consider compressing PDFs before upload (admin guidance)
4. Future improvement: generate signed download links instead of attachments

**Detection:**
- `send_ebook_delivery()` logs "Failed to send ebook email" for specific products
- Brevo dashboard shows rejected messages with size limit errors

**Phase to address:** Phase 3 (Email configuration) -- verify ebook file sizes before going live

---

## Minor Pitfalls

---

### Pitfall 14: Missing Logging Configuration for Production

**What goes wrong:**
Errors occur but nobody knows. The default Django logging goes to console, which Passenger may or may not capture in `error.log`.

**Prevention:**
Add file-based logging to settings:
```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
        },
    },
    "root": {
        "handlers": ["file"],
        "level": "WARNING",
    },
}
```

**Phase to address:** Phase 1 (Server configuration)

---

### Pitfall 15: Session Backend on Default Database-Backed Sessions

**What goes wrong:**
Session-based cart works but `django_session` table grows indefinitely. On PostgreSQL this causes slow queries over time.

**Prevention:**
Set up periodic session cleanup via cron:
```bash
devil cron add "0 3 * * * cd /path/to/project && python manage.py clearsessions"
```

**Phase to address:** Phase 1 (Server configuration) -- set up cron after deploy

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Server setup (Passenger) | passenger_wsgi.py wrong path/settings | Test with `python passenger_wsgi.py` over SSH before restart |
| Server setup (static) | CSS/JS/images 404 when DEBUG=False | Run collectstatic, verify Nginx serves from public/ |
| Server setup (HTTPS) | CSRF_TRUSTED_ORIGINS missing | Add domain to CSRF_TRUSTED_ORIGINS, test form submission |
| Server setup (.env) | .env not found, defaults used silently | SSH verify .env exists, test SECRET_KEY loads |
| Database migration | Type strictness breaks loaddata | Test dump/load locally first, exclude contenttypes |
| Database migration | psycopg2 not installed | Add psycopg2-binary to requirements.txt |
| Email (Brevo) | SMTP key vs API key confusion | Use xsmtpsib- prefixed key, test send_mail in shell |
| Email (Brevo) | Domain not authenticated (DKIM) | Sender rewritten to @brevosend.com -- configure DNS |
| Email (attachments) | Ebook PDF path wrong on production | Upload ebooks through admin on production |
| Payments (P24) | Webhook URL generates localhost | Verify ALLOWED_HOSTS and SECURE_PROXY_SSL_HEADER |
| Payments (P24) | Sandbox vs production credentials mixed | All four P24_* vars must match the environment |
| Deploy workflow | Old .pyc served after code update | Delete __pycache__ + devil www restart in deploy script |

---

## "Looks Done But Isn't" Checklist

Post-deployment verification. Every item must be manually tested on the production URL.

### Server & Infrastructure
- [ ] Site loads with full CSS/JS styling (not just HTML)
- [ ] Admin panel at `/admin/` loads with styles
- [ ] All static files return 200 (check browser Network tab for 404s)
- [ ] Media files (product images) display correctly
- [ ] `manage.py check --deploy` returns no critical warnings
- [ ] Error log at `/usr/home/LOGIN/domains/DOMENA/logs/error.log` is clean

### Security & HTTPS
- [ ] Site redirects HTTP to HTTPS
- [ ] Browser shows padlock icon (no mixed content warnings)
- [ ] Form submission works (login, checkout, newsletter) -- no CSRF 403
- [ ] `SECRET_KEY` is unique and not the .env.example default
- [ ] `DEBUG=False` confirmed (visit a non-existent URL -- should show custom 404, not Django debug page)
- [ ] Django admin URL is not guessable (consider moving from `/admin/`)

### Email
- [ ] Test email arrives in inbox (not spam): `manage.py shell` then `send_mail(...)`
- [ ] Sender shows as "Kuchenna Komitywa" not "@brevosend.com"
- [ ] Newsletter confirmation email works end-to-end (subscribe, receive, click confirm)
- [ ] Order confirmation email arrives after test purchase
- [ ] Ebook PDF is attached to delivery email (not empty email)
- [ ] Password reset email arrives and link works

### Payments
- [ ] Checkout form submits and redirects to P24 payment page
- [ ] P24 webhook URL is `https://` (not `http://` or `localhost`)
- [ ] After sandbox payment, order status changes to "paid" (webhook received)
- [ ] Ebook delivery triggered after payment confirmation
- [ ] P24 cancel/return URLs work (user can go back to site)
- [ ] Webhook endpoint returns 200 for valid P24 requests (test with curl)

### Database
- [ ] All existing products/recipes visible on production (if data was migrated)
- [ ] Admin can create new products, recipes, and they display correctly
- [ ] Order creation works (checkout flow completes)
- [ ] Newsletter subscriber count matches expected (if data migrated)

### Resilience
- [ ] Site recovers after idle period (visit after 24h+ gap)
- [ ] Deploy script works: git pull, collectstatic, migrate, restart
- [ ] Cron jobs active: session cleanup, keep-alive ping

---

## Sources

- [MyDevil.net Django documentation](https://pomoc.mydevil.net/Django/) -- official deployment guide
- [MyDevil.net PostgreSQL documentation](https://pomoc.mydevil.net/PostgreSQL/) -- database management
- [Phusion Passenger WSGI spec](https://www.phusionpassenger.com/library/deploy/wsgi_spec.html) -- passenger_wsgi.py reference
- [Django deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) -- official security checklist
- [Brevo SMTP integration docs](https://developers.brevo.com/docs/smtp-integration) -- SMTP relay configuration
- [Brevo SMTP troubleshooting](https://help.brevo.com/hc/en-us/articles/115000188150-Troubleshooting-issues-with-Brevo-SMTP) -- common SMTP issues
- [Brevo DKIM authentication](https://www.captaindns.com/en/blog/brevo-transactional-email-technical-guide) -- domain authentication requirements
- [Django Forum: SQLite to PostgreSQL migration](https://forum.djangoproject.com/t/migrating-from-sqlite-to-postgresql/29128) -- community migration advice
- [Django static files deployment](https://docs.djangoproject.com/en/5.2/howto/static-files/) -- static file serving in production

---
*Pitfalls research for: v1.1 production deployment (MyDevil.net + PostgreSQL + Brevo SMTP)*
*Researched: 2026-04-10*
