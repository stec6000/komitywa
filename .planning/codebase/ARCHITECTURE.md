# Architecture

**Analysis Date:** 2026-03-30

## Pattern Overview

**Overall:** Django REST API backend with email-based authentication

**Key Characteristics:**
- API-only Django project (no server-rendered HTML views) designed to serve a frontend client
- Email-only authentication (no username field) via django-allauth + dj-rest-auth
- Custom User model extending `AbstractUser` with email as the primary identifier
- Single Django app (`accounts`) handling all user/auth concerns
- SQLite database (development configuration)

## Layers

**Project Configuration Layer:**
- Purpose: Django project settings, URL routing, WSGI/ASGI entry points
- Location: `backend/`
- Contains: `settings.py`, `urls.py`, `wsgi.py`, `asgi.py`
- Depends on: Django framework, installed apps
- Used by: All apps and the Django runtime

**Accounts App Layer:**
- Purpose: User model, authentication serializers, admin interface, email templates
- Location: `accounts/`
- Contains: Models, serializers, forms, admin configuration, email templates
- Depends on: `django.contrib.auth`, `allauth`, `dj_rest_auth`, `rest_framework`
- Used by: API endpoints via dj-rest-auth URL routing

**Third-Party Auth Layer (dj-rest-auth + allauth):**
- Purpose: Provides REST API endpoints for registration, login, logout, password reset
- Location: Installed packages, configured in `backend/settings.py` and `backend/urls.py`
- Contains: Views, URL patterns, adapters for auth flows
- Depends on: `accounts.serializers` (custom serializers), `accounts.forms` (custom signup form)
- Used by: Frontend clients via `api/auth/` endpoints

**Admin Layer:**
- Purpose: Django admin interface for managing users and email addresses
- Location: `accounts/admin.py`
- Contains: Custom `UserAdmin` with activate/deactivate actions, custom `EmailAddressAdmin` with verify/mark-primary actions
- Depends on: `accounts.forms.AdminUserCreationForm`, `accounts.forms.AdminUserChangeForm`, `allauth.account.models.EmailAddress`
- Used by: Staff users via `/admin/`

## Data Flow

**User Registration:**

1. Client POSTs to `api/auth/registration/` with `{email, password1, password2}`
2. `dj_rest_auth.registration` routes to its registration view
3. `accounts.serializers.EmailOnlyRegisterSerializer` validates: email uniqueness (checks both `EmailAddress` and `User` tables), password strength via allauth adapter, password match
4. Serializer `.save(request)` creates user via allauth adapter (`adapter.new_user()` then `adapter.save_user()`)
5. `setup_user_email()` creates an `EmailAddress` record and triggers email verification flow
6. Returns 201/204 with auth token key

**User Login:**

1. Client POSTs to `api/auth/login/` with `{email, password}`
2. `dj_rest_auth` routes to its login view
3. `accounts.serializers.EmailOnlyLoginSerializer` (extends `LoginSerializer`, removes `username` field) validates credentials
4. Returns 200 with `{key: "<token>"}` (Token authentication via `rest_framework.authtoken`)

**Password Reset:**

1. Client POSTs to `api/auth/password/reset/` with `{email}`
2. allauth sends email using template at `accounts/templates/account/email/password_reset_key_message.txt`
3. Client receives link with reset key, POSTs to `api/auth/password/reset/confirm/` with `{uid, token, new_password1, new_password2}`

**Email Confirmation:**

1. After registration, allauth sends confirmation email using `accounts/templates/account/email/email_confirmation_message.txt`
2. User clicks link containing confirmation key
3. `EmailAddress` record is marked as verified

**State Management:**
- Authentication state: Token-based via `rest_framework.authtoken` (tokens stored in database)
- Session-based authentication also enabled (`SessionAuthentication` in `REST_FRAMEWORK` settings)
- No client-side state management (API-only backend)

## Key Abstractions

**Custom User Model:**
- Purpose: Email-only user identity (no username)
- Location: `accounts/models.py`
- Pattern: Extends `AbstractUser`, sets `username = None`, overrides `USERNAME_FIELD = "email"`, provides custom `UserManager` with `create_user()` and `create_superuser()` methods

**Custom Serializers:**
- Purpose: Adapt dj-rest-auth's default serializers to email-only flow
- Location: `accounts/serializers.py`
- Pattern: `EmailOnlyRegisterSerializer` is a standalone `serializers.Serializer` (not ModelSerializer) that manually validates and creates users via allauth adapter. `EmailOnlyLoginSerializer` extends `LoginSerializer` and removes the `username` field.

**Custom Forms:**
- Purpose: Email-only forms for allauth signup and Django admin
- Location: `accounts/forms.py`
- Pattern: `EmailOnlySignupForm` extends allauth `SignupForm` and removes username. `AdminUserCreationForm` and `AdminUserChangeForm` extend Django's built-in forms scoped to email-only fields.

## Entry Points

**API Endpoints:**
- Location: `backend/urls.py`
- `api/auth/` - dj-rest-auth endpoints (login, logout, password reset, password change, user details)
- `api/auth/registration/` - dj-rest-auth registration endpoints
- `api/schema/` - OpenAPI schema (drf-spectacular)
- `api/docs/` - Swagger UI (drf-spectacular)
- `admin/` - Django admin interface

**CLI Entry Point:**
- Location: `manage.py`
- Standard Django management commands

**WSGI/ASGI:**
- WSGI: `backend/wsgi.py`
- ASGI: `backend/asgi.py`

## Error Handling

**Strategy:** Django REST Framework standard error responses

**Patterns:**
- Validation errors in serializers raise `serializers.ValidationError` with field-specific messages, returned as 400 responses with JSON error details
- Django `ValidationError` caught and re-raised as DRF `ValidationError` in `EmailOnlyRegisterSerializer.save()` for password validation
- allauth adapter handles email/password validation rules
- No custom exception handler configured (uses DRF defaults)

## Cross-Cutting Concerns

**Authentication:** Dual authentication backends: Django's `ModelBackend` + allauth's `AuthenticationBackend`. REST API uses `SessionAuthentication` and `BasicAuthentication` (token auth available via `rest_framework.authtoken` app).

**CORS:** Configured via `django-cors-headers`. Defaults to `localhost:3000` and `127.0.0.1:3000`. Overridable via `CORS_ALLOWED_ORIGINS` environment variable (comma-separated).

**API Documentation:** Auto-generated OpenAPI 3 schema via `drf-spectacular` at `api/schema/`, with Swagger UI at `api/docs/`.

**Internationalization:** Email templates are in Polish. Django i18n is enabled (`USE_I18N = True`), locale set to `en-us`.

**Logging:** No custom logging configuration. Uses Django defaults.

**Validation:** Django's four built-in password validators are active (similarity, minimum length, common password, numeric). Email uniqueness enforced at both model level (`unique=True`) and serializer level.

---

*Architecture analysis: 2026-03-30*
