# External Integrations

**Analysis Date:** 2026-03-30

## APIs (Exposed)

**REST API - Authentication endpoints:**
- `api/auth/` - Login, logout, password management (via `dj-rest-auth`)
  - Configured in `backend/urls.py` line 27
- `api/auth/registration/` - User registration (via `dj-rest-auth.registration`)
  - Configured in `backend/urls.py` line 29
- `admin/` - Django admin interface
  - Configured in `backend/urls.py` line 22

**API Documentation endpoints:**
- `api/schema/` - OpenAPI 3 JSON/YAML schema (via `drf-spectacular`)
  - Configured in `backend/urls.py` line 24
- `api/docs/` - Swagger UI (via `drf-spectacular`)
  - Configured in `backend/urls.py` line 25

**REST Framework Configuration** (`backend/settings.py` lines 97-103):
- Schema class: `drf_spectacular.openapi.AutoSchema`
- Authentication: Session authentication + Basic authentication
- Token authentication app installed (`rest_framework.authtoken`) but not listed in `DEFAULT_AUTHENTICATION_CLASSES`

## APIs (Consumed)

- None detected. The `requests` library is in `requirements.txt` but no outbound HTTP calls exist in application code.

## External Services

- None. No third-party service integrations (no payment, email, storage, or analytics services configured).

## Authentication & Identity

**Auth Provider:** django-allauth + dj-rest-auth (self-hosted, email-based)

**Implementation details:**
- Custom user model: `accounts.User` (defined in `accounts/models.py`)
  - Email-only authentication (no username field)
  - Custom `UserManager` in `accounts/models.py`
- `AUTH_USER_MODEL = "accounts.User"` in `backend/settings.py` line 138
- Login method: email only (`ACCOUNT_LOGIN_METHODS = {"email"}` in `backend/settings.py` line 140)
- Registration fields: email, password1, password2 (`backend/settings.py` lines 142-146)

**Authentication backends** (`backend/settings.py` lines 106-109):
- `django.contrib.auth.backends.ModelBackend`
- `allauth.account.auth_backends.AuthenticationBackend`

**Custom serializers** (`accounts/serializers.py`):
- `EmailOnlyRegisterSerializer` - Registration without username
- `EmailOnlyLoginSerializer` - Login without username

**Custom forms** (`accounts/forms.py`):
- `EmailOnlySignupForm` - Allauth signup form without username
- `AdminUserCreationForm` - Admin panel user creation
- `AdminUserChangeForm` - Admin panel user editing

**Social auth:** `allauth.socialaccount` is installed but no social providers are configured.

## Database

**Type:** SQLite3
- Engine: `django.db.backends.sqlite3`
- File: `db.sqlite3` (project root)
- Configured in `backend/settings.py` lines 89-94
- No ORM beyond Django's built-in ORM

## CORS

**Package:** django-cors-headers
- Middleware: `corsheaders.middleware.CorsMiddleware` (positioned second in middleware stack)
- Allowed origins configurable via `CORS_ALLOWED_ORIGINS` env var
- Defaults: `http://localhost:3000`, `http://127.0.0.1:3000`
- Configured in `backend/settings.py` lines 152-163

## Caching

- None configured (Django default: local memory cache)

## Message Queues

- None

## File Storage

- None (Django default: local filesystem for static/media)

## Monitoring & Observability

**Error Tracking:** None
**Logging:** None configured (Django defaults)

## Email

- Not configured. django-allauth may require email for verification, but no `EMAIL_BACKEND` setting is present (Django defaults to SMTP on localhost:25).

## CI/CD & Deployment

- No CI/CD configuration detected
- No deployment scripts or platform config files

## Webhooks & Callbacks

**Incoming:** None
**Outgoing:** None

---

*Integration audit: 2026-03-30*
