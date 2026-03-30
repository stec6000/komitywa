<!-- GSD:project-start source:PROJECT.md -->
## Project

**Kuchenna Komitywa**

Strona informacyjna i sklep online dla firmy Kuchenna Komitywa — wegańskiej/roślinnej kuchni. Serwis łączy blog z przepisami, sprzedaż ebooków (PDF), sprzedaż gotowych produktów (dania w słoiku, ciasta z odbiorem osobistym) oraz newsletter. Całość po polsku, na Django z klasycznymi szablonami HTML.

**Core Value:** Klienci mogą przeglądać przepisy, kupować ebooki i zamawiać gotowe wegańskie produkty z odbiorem osobistym — w jednym miejscu.

### Constraints

- **Stack**: Django 5.2 + Django templates (bez SPA)
- **Płatności**: Przelewy24
- **Język**: Tylko polski
- **Dostawa ebooków**: Wyłącznie na email (PDF)
- **Dostawa produktów**: Tylko odbiór osobisty
- **Identyfikacja wizualna**: Do stworzenia od zera
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.x - All backend code (Django project)
## Runtime
- Python 3.x (exact version not pinned; no `.python-version` or `runtime.txt` present)
- Django settings module: `backend.settings`
- pip
- Lockfile: missing (no `requirements.lock`, `Pipfile.lock`, or `poetry.lock`; only unpinned `requirements.txt`)
## Frameworks
- Django 5.2.x - Web framework (version from `backend/settings.py` generated comment: "using Django 5.2.11")
- Django REST Framework (djangorestframework) - REST API layer, configured in `backend/settings.py` under `REST_FRAMEWORK`
- django-allauth - Authentication and account management
- dj-rest-auth - REST API authentication endpoints (login, logout, registration)
- drf-spectacular - OpenAPI 3 schema generation and Swagger UI
- `manage.py` - Standard Django management CLI (entry point at `manage.py`)
## Key Dependencies
| Package | Purpose |
|---------|---------|
| `django` | Core web framework (5.2.x) |
| `djangorestframework` | REST API framework |
| `django-allauth` | Account management, email-based auth |
| `dj-rest-auth` | REST endpoints for auth (login/register/logout) |
| `drf-spectacular` | OpenAPI schema + Swagger UI |
| `django-cors-headers` | CORS handling for cross-origin requests |
| `requests` | HTTP client library (no current usage detected in app code) |
| `python-dotenv` | `.env` file loading (no current usage detected in app code) |
## Configuration
- `CORS_ALLOWED_ORIGINS` - Comma-separated allowed origins (defaults to `http://localhost:3000`, `http://127.0.0.1:3000`)
- `DJANGO_SETTINGS_MODULE` - Set to `backend.settings` in `manage.py`
- `backend/settings.py` - All Django settings (database, auth, REST framework, CORS, installed apps)
- `requirements.txt` - Python dependencies (unpinned)
## Database
- SQLite3 (default Django config)
- Database file: `db.sqlite3` at project root
- Configured in `backend/settings.py` lines 89-94
## Platform Requirements
- Python 3.x with pip
- No containerization files (no `Dockerfile`, `docker-compose.yml`)
- No CI/CD configuration detected
- Not configured for production (hardcoded `SECRET_KEY`, `DEBUG = True`, SQLite database)
- WSGI entry point available at `backend/wsgi.application`
- ASGI entry point available at `backend/asgi.py`
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- Use lowercase `snake_case` for all Python modules: `models.py`, `serializers.py`, `forms.py`
- Follow standard Django app file naming: `models.py`, `views.py`, `admin.py`, `apps.py`, `tests.py`, `forms.py`, `serializers.py`
- Migration files use Django's auto-generated numbering: `0001_initial.py`
- Use `PascalCase` for all classes
- Model classes: noun describing the entity (`User`, `UserManager`)
- Serializer classes: descriptive name + `Serializer` suffix (`EmailOnlyRegisterSerializer`, `EmailOnlyLoginSerializer`)
- Form classes: descriptive name + `Form` suffix (`EmailOnlySignupForm`, `AdminUserCreationForm`, `AdminUserChangeForm`)
- Admin classes: model name + `Admin` suffix (`UserAdmin`, `EmailAddressAdmin`)
- Use `snake_case` for all functions and methods
- Admin actions use descriptive verb phrases: `activate_users`, `deactivate_users`, `mark_email_verified`
- Private/internal methods prefixed with underscore: `_create_user` in `accounts/models.py`
- Use `snake_case` for local variables and parameters
- Django settings use `UPPER_SNAKE_CASE`: `AUTH_USER_MODEL`, `ACCOUNT_LOGIN_METHODS`
- Prefix private settings variables with underscore: `_cors_allowed_origins` in `backend/settings.py`
## Code Style
- No explicit formatter config detected (no `.flake8`, `pyproject.toml`, `setup.cfg`, or `.editorconfig`)
- `.gitignore` references `.ruff_cache/`, suggesting Ruff is the intended linter/formatter but is not yet configured
- Indentation: 4 spaces (standard Python)
- String quoting is inconsistent: `backend/settings.py` mixes single quotes (`'django.contrib.admin'`) and double quotes (`"corsheaders"`) -- third-party app entries use double quotes, Django defaults use single quotes
- Prescriptive rule: **Use double quotes for all new string literals** to match the pattern in hand-written code (`accounts/models.py`, `accounts/serializers.py`, `accounts/admin.py` all use double quotes consistently)
- No configured limit. Some lines in `accounts/admin.py` exceed 100 characters (line 54)
- Follow PEP 8 convention: 79 characters for code, 99 characters acceptable with formatter
- Two blank lines between top-level definitions (classes, functions)
- One blank line between methods within a class
- Two blank lines after imports
## Import Organization
- Use `from X import Y` style predominantly, not bare `import X`
- Use `get_user_model()` instead of importing User model directly in all files except `accounts/admin.py` which assigns `User = get_user_model()` at module level
- Relative imports for intra-app references: `from .forms import AdminUserChangeForm, AdminUserCreationForm` in `accounts/admin.py`
- Absolute imports for cross-app and framework references
- Always use `get_user_model()` to reference the User model, never import `accounts.models.User` directly
- Use relative imports within the same Django app
- Use absolute imports for everything else
## Django Patterns
- Email-based authentication with no username field
- Custom manager `UserManager` extending `BaseUserManager` at `accounts/models.py`
- `AbstractUser` subclass with `username = None` to remove the field
- `USERNAME_FIELD = "email"`, `REQUIRED_FIELDS = []`
- Configured via `AUTH_USER_MODEL = "accounts.User"` in `backend/settings.py`
- Use `@admin.register(Model)` decorator pattern for registration (see `accounts/admin.py` line 33)
- Use `@admin.action(description="...")` decorator for admin actions (see `accounts/admin.py` lines 13, 23, 70, 81)
- Custom admin forms for user creation/change: `AdminUserCreationForm`, `AdminUserChangeForm` in `accounts/forms.py`
- Override `BaseUserAdmin` with custom `fieldsets`, `add_fieldsets`, `list_display`, `ordering`
- Use `BigAutoField` as default primary key (`DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'`)
- Implement `__str__` on all models
- Use `extra_fields.setdefault()` pattern for setting defaults in manager methods
- Single settings file at `backend/settings.py` (no split into base/dev/prod)
- Environment variables read via `os.environ.get()` with fallback defaults (see CORS config)
- `python-dotenv` is in requirements but no explicit `load_dotenv()` call in settings
## API Patterns
- All API endpoints prefixed with `api/`: `api/auth/`, `api/schema/`, `api/docs/`
- Auth endpoints delegated to `dj_rest_auth`: `api/auth/` and `api/auth/registration/`
- Schema/docs at `api/schema/` (OpenAPI JSON) and `api/docs/` (Swagger UI)
- Extend `serializers.Serializer` for custom registration (not `ModelSerializer`) at `accounts/serializers.py`
- Extend library serializers for customization: `EmailOnlyLoginSerializer(LoginSerializer)` at `accounts/serializers.py` line 66
- Field-level validation via `validate_<fieldname>` methods
- Cross-field validation via `validate()` method
- Use `gettext_lazy` (`_()`) for all user-facing validation messages
- Token-based auth via `rest_framework.authtoken`
- Session and Basic authentication configured as defaults in `REST_FRAMEWORK`
- allauth handles email verification, account management
- Custom serializers registered via `REST_AUTH` setting in `backend/settings.py`
- Catch Django `ValidationError` and re-raise as DRF `serializers.ValidationError`
- Use `serializers.as_serializer_error(exc)` for conversion (see `accounts/serializers.py` line 59)
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- API-only Django project (no server-rendered HTML views) designed to serve a frontend client
- Email-only authentication (no username field) via django-allauth + dj-rest-auth
- Custom User model extending `AbstractUser` with email as the primary identifier
- Single Django app (`accounts`) handling all user/auth concerns
- SQLite database (development configuration)
## Layers
- Purpose: Django project settings, URL routing, WSGI/ASGI entry points
- Location: `backend/`
- Contains: `settings.py`, `urls.py`, `wsgi.py`, `asgi.py`
- Depends on: Django framework, installed apps
- Used by: All apps and the Django runtime
- Purpose: User model, authentication serializers, admin interface, email templates
- Location: `accounts/`
- Contains: Models, serializers, forms, admin configuration, email templates
- Depends on: `django.contrib.auth`, `allauth`, `dj_rest_auth`, `rest_framework`
- Used by: API endpoints via dj-rest-auth URL routing
- Purpose: Provides REST API endpoints for registration, login, logout, password reset
- Location: Installed packages, configured in `backend/settings.py` and `backend/urls.py`
- Contains: Views, URL patterns, adapters for auth flows
- Depends on: `accounts.serializers` (custom serializers), `accounts.forms` (custom signup form)
- Used by: Frontend clients via `api/auth/` endpoints
- Purpose: Django admin interface for managing users and email addresses
- Location: `accounts/admin.py`
- Contains: Custom `UserAdmin` with activate/deactivate actions, custom `EmailAddressAdmin` with verify/mark-primary actions
- Depends on: `accounts.forms.AdminUserCreationForm`, `accounts.forms.AdminUserChangeForm`, `allauth.account.models.EmailAddress`
- Used by: Staff users via `/admin/`
## Data Flow
- Authentication state: Token-based via `rest_framework.authtoken` (tokens stored in database)
- Session-based authentication also enabled (`SessionAuthentication` in `REST_FRAMEWORK` settings)
- No client-side state management (API-only backend)
## Key Abstractions
- Purpose: Email-only user identity (no username)
- Location: `accounts/models.py`
- Pattern: Extends `AbstractUser`, sets `username = None`, overrides `USERNAME_FIELD = "email"`, provides custom `UserManager` with `create_user()` and `create_superuser()` methods
- Purpose: Adapt dj-rest-auth's default serializers to email-only flow
- Location: `accounts/serializers.py`
- Pattern: `EmailOnlyRegisterSerializer` is a standalone `serializers.Serializer` (not ModelSerializer) that manually validates and creates users via allauth adapter. `EmailOnlyLoginSerializer` extends `LoginSerializer` and removes the `username` field.
- Purpose: Email-only forms for allauth signup and Django admin
- Location: `accounts/forms.py`
- Pattern: `EmailOnlySignupForm` extends allauth `SignupForm` and removes username. `AdminUserCreationForm` and `AdminUserChangeForm` extend Django's built-in forms scoped to email-only fields.
## Entry Points
- Location: `backend/urls.py`
- `api/auth/` - dj-rest-auth endpoints (login, logout, password reset, password change, user details)
- `api/auth/registration/` - dj-rest-auth registration endpoints
- `api/schema/` - OpenAPI schema (drf-spectacular)
- `api/docs/` - Swagger UI (drf-spectacular)
- `admin/` - Django admin interface
- Location: `manage.py`
- Standard Django management commands
- WSGI: `backend/wsgi.py`
- ASGI: `backend/asgi.py`
## Error Handling
- Validation errors in serializers raise `serializers.ValidationError` with field-specific messages, returned as 400 responses with JSON error details
- Django `ValidationError` caught and re-raised as DRF `ValidationError` in `EmailOnlyRegisterSerializer.save()` for password validation
- allauth adapter handles email/password validation rules
- No custom exception handler configured (uses DRF defaults)
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
