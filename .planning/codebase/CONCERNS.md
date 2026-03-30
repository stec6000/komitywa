# Codebase Concerns

**Analysis Date:** 2026-03-30

## Security

**Hardcoded SECRET_KEY in settings:**
- Issue: `SECRET_KEY` is hardcoded as a Django-insecure key directly in source code at `backend/settings.py:24`. This key is committed to git and uses the `django-insecure-` prefix, confirming it is not production-safe.
- Files: `backend/settings.py`
- Impact: Any attacker with repo access can forge sessions, CSRF tokens, and signed data. Deploying this to production means complete authentication bypass.
- Fix approach: Read `SECRET_KEY` from an environment variable using `os.environ["SECRET_KEY"]` with no fallback. Generate a new production key with `django.core.management.utils.get_random_secret_key()`.

**DEBUG=True with no environment toggle:**
- Issue: `DEBUG = True` is hardcoded at `backend/settings.py:27` with no mechanism to disable it via environment variable.
- Files: `backend/settings.py`
- Impact: In production, DEBUG mode exposes full stack traces, settings values, and SQL queries to end users. It also serves static files inefficiently and disables some security checks.
- Fix approach: Set `DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1")`.

**ALLOWED_HOSTS limited to localhost only:**
- Issue: `ALLOWED_HOSTS` at `backend/settings.py:29` contains only `localhost` and `127.0.0.1`. There is no mechanism to configure production hostnames.
- Files: `backend/settings.py`
- Impact: The application will return 400 errors for any request with a different Host header, making deployment impossible without code changes.
- Fix approach: Read from environment variable, e.g., `ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")`.

**BasicAuthentication enabled in production REST_FRAMEWORK config:**
- Issue: `rest_framework.authentication.BasicAuthentication` is listed in `DEFAULT_AUTHENTICATION_CLASSES` at `backend/settings.py:100-102`.
- Files: `backend/settings.py`
- Impact: BasicAuth sends credentials as base64 in every request. Without HTTPS enforcement, credentials are transmitted in cleartext. It also encourages storing passwords client-side.
- Fix approach: Remove `BasicAuthentication` from the defaults. Use `TokenAuthentication` (already installed via `rest_framework.authtoken`) or JWT-based auth instead.

**No HTTPS/security headers configured:**
- Issue: Missing production security settings: `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_BROWSER_XSS_FILTER`, `SECURE_CONTENT_TYPE_NOSNIFF`.
- Files: `backend/settings.py`
- Impact: No transport-layer security enforcement. Cookies transmittable over HTTP. No HSTS protection.
- Fix approach: Add these settings gated behind a production environment check (e.g., `not DEBUG`).

**No rate limiting on authentication endpoints:**
- Issue: The registration (`api/auth/registration/`) and login (`api/auth/`) endpoints at `backend/urls.py:27-29` have no throttling configured.
- Files: `backend/urls.py`, `backend/settings.py`
- Impact: Vulnerable to brute-force login attacks and registration spam.
- Fix approach: Configure `DEFAULT_THROTTLE_CLASSES` and `DEFAULT_THROTTLE_RATES` in `REST_FRAMEWORK` settings, or add per-view throttle classes to auth endpoints.

## Tech Debt

**python-dotenv installed but never used:**
- Issue: `python-dotenv` is listed in `requirements.txt:8` but is never imported in `backend/settings.py` or anywhere else. `os.environ.get()` is used directly at line 152 for `CORS_ALLOWED_ORIGINS`, but `load_dotenv()` is never called.
- Files: `requirements.txt`, `backend/settings.py`
- Impact: `.env` files have no effect on the application. Developers may expect env vars from `.env` to load automatically, but they do not.
- Fix approach: Add `from dotenv import load_dotenv; load_dotenv()` at the top of `backend/settings.py`, then migrate all hardcoded settings (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASES`) to use `os.environ`.

**Empty views.py:**
- Issue: `accounts/views.py` contains only the default Django stub comment with no actual views.
- Files: `accounts/views.py`
- Impact: No functional impact (all auth views come from `dj_rest_auth`), but the empty file is unnecessary clutter.
- Fix approach: Either remove the file or add a comment noting views are provided by `dj_rest_auth`.

**SQLite database for all environments:**
- Issue: `DATABASES` at `backend/settings.py:89-94` is hardcoded to SQLite with no option to switch to PostgreSQL or another production database.
- Files: `backend/settings.py`
- Impact: SQLite does not support concurrent writes, has no network access, and lacks features needed in production (e.g., full-text search, JSON fields performance). Migrations developed against SQLite may not work on PostgreSQL.
- Fix approach: Use `dj-database-url` or environment-variable-based configuration to allow PostgreSQL in production while keeping SQLite for local development.

**README.md is empty:**
- Issue: `README.md` exists but contains no content (only 1 empty line).
- Files: `README.md`
- Impact: New developers have no onboarding documentation, setup instructions, or project context.
- Fix approach: Add project description, setup instructions, environment variable documentation, and development workflow.

**No email backend configured for production:**
- Issue: No `EMAIL_BACKEND` setting in `backend/settings.py`. Django defaults to `smtp.EmailBackend` which will fail without SMTP configuration. The allauth email templates exist at `accounts/templates/account/email/` but no sending infrastructure is configured.
- Files: `backend/settings.py`, `accounts/templates/account/email/`
- Impact: Email verification and password reset will fail silently or raise connection errors in any environment.
- Fix approach: Configure `EMAIL_BACKEND` with a service (e.g., SendGrid, SES, Mailgun) for production and `console.EmailBackend` for development.

**No ACCOUNT_EMAIL_VERIFICATION setting:**
- Issue: `backend/settings.py` does not set `ACCOUNT_EMAIL_VERIFICATION`. The allauth default is `"optional"`, meaning users can register without verifying email.
- Files: `backend/settings.py`
- Impact: Unverified emails in the system. For an app that uses email as the sole login identifier, this is a data integrity risk.
- Fix approach: Explicitly set `ACCOUNT_EMAIL_VERIFICATION = "mandatory"` once email sending is configured.

## Missing Infrastructure

**No CI/CD pipeline:**
- Issue: No `.github/workflows/`, `Jenkinsfile`, `.gitlab-ci.yml`, or any CI configuration exists.
- Impact: No automated testing, linting, or deployment. Regressions can reach production undetected.
- Fix approach: Add a GitHub Actions workflow that runs `python manage.py test`, linting, and security checks on push/PR.

**No Docker configuration:**
- Issue: No `Dockerfile`, `docker-compose.yml`, or container configuration exists.
- Impact: No reproducible development or deployment environment. "Works on my machine" risk.
- Fix approach: Add a `Dockerfile` for the Django app and a `docker-compose.yml` with Django + PostgreSQL + Redis services.

**No linting or formatting tools configured:**
- Issue: No `.flake8`, `pyproject.toml` (with ruff/black config), `setup.cfg`, or any linter configuration exists. The `.gitignore` references `.ruff_cache/` and `.mypy_cache/` suggesting intent to use these tools, but they are not installed or configured.
- Files: `.gitignore`, `requirements.txt`
- Impact: No enforced code style. Inconsistent formatting across contributors (already visible: mixed quote styles in `backend/settings.py`).
- Fix approach: Add `ruff` to requirements and create a `pyproject.toml` with ruff configuration. Add a pre-commit hook.

**No pre-commit hooks:**
- Issue: No `.pre-commit-config.yaml` exists.
- Impact: Linting, formatting, and secret detection are not enforced before commits.
- Fix approach: Add `pre-commit` with hooks for ruff, secret scanning, and trailing whitespace.

**No logging configuration:**
- Issue: No `LOGGING` dict in `backend/settings.py`. Django uses default logging which goes to console with minimal structure.
- Files: `backend/settings.py`
- Impact: No structured logs for debugging production issues. No log levels, formatters, or handlers configured.
- Fix approach: Add a `LOGGING` configuration with appropriate handlers for development (console) and production (structured JSON to stdout).

**No STATIC_ROOT or static file serving strategy:**
- Issue: `STATIC_URL` is set at `backend/settings.py:181` but `STATIC_ROOT` is not defined, and no static file serving solution (e.g., `whitenoise`) is installed.
- Files: `backend/settings.py`, `requirements.txt`
- Impact: `collectstatic` will fail. Static files (admin CSS/JS) will not be served in production.
- Fix approach: Set `STATIC_ROOT = BASE_DIR / "staticfiles"` and add `whitenoise` to middleware.

## Dependency Health

**No version pinning in requirements.txt:**
- Issue: All 8 dependencies in `requirements.txt` are unpinned (no `==` version specifiers).
- Files: `requirements.txt`
- Impact: Builds are non-reproducible. A breaking update to any dependency will silently break the application. Different developers may have different versions installed.
- Fix approach: Pin all dependencies with exact versions (`django==5.2.11`). Use `pip freeze > requirements.lock` or adopt `pip-tools` with a `requirements.in` / `requirements.txt` workflow.

**No dev/prod dependency separation:**
- Issue: Single `requirements.txt` with no distinction between production and development dependencies.
- Files: `requirements.txt`
- Impact: Test and development tools would be installed in production if any were added.
- Fix approach: Split into `requirements/base.txt`, `requirements/dev.txt`, and `requirements/prod.txt`, or use `pyproject.toml` with optional dependency groups.

**`requests` package present but unused:**
- Issue: `requests` is listed in `requirements.txt:7` but is not imported anywhere in the codebase.
- Files: `requirements.txt`
- Impact: Unnecessary dependency increases attack surface and install time.
- Fix approach: Remove `requests` from `requirements.txt` unless it is needed for planned features.

## Documentation Gaps

**No API documentation beyond auto-generated schema:**
- Issue: The only API docs are the auto-generated Swagger UI at `/api/docs/` via `drf-spectacular`. No written API documentation, usage examples, or authentication flow documentation exists.
- Files: `backend/urls.py`
- Impact: Frontend developers and API consumers have no guidance on authentication flows, error response formats, or expected request/response shapes beyond what Swagger generates.
- Fix approach: Document the authentication flow (register -> verify email -> login -> use token) in the README or a dedicated docs directory.

**No environment variable documentation:**
- Issue: The only environment variable currently read is `CORS_ALLOWED_ORIGINS` at `backend/settings.py:152`. There is no `.env.example` file documenting required/optional environment variables.
- Files: `backend/settings.py`
- Impact: Developers must read settings.py to discover configuration options.
- Fix approach: Create a `.env.example` file listing all environment variables with descriptions and example values.

## Scalability

**SQLite database:**
- Issue: SQLite at `backend/settings.py:89-94` is a single-file database with no concurrent write support.
- Files: `backend/settings.py`
- Impact: Any concurrent API traffic (e.g., multiple simultaneous registrations) will cause database lock errors. Maximum practical capacity is approximately 1 concurrent user.
- Fix approach: Migrate to PostgreSQL for anything beyond local development.

**Session-based authentication default:**
- Issue: `SessionAuthentication` is the primary auth method at `backend/settings.py:99`. Sessions are stored in the database by default.
- Files: `backend/settings.py`
- Impact: Every authenticated request requires a database read for session lookup. No horizontal scaling without shared session store. Not suitable for mobile/SPA clients that need stateless auth.
- Fix approach: Switch primary authentication to `TokenAuthentication` (already installed) or JWT. Use `TokenAuthentication` from `rest_framework.authtoken` which is already in `INSTALLED_APPS`.

## Test Coverage Gaps

**Only authentication flows tested:**
- Issue: `accounts/tests.py` contains 5 tests covering only registration and login. No tests exist for admin actions, serializer edge cases, model methods, or the custom `UserManager`.
- Files: `accounts/tests.py`
- What is not tested:
  - `UserManager.create_user()` and `create_superuser()` in `accounts/models.py`
  - Admin actions (`activate_users`, `deactivate_users`, `mark_email_verified`, `mark_email_primary`) in `accounts/admin.py`
  - `AdminUserCreationForm` and `AdminUserChangeForm` in `accounts/forms.py`
  - Password reset flow via allauth templates
  - Logout endpoint
  - Edge cases: empty email, extremely long email, unicode email
- Risk: Admin actions modifying user state and email verification have no test coverage. Regressions in these areas would go undetected.
- Priority: Medium - the tested auth flows cover the critical path, but admin and model-layer tests should be added before expanding the application.

---

*Concerns audit: 2026-03-30*
