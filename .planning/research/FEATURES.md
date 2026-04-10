# Feature Landscape: v1.1 Production Deployment

**Domain:** Django production deployment on MyDevil.net shared hosting
**Project:** Kuchenna Komitywa
**Researched:** 2026-04-10

## Table Stakes

Features absolutely required for the site to be live and functional. Missing any of these means the site cannot go to production.

### Server Configuration

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Passenger WSGI setup | MyDevil runs Python apps via Phusion Passenger; no alternative | Low | `passenger_wsgi.py` in `public_python/` with `DJANGO_SETTINGS_MODULE=backend.settings` |
| Python virtualenv on server | Isolate dependencies; MyDevil requires explicit venv path for Python site type | Low | Create venv, `pip install -r requirements.txt` inside it |
| Production `.env` file | `DEBUG=False`, unique `SECRET_KEY`, proper `ALLOWED_HOSTS`; already uses django-environ | Low | Set correct values on server; never commit `.env` |
| `collectstatic` execution | Static files must be collected to `STATIC_ROOT` for production serving | Low | `python manage.py collectstatic`; STATIC_ROOT already set to `public/static` |
| Application restart procedure | MyDevil does not auto-restart on code changes | Low | `devil www restart DOMENA` after each deployment |

### Database Migration (SQLite to PostgreSQL)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| PostgreSQL database creation on MyDevil | SQLite unsuitable for production (concurrent writes fail, no remote access) | Low | `devil pgsql db add NAZWA_BAZY` on MyDevil shell |
| psycopg installation | Django PostgreSQL adapter; required dependency | Low | Use `psycopg[binary]` (psycopg3) -- Django 5.2 supports it natively; psycopg2 is legacy |
| Database URL configuration via env | Connection string must not be hardcoded | Low | `DATABASES["default"] = env.db("DATABASE_URL")` -- django-environ supports this natively |
| Django migrations on PostgreSQL | Schema must be created on fresh PostgreSQL database | Low | `python manage.py migrate` on server after database creation |
| Initial data seeding | Admin account, site configuration, initial content | Medium | `createsuperuser` + manual content entry via admin; or `dumpdata`/`loaddata` if migrating dev data |

### Email Configuration (Brevo SMTP)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| SMTP backend switch | Console backend is dev-only; emails must actually send in production | Low | `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` in prod `.env` |
| Brevo SMTP credentials | Transactional emails: order confirmations, ebook PDF delivery, newsletter, auth flows | Low | `EMAIL_HOST=smtp-relay.brevo.com`, port 587, TLS; use SMTP key (not API key) |
| Sender domain verification | Brevo requires SPF/DKIM DNS records for deliverability | Medium | Add DNS records on `kuchennakomitywa.pl`; without this, emails land in spam |
| Email flow verification | All email types must work: registration, password reset, order confirmation, ebook delivery, newsletter | Medium | Manual end-to-end testing of each email flow after deployment |

### SSL / HTTPS

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Let's Encrypt certificate | HTTPS mandatory for payments, user accounts, and modern browser trust | Low | `devil ssl www add IP le le DOMENA` or via DevilWEB panel; auto-renews |
| Django HTTPS security settings | Cookies, CSRF, session must enforce HTTPS | Low | `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS` |
| Remove AAAA DNS record if present | MyDevil does not support IPv6 for Let's Encrypt validation; cert generation fails with AAAA | Low | Check and remove AAAA record from DNS before generating certificate |

### Static and Media Files

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Static files served from `public/static` | CSS, JS, images must load; MyDevil serves `public/` directory via web server | Low | Already configured: `STATIC_ROOT = BASE_DIR / "public" / "static"` |
| Media files served from `public/media` | Recipe photos, product images, ebook covers must display | Low | Already configured: `MEDIA_ROOT = BASE_DIR / "public" / "media"` |
| WhiteNoise middleware | Serves static files through Django with compression and caching headers; fallback when web server config is limited | Low | `whitenoise` package; insert middleware after `SecurityMiddleware` |

### Przelewy24 (Sandbox on Production)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| P24 sandbox credentials in prod `.env` | Payment flow must work end-to-end in sandbox mode | Low | Copy existing sandbox credentials to production `.env` |
| P24 webhook URL update | Webhook callback must point to production domain, not localhost | Low | Update P24 sandbox panel with `https://DOMENA/shop/p24/webhook/` URL |
| HTTPS for P24 callbacks | P24 requires HTTPS for webhook notifications | Low | Depends on SSL certificate being active first |

### Domain and DNS

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Domain DNS pointing to MyDevil | Site must be accessible at the production domain | Low | A record pointing to MyDevil server IP address |
| `ALLOWED_HOSTS` in production `.env` | Django rejects requests for unknown hosts when `DEBUG=False` | Low | Domain name + `www` variant in env |
| `CSRF_TRUSTED_ORIGINS` setting | Django 4+ requires explicit trusted origins for HTTPS POST requests (forms, checkout) | Low | `["https://kuchennakomitywa.pl", "https://www.kuchennakomitywa.pl"]` |

## Differentiators

Not required for go-live but improve reliability, maintainability, or developer experience. Low effort, high value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| `manage.py check --deploy` audit | Catches security misconfigurations before go-live; free safety net | Low | Run against production settings; fix all warnings |
| `.env.example` file | Documents all required env vars; prevents forgotten config during future deployments | Low | Copy of `.env` structure without secret values |
| Custom 404/500 error pages | Professional appearance when errors occur; Django default pages are ugly with `DEBUG=False` | Low | `templates/404.html` and `templates/500.html` with site branding |
| Deployment shell script | Repeatable deployments; avoids forgetting steps (pull, install, migrate, collectstatic, restart) | Low | Single `deploy.sh` script on server |
| Error logging configuration | Django `LOGGING` dict writing to file; MyDevil stores errors in `domains/DOMENA/logs/error.log` | Low | Configure Django logging to write to MyDevil's log directory |
| Database backup via cron | Recover from data loss; `pg_dump` scheduled via MyDevil cron | Low | Set up within first week of going live |
| Sentry error tracking | Proactive error notification; see production errors before users report them | Medium | `sentry-sdk[django]`; free tier sufficient for low-traffic site |
| `SERVER_EMAIL` setting | Django admin receives error notification emails from the correct address | Low | Set to a valid email address in production settings |

## Anti-Features

Features to explicitly NOT build for this milestone. Each adds complexity without proportional value.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| CI/CD pipeline | Overkill for single-developer project on shared hosting | Manual deployment via SSH + `deploy.sh` script |
| Docker containerization | MyDevil is shared hosting with no Docker support | Use MyDevil's native Python/Passenger setup |
| Nginx/Apache configuration | MyDevil manages the web server; cannot configure it directly | Passenger WSGI + WhiteNoise handles everything needed |
| Redis/Memcached caching | Premature optimization; site traffic will be low initially | Django default caching; add later if performance requires it |
| Celery task queue | No background task needs; email sending is synchronous and fast enough | Send emails synchronously; revisit only if newsletter campaigns grow large |
| Staging environment | Single shared hosting account; one domain is sufficient | Test locally with production-like settings, deploy to production |
| CDN for static files | Low-traffic site; WhiteNoise compression is sufficient | Add CloudFlare later if performance becomes an issue |
| Automated cloud backups | Manual `pg_dump` is sufficient at this scale | Simple cron job for local backups |
| Production P24 credentials | Client has not provided production merchant credentials yet | Keep sandbox; switch when credentials arrive (env var change only) |
| Split settings files (base/dev/prod) | django-environ already handles env-specific config via `.env` per environment | Single `settings.py` + different `.env` files |
| Gunicorn/uWSGI | MyDevil uses Passenger; cannot swap WSGI servers on shared hosting | Passenger is the only option and works fine |
| Database connection pooling | Low traffic; connection overhead is negligible | Revisit if performance monitoring shows connection issues |

## Feature Dependencies

```
Domain DNS ──→ SSL Certificate ──→ HTTPS Security Settings
                                ──→ P24 Webhook URL Update
                                ──→ CSRF Trusted Origins

PostgreSQL Creation ──→ Database URL Config ──→ Django Migrations ──→ Data Seeding
                                                                   ──→ Application Start

Virtualenv Setup ──→ pip install requirements ──→ passenger_wsgi.py ──→ Application Start
                                               ──→ collectstatic

Brevo Account ──→ Domain Verification (SPF/DKIM DNS) ──→ SMTP Credentials in .env
                                                       ──→ Email Flow Testing

SSL Certificate ──→ SECURE_SSL_REDIRECT + cookie security settings
SSL Certificate ──→ P24 webhook HTTPS requirement
```

## Critical Path (Execution Order)

This order matters because of hard dependencies:

1. **DNS setup** -- domain must point to MyDevil before anything else
2. **Virtualenv + dependencies** -- nothing runs without Python packages
3. **PostgreSQL setup + migrations** -- app cannot start without database
4. **Production `.env` + passenger_wsgi.py** -- app must boot
5. **SSL certificate** -- must be active before enabling HTTPS settings
6. **HTTPS security settings + CSRF trusted origins** -- enable after SSL confirmed
7. **collectstatic** -- site looks broken without CSS/JS
8. **Email configuration (Brevo SMTP + domain verification)** -- transactional emails must work
9. **P24 webhook URL update** -- payment flow needs correct callback URL
10. **End-to-end verification** -- test all flows: browse, register, order, pay, receive email

## MVP Recommendation

### Must Ship (all Table Stakes)

Everything in the Table Stakes section is required. The site cannot function without any single item.

1. Server: Passenger WSGI + virtualenv + production `.env`
2. Database: PostgreSQL created, migrated, initial data seeded
3. SSL: Let's Encrypt certificate + HTTPS security settings
4. Static/Media: `collectstatic` + WhiteNoise
5. Email: Brevo SMTP configured, domain verified, all flows tested
6. P24: Sandbox credentials on production, webhook URL updated
7. Domain: DNS configured, `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` set

### Include from Differentiators (low effort, high value)

These should ship with the deployment -- they take minutes and prevent real problems:

1. `manage.py check --deploy` -- free security audit, catches missed settings
2. `.env.example` -- documentation for all required env vars
3. Custom 404/500 pages -- site looks professional even when errors occur
4. `deploy.sh` script -- makes re-deployment reliable and repeatable
5. Error logging to file -- debug production issues without guessing

### Defer to Post-Launch (first week)

6. Database backup cron job -- set up once site is stable
7. Sentry error tracking -- add when there is real traffic to monitor

## Sources

- [MyDevil.net Django Documentation](https://pomoc.mydevil.net/Django/)
- [MyDevil.net PostgreSQL Documentation](https://pomoc.mydevil.net/PostgreSQL/)
- [MyDevil.net SSL Documentation](https://pomoc.mydevil.net/SSL/)
- [Django 5.2 Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [Brevo SMTP Integration Docs](https://developers.brevo.com/docs/smtp-integration)
- [Brevo SMTP Key Management](https://help.brevo.com/hc/en-us/articles/7959631848850-Create-and-manage-your-SMTP-keys)
- [WhiteNoise Django Documentation](https://whitenoise.readthedocs.io/en/stable/django.html)
- [Practical MyDevil Django Deployment Guide](https://blog.joanna-siwiec.pl/aplikacja-django-na-serwerze-mydevil/1849/)
- [psycopg3 vs psycopg2 for Django](https://dev.to/jimmyyeung/upgrade-to-django-5-with-psycopg3-4e8b)
- [Django Forum: psycopg2 support in Django 5.2](https://forum.djangoproject.com/t/is-psycopg2-still-supported-in-django-5-2/41032)
