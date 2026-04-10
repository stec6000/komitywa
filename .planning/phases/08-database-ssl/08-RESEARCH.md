# Phase 8: Database & SSL - Research

**Researched:** 2026-04-10
**Domain:** PostgreSQL database setup + Let's Encrypt SSL on MyDevil.net shared hosting
**Confidence:** HIGH

## Summary

Phase 8 converts the Django application from SQLite to PostgreSQL on MyDevil.net and enables HTTPS-only access with Let's Encrypt certificates. The codebase is already well-prepared: `settings.py` uses `env.db("DATABASE_URL", default="sqlite:///db.sqlite3")` for database configuration and has all security settings (SSL redirect, secure cookies, HSTS, CSRF trusted origins) as env-driven with safe defaults. The `.env.example` has all these values commented out, ready for activation.

The work splits into three distinct areas: (1) PostgreSQL setup via MyDevil `devil pgsql` commands + adding `psycopg[binary]` to requirements, (2) Let's Encrypt certificate via `devil ssl` commands + enabling `sslonly` option, and (3) activating security env vars in the production `.env` file and setting up a keep-alive cron job. Since this is a fresh database (no data migration from SQLite needed -- documented as Out of Scope in REQUIREMENTS.md), the PostgreSQL setup is straightforward: create DB, uncomment DATABASE_URL, run migrations, create superuser.

**Primary recommendation:** This phase is almost entirely operational/server-side work. The only code change is adding `psycopg[binary]` to `requirements.txt`. Everything else is `.env` configuration changes and MyDevil CLI commands executed via SSH.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DB-01 | Aplikacja uzywa PostgreSQL jako bazy danych na produkcji | `devil pgsql db add` creates DB; `DATABASE_URL` env var already supported in settings.py; `psycopg[binary]>=3.3` needed in requirements.txt |
| DB-02 | Wszystkie migracje Django sa wykonane poprawnie na PostgreSQL | `python manage.py migrate --noinput` in deploy.sh already handles this; fresh DB means no migration conflicts |
| DB-03 | Operator moze zalogowac sie do panelu admin Django | `python manage.py createsuperuser` after migrations; admin already at `/admin/` |
| SSL-01 | Strona dostepna wylacznie przez HTTPS z certyfikatem Let's Encrypt | `devil ssl www add IP le le DOMAIN` generates cert; `devil www options DOMAIN sslonly on` forces HTTPS |
| SSL-02 | Wszystkie zadania HTTP sa automatycznie przekierowywane na HTTPS | `sslonly on` handles server-level redirect; `SECURE_SSL_REDIRECT=True` as Django fallback |
| SSL-03 | Formularze POST dzialaja poprawnie pod HTTPS -- CSRF_TRUSTED_ORIGINS skonfigurowane | `CSRF_TRUSTED_ORIGINS=https://kuchennakomitywa.pl` in .env |
| SSL-04 | Pliki cookie sesji i CSRF sa zabezpieczone flagami Secure i HttpOnly | `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True` in .env; HttpOnly is Django default for session cookies |
| SSL-05 | Cron job pinguje strone co 12h aby zapobiec auto-shutdown | `crontab -e` with curl ping every 12h on MyDevil |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Stack**: Django 5.2 + Django templates, no SPA
- **Single settings file**: `backend/settings.py` with `django-environ` for env var parsing
- **Code style**: Double quotes for all new string literals
- **Database**: Currently SQLite3, target PostgreSQL (locked decision from STATE.md)
- **Hosting**: MyDevil.net shared hosting with Passenger WSGI
- **psycopg[binary] >=3.3**: Locked decision from STATE.md (not psycopg2)
- **No data migration from SQLite**: Fresh database, documented as Out of Scope

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| psycopg[binary] | >=3.3,<4 | PostgreSQL adapter for Python | Django 5.2 preferred adapter; binary avoids libpq build deps on shared hosting |
| django-environ | (already installed) | DATABASE_URL parsing | Already in use via `env.db()` in settings.py |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| psycopg-binary | 3.3.3 | Pre-compiled C extension for psycopg | Always -- installed automatically as dependency of `psycopg[binary]` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| psycopg[binary] | psycopg2-binary | Legacy; Django 5.2 prefers psycopg3; psycopg2 will eventually lose Django support |
| psycopg[binary] | psycopg[c] | Requires libpq-dev at build time -- unavailable on shared hosting |

**Installation (add to requirements.txt):**
```
psycopg[binary]>=3.3,<4
```

**Version verification:**
- psycopg: 3.3.3 (latest, verified via pip index 2026-04-10)
- psycopg-binary: 3.3.3 (latest, verified via pip index 2026-04-10)

## Architecture Patterns

### Current State (already in place from Phase 7)

The settings.py is already configured for PostgreSQL switchover:

```python
# settings.py line 102-104
DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3"),
}
```

Security settings are already env-driven with safe defaults (lines 248-254):

```python
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
```

The `.env.example` has these values commented out, ready for Phase 8 activation.

### Pattern: MyDevil PostgreSQL Connection String

```
DATABASE_URL=postgres://USERNAME:PASSWORD@pgsqlX.mydevil.net:5432/DB_NAME
```

Where:
- USERNAME = database name (auto-created to match DB name on MyDevil)
- pgsqlX = matches your server number (e.g., pgsql5.mydevil.net for s5.mydevil.net)
- DB_NAME = the database name you create

### Pattern: MyDevil SSL Setup Sequence

The correct order is critical:
1. DNS A record must point to MyDevil IP (prerequisite)
2. `devil ssl www add IP le le DOMAIN` -- generates Let's Encrypt cert
3. `devil www options DOMAIN sslonly on` -- forces all HTTP to HTTPS
4. Update production `.env` with security settings
5. Restart app: `devil www restart DOMAIN`

### Pattern: Production .env Security Block

```bash
# Uncomment and activate AFTER HTTPS is confirmed working:
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
CSRF_TRUSTED_ORIGINS=https://kuchennakomitywa.pl,https://www.kuchennakomitywa.pl
```

### Anti-Patterns to Avoid
- **Enabling HSTS before confirming SSL works:** Start with `SECURE_HSTS_SECONDS=3600` (1 hour) for testing. Once confirmed, increase to `31536000` (1 year). HSTS is cached by browsers and cannot be easily undone.
- **Enabling SECURE_SSL_REDIRECT when sslonly is on:** MyDevil's `sslonly on` handles redirect at Apache/Nginx level. Django's `SECURE_SSL_REDIRECT` is a safety net but may cause redirect loops if the proxy header is misconfigured. The `SECURE_PROXY_SSL_HEADER` is already set correctly in settings.py.
- **Running createsuperuser non-interactively without env vars:** Use `DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD` env vars with `--noinput` flag for scripted setup.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTPS redirect | Custom Django middleware | `devil www options DOMAIN sslonly on` | Server-level redirect is faster and more reliable |
| SSL certificate | Manual certificate generation | `devil ssl www add IP le le DOMAIN` | MyDevil auto-renews Let's Encrypt certs |
| Database URL parsing | Manual DB config dict | `env.db("DATABASE_URL")` | Already in place; handles all URL formats |
| Keep-alive pinger | Custom management command | `curl -s` in crontab | Simplest possible solution |

## Common Pitfalls

### Pitfall 1: HSTS Lock-in
**What goes wrong:** Setting `SECURE_HSTS_SECONDS=31536000` immediately, then needing to debug HTTP issues
**Why it happens:** Browsers cache HSTS headers and refuse HTTP for the entire duration
**How to avoid:** Start with `SECURE_HSTS_SECONDS=3600` (1 hour), test thoroughly, then increase
**Warning signs:** Cannot access site via HTTP even after removing HSTS setting (browser cache)

### Pitfall 2: CSRF_TRUSTED_ORIGINS Missing or Wrong
**What goes wrong:** All POST forms return 403 Forbidden after enabling HTTPS
**Why it happens:** Django 4.0+ requires explicit `CSRF_TRUSTED_ORIGINS` with full scheme (`https://`)
**How to avoid:** Set `CSRF_TRUSTED_ORIGINS=https://kuchennakomitywa.pl,https://www.kuchennakomitywa.pl` before testing forms
**Warning signs:** Login form, checkout, newsletter signup all fail with CSRF errors

### Pitfall 3: psycopg vs psycopg-binary Confusion
**What goes wrong:** `pip install psycopg` without `[binary]` extra fails on shared hosting (no libpq-dev)
**Why it happens:** Plain `psycopg` tries to build C extension from source
**How to avoid:** Always use `psycopg[binary]` which pulls in pre-compiled `psycopg-binary`
**Warning signs:** Build errors mentioning `pg_config` or `libpq` during pip install

### Pitfall 4: DATABASE_URL Encoding Special Characters
**What goes wrong:** Database password with `@`, `/`, or `%` breaks URL parsing
**Why it happens:** These characters have special meaning in URLs
**How to avoid:** Use only alphanumeric + simple special characters in the password, or URL-encode with `%40` for `@`, etc.
**Warning signs:** Django can't connect to database, "no such database" errors

### Pitfall 5: IPv6 AAAA Record Blocks Let's Encrypt
**What goes wrong:** Let's Encrypt certificate generation fails
**Why it happens:** If domain has AAAA DNS record, Let's Encrypt tries IPv6 which MyDevil doesn't support
**How to avoid:** Remove any AAAA DNS records for the domain before certificate generation
**Warning signs:** `devil ssl www add` command fails with validation error

### Pitfall 6: Redirect Loop with SECURE_SSL_REDIRECT
**What goes wrong:** Infinite redirect loop (301 -> 301 -> ...)
**Why it happens:** Both MyDevil `sslonly` AND Django `SECURE_SSL_REDIRECT` both try to redirect; if `SECURE_PROXY_SSL_HEADER` doesn't detect the proxied HTTPS correctly, Django thinks connection is always HTTP
**How to avoid:** `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` is already set in settings.py. If redirect loop occurs, set `SECURE_SSL_REDIRECT=False` since `sslonly on` already handles it at server level
**Warning signs:** ERR_TOO_MANY_REDIRECTS in browser

## Code Examples

### Adding psycopg to requirements.txt
```
# Add this line to requirements.txt:
psycopg[binary]>=3.3,<4
```

### MyDevil PostgreSQL Setup Commands (SSH)
```bash
# Source: https://pomoc.mydevil.net/PostgreSQL/

# Create database (auto-creates user with same name)
devil pgsql db add komitywa

# Set/change password
devil pgsql passwd komitywa

# List databases to verify
devil pgsql list
```

### MyDevil SSL Setup Commands (SSH)
```bash
# Source: https://pomoc.mydevil.net/SSL/

# Get your IP address
devil www list

# Generate Let's Encrypt certificate
devil ssl www add YOUR_IP le le kuchennakomitywa.pl

# Force HTTPS for the domain
devil www options kuchennakomitywa.pl sslonly on

# Verify certificate is installed
devil ssl www list
```

### Cron Job for Keep-Alive Ping (SSH)
```bash
# Source: https://pomoc.mydevil.net/Cron/

# Edit crontab
crontab -e

# Add this line (every 12 hours at minute 0):
0 */12 * * * /usr/local/bin/curl -s https://kuchennakomitywa.pl > /dev/null 2>&1
```

### Superuser Creation on Production (SSH)
```bash
# Interactive:
cd ~/domains/kuchennakomitywa.pl
source ~/.virtualenvs/komitywa/bin/activate
python manage.py createsuperuser

# Non-interactive (for scripting):
DJANGO_SUPERUSER_EMAIL=admin@kuchennakomitywa.pl \
DJANGO_SUPERUSER_PASSWORD=secure-password-here \
python manage.py createsuperuser --noinput
```

### Production .env Changes for Phase 8
```bash
# Uncomment and set DATABASE_URL:
DATABASE_URL=postgres://komitywa:PASSWORD@pgsqlX.mydevil.net:5432/komitywa

# Uncomment security settings AFTER HTTPS works:
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=3600
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=False
CSRF_TRUSTED_ORIGINS=https://kuchennakomitywa.pl,https://www.kuchennakomitywa.pl
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| psycopg2/psycopg2-binary | psycopg[binary] (psycopg3) | Django 4.2+ | Django 5.2 prefers psycopg3; native async support, connection pooling |
| Manual DATABASES dict | `env.db("DATABASE_URL")` | django-environ established pattern | Already in place in this project |
| Manual .htaccess for HTTPS | `devil www options DOMAIN sslonly on` | MyDevil panel feature | Cleaner than .htaccess rules, no risk of syntax errors |

## Open Questions

1. **MyDevil PostgreSQL server address**
   - What we know: Format is `pgsqlX.mydevil.net` where X matches server number
   - What's unclear: The exact server number -- only discoverable after SSH login
   - Recommendation: Operator determines this via `devil pgsql list` during execution

2. **MyDevil auto-shutdown behavior**
   - What we know: The requirement mentions "prevent auto-shutdown" with a 12h cron ping
   - What's unclear: Whether MyDevil actually shuts down idle Passenger processes after 24h (not documented publicly)
   - Recommendation: Implement the cron ping regardless -- it's cheap insurance and part of success criteria

3. **www vs non-www domain**
   - What we know: CSRF_TRUSTED_ORIGINS should include both `https://kuchennakomitywa.pl` and `https://www.kuchennakomitywa.pl`
   - What's unclear: Whether `www.kuchennakomitywa.pl` is configured as a separate site or redirect on MyDevil
   - Recommendation: Include both in CSRF_TRUSTED_ORIGINS; SSL cert may need to cover both or just the canonical domain

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| MyDevil SSH access | All server commands | Assumed (Phase 7 done) | -- | None -- blocking |
| MyDevil PostgreSQL | DB-01, DB-02, DB-03 | Assumed (MyDevil feature) | PostgreSQL 14+ | None -- blocking |
| MyDevil Let's Encrypt | SSL-01, SSL-02 | Assumed (MyDevil feature) | -- | None -- blocking |
| MyDevil devil CLI | All server operations | Assumed (Phase 7 done) | -- | DevilWEB panel |
| crontab | SSL-05 | Assumed (standard on MyDevil) | -- | DevilWEB panel cron UI |
| curl | SSL-05 (keep-alive) | Standard on MyDevil | -- | wget |
| DNS A record for domain | SSL-01 | Assumed (Phase 7 done) | -- | None -- blocking |

**Missing dependencies with no fallback:** None (all assumed available from Phase 7 completion)

**Note:** All server-side dependencies are on MyDevil.net and were validated during Phase 7. The only local code change is adding `psycopg[binary]` to requirements.txt.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Django TestCase (built-in) |
| Config file | None (uses manage.py defaults) |
| Quick run command | `python manage.py test` |
| Full suite command | `python manage.py test --verbosity=2` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DB-01 | App uses PostgreSQL | manual-only | SSH: verify DATABASE_URL in .env points to postgres | N/A -- server config |
| DB-02 | Migrations run on PostgreSQL | manual-only | SSH: `python manage.py migrate --noinput` exits 0 | N/A -- server operation |
| DB-03 | Admin login works | manual-only | Browser: navigate to /admin/ and log in | N/A -- manual verification |
| SSL-01 | HTTPS with valid cert | manual-only | `curl -I https://kuchennakomitywa.pl` shows 200 | N/A -- server config |
| SSL-02 | HTTP redirects to HTTPS | manual-only | `curl -I http://kuchennakomitywa.pl` shows 301 to https | N/A -- server config |
| SSL-03 | POST forms work under HTTPS | manual-only | Browser: test login form, newsletter signup | N/A -- manual verification |
| SSL-04 | Secure cookie flags | smoke | `curl -I https://kuchennakomitywa.pl/admin/login/` and check Set-Cookie headers | N/A -- server config |
| SSL-05 | Cron job exists | manual-only | SSH: `crontab -l` shows curl ping entry | N/A -- server config |

### Sampling Rate
- **Per task commit:** `python manage.py test` (local -- ensure no regressions from requirements.txt change)
- **Per wave merge:** Full test suite + `python manage.py check --deploy` locally
- **Phase gate:** All manual server verifications completed

### Wave 0 Gaps
None -- this phase is primarily server configuration. The only code change (adding psycopg to requirements.txt) is verified by existing test suite passing. All requirements are verified through server-side manual checks.

## Sources

### Primary (HIGH confidence)
- [MyDevil PostgreSQL docs](https://pomoc.mydevil.net/PostgreSQL/) - database creation commands, connection format
- [MyDevil SSL docs](https://pomoc.mydevil.net/SSL/) - Let's Encrypt setup, devil ssl commands
- [MyDevil Cron docs](https://pomoc.mydevil.net/Cron/) - crontab syntax, PATH requirements
- [MyDevil .htaccess docs](https://pomoc.mydevil.net/htaccess/) - HTTPS redirect rules (backup method)
- [MyDevil Strona WWW docs](https://pomoc.mydevil.net/Strona_WWW/) - `devil www options DOMAIN sslonly on|off`
- Project codebase: `backend/settings.py` - verified all env var patterns already in place
- pip index: psycopg 3.3.3, psycopg-binary 3.3.3 (verified 2026-04-10)

### Secondary (MEDIUM confidence)
- [Django Forum: psycopg2 vs psycopg3 in Django 5.2](https://forum.djangoproject.com/t/is-psycopg2-still-supported-in-django-5-2/41032) - Django 5.2 prefers psycopg3
- [django-environ DATABASE_URL docs](https://django-environ.readthedocs.io/en/latest/types.html) - URL format for PostgreSQL

### Tertiary (LOW confidence)
- MyDevil auto-shutdown behavior: not documented publicly; the 12h cron ping is specified in requirements but the underlying auto-shutdown mechanism is unverified

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - psycopg3 version verified via pip index, django-environ already in project
- Architecture: HIGH - all settings patterns already in place from Phase 7, just need env var activation
- Pitfalls: HIGH - well-documented Django/SSL issues, MyDevil-specific IPv6 issue from official docs
- MyDevil commands: HIGH - sourced directly from official MyDevil documentation

**Research date:** 2026-04-10
**Valid until:** 2026-05-10 (stable infrastructure, unlikely to change)
