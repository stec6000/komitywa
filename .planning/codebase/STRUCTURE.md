# Codebase Structure

**Analysis Date:** 2026-03-30

## Directory Layout

```
komitywa/
├── backend/                    # Django project configuration
│   ├── __init__.py
│   ├── asgi.py                 # ASGI entry point
│   ├── settings.py             # All Django settings
│   ├── urls.py                 # Root URL configuration
│   └── wsgi.py                 # WSGI entry point
├── accounts/                   # User/auth Django app
│   ├── __init__.py
│   ├── admin.py                # User and EmailAddress admin config
│   ├── apps.py                 # App configuration
│   ├── forms.py                # Signup and admin forms
│   ├── migrations/             # Database migrations
│   │   ├── __init__.py
│   │   └── 0001_initial.py     # Initial User model migration
│   ├── models.py               # Custom User model and UserManager
│   ├── serializers.py          # DRF serializers for registration/login
│   ├── templates/              # Email templates
│   │   └── account/
│   │       └── email/
│   │           ├── email_confirmation_message.txt
│   │           ├── email_confirmation_subject.txt
│   │           ├── password_reset_key_message.txt
│   │           └── password_reset_key_subject.txt
│   ├── tests.py                # Auth endpoint tests
│   └── views.py                # Empty (views handled by dj-rest-auth)
├── manage.py                   # Django CLI entry point
├── requirements.txt            # Python dependencies
├── .gitignore
└── README.md
```

## Directory Purposes

**`backend/`:**
- Purpose: Django project package (settings, URL routing, server entry points)
- Contains: Configuration files only, no business logic
- Key files: `settings.py` (all config including auth, CORS, REST framework), `urls.py` (all API route definitions)

**`accounts/`:**
- Purpose: The sole Django app; handles user model, authentication customization, admin interface
- Contains: Models, serializers, forms, admin config, email templates, tests
- Key files: `models.py` (custom User), `serializers.py` (registration/login serializers), `admin.py` (User + EmailAddress admin)

**`accounts/migrations/`:**
- Purpose: Database schema migrations for the accounts app
- Contains: Auto-generated Django migration files
- Key files: `0001_initial.py` (creates User table)

**`accounts/templates/account/email/`:**
- Purpose: Override allauth's default email templates with Polish-language versions
- Contains: Plain text email templates for confirmation and password reset
- Key files: `email_confirmation_message.txt`, `password_reset_key_message.txt`

## Key File Locations

**Entry Points:**
- `manage.py`: Django management CLI
- `backend/wsgi.py`: WSGI application for production deployment
- `backend/asgi.py`: ASGI application for async deployment
- `backend/urls.py`: All URL routes (admin, API auth, API docs)

**Configuration:**
- `backend/settings.py`: All Django, DRF, allauth, CORS, and auth settings
- `requirements.txt`: Python package dependencies (unpinned)

**Core Logic:**
- `accounts/models.py`: Custom `User` model (email-only, no username) and `UserManager`
- `accounts/serializers.py`: `EmailOnlyRegisterSerializer` (registration validation + user creation), `EmailOnlyLoginSerializer` (login without username)
- `accounts/forms.py`: `EmailOnlySignupForm` (allauth form override), `AdminUserCreationForm`, `AdminUserChangeForm`
- `accounts/admin.py`: `UserAdmin` (custom fieldsets, bulk activate/deactivate actions), `EmailAddressAdmin` (verify/mark-primary actions)

**Testing:**
- `accounts/tests.py`: 5 tests covering registration (success, duplicate email, password mismatch) and login (success, invalid credentials)

## Naming Conventions

**Files:**
- Standard Django convention: `models.py`, `views.py`, `serializers.py`, `forms.py`, `admin.py`, `tests.py`, `apps.py`

**Directories:**
- Django project config: `backend/` (named after the project)
- Django apps: `accounts/` (lowercase, plural noun)
- Templates follow allauth's expected path: `templates/account/email/`

**Classes:**
- Models: PascalCase nouns (`User`, `UserManager`)
- Serializers: PascalCase with `Serializer` suffix (`EmailOnlyRegisterSerializer`, `EmailOnlyLoginSerializer`)
- Forms: PascalCase with `Form` suffix (`EmailOnlySignupForm`, `AdminUserCreationForm`)
- Admin: PascalCase with `Admin` suffix (`UserAdmin`, `EmailAddressAdmin`)

## Where to Add New Code

**New Django App:**
- Create at project root: `komitywa/<app_name>/`
- Register in `backend/settings.py` under `INSTALLED_APPS`
- Add URL patterns in `backend/urls.py` under `urlpatterns`

**New API Endpoint (within accounts):**
- View: `accounts/views.py` (currently empty, ready for custom views)
- Serializer: `accounts/serializers.py`
- URL routing: Add to `backend/urls.py` or create `accounts/urls.py` and include it

**New Model:**
- For user-related: `accounts/models.py`
- For other domains: Create a new app at project root
- After adding: run `python manage.py makemigrations` and `python manage.py migrate`

**New Tests:**
- For accounts: `accounts/tests.py` (or split into `accounts/tests/` package as it grows)
- For new apps: `<app_name>/tests.py`
- Pattern: Use `django.test.TestCase`, `@override_settings` for auth config

**New Email Templates:**
- Location: `accounts/templates/account/email/`
- Follow allauth template naming convention (e.g., `<event>_message.txt`, `<event>_subject.txt`)

**New Admin Configuration:**
- For accounts models: `accounts/admin.py`
- For new apps: `<app_name>/admin.py`

## Special Directories

**`accounts/migrations/`:**
- Purpose: Auto-generated database migration files
- Generated: Yes (via `manage.py makemigrations`)
- Committed: Yes (must be committed for reproducible deployments)

**`accounts/templates/`:**
- Purpose: Overrides allauth default email templates
- Generated: No (manually created)
- Committed: Yes

---

*Structure analysis: 2026-03-30*
