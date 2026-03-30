# Coding Conventions

**Analysis Date:** 2026-03-30

## Naming Patterns

**Files:**
- Use lowercase `snake_case` for all Python modules: `models.py`, `serializers.py`, `forms.py`
- Follow standard Django app file naming: `models.py`, `views.py`, `admin.py`, `apps.py`, `tests.py`, `forms.py`, `serializers.py`
- Migration files use Django's auto-generated numbering: `0001_initial.py`

**Classes:**
- Use `PascalCase` for all classes
- Model classes: noun describing the entity (`User`, `UserManager`)
- Serializer classes: descriptive name + `Serializer` suffix (`EmailOnlyRegisterSerializer`, `EmailOnlyLoginSerializer`)
- Form classes: descriptive name + `Form` suffix (`EmailOnlySignupForm`, `AdminUserCreationForm`, `AdminUserChangeForm`)
- Admin classes: model name + `Admin` suffix (`UserAdmin`, `EmailAddressAdmin`)

**Functions:**
- Use `snake_case` for all functions and methods
- Admin actions use descriptive verb phrases: `activate_users`, `deactivate_users`, `mark_email_verified`
- Private/internal methods prefixed with underscore: `_create_user` in `accounts/models.py`

**Variables:**
- Use `snake_case` for local variables and parameters
- Django settings use `UPPER_SNAKE_CASE`: `AUTH_USER_MODEL`, `ACCOUNT_LOGIN_METHODS`
- Prefix private settings variables with underscore: `_cors_allowed_origins` in `backend/settings.py`

## Code Style

**Formatting:**
- No explicit formatter config detected (no `.flake8`, `pyproject.toml`, `setup.cfg`, or `.editorconfig`)
- `.gitignore` references `.ruff_cache/`, suggesting Ruff is the intended linter/formatter but is not yet configured
- Indentation: 4 spaces (standard Python)
- String quoting is inconsistent: `backend/settings.py` mixes single quotes (`'django.contrib.admin'`) and double quotes (`"corsheaders"`) -- third-party app entries use double quotes, Django defaults use single quotes
- Prescriptive rule: **Use double quotes for all new string literals** to match the pattern in hand-written code (`accounts/models.py`, `accounts/serializers.py`, `accounts/admin.py` all use double quotes consistently)

**Line Length:**
- No configured limit. Some lines in `accounts/admin.py` exceed 100 characters (line 54)
- Follow PEP 8 convention: 79 characters for code, 99 characters acceptable with formatter

**Blank Lines:**
- Two blank lines between top-level definitions (classes, functions)
- One blank line between methods within a class
- Two blank lines after imports

## Import Organization

**Order observed across all files:**
1. Standard library imports (`os`, `pathlib`)
2. Django imports (`django.contrib`, `django.db`, `django.urls`)
3. Third-party imports (`rest_framework`, `allauth`, `dj_rest_auth`, `drf_spectacular`)
4. Local/relative imports (`.forms`, `.serializers`)

**Import style:**
- Use `from X import Y` style predominantly, not bare `import X`
- Use `get_user_model()` instead of importing User model directly in all files except `accounts/admin.py` which assigns `User = get_user_model()` at module level
- Relative imports for intra-app references: `from .forms import AdminUserChangeForm, AdminUserCreationForm` in `accounts/admin.py`
- Absolute imports for cross-app and framework references

**Prescriptive rules:**
- Always use `get_user_model()` to reference the User model, never import `accounts.models.User` directly
- Use relative imports within the same Django app
- Use absolute imports for everything else

## Django Patterns

**Custom User Model:**
- Email-based authentication with no username field
- Custom manager `UserManager` extending `BaseUserManager` at `accounts/models.py`
- `AbstractUser` subclass with `username = None` to remove the field
- `USERNAME_FIELD = "email"`, `REQUIRED_FIELDS = []`
- Configured via `AUTH_USER_MODEL = "accounts.User"` in `backend/settings.py`

**Admin Customization:**
- Use `@admin.register(Model)` decorator pattern for registration (see `accounts/admin.py` line 33)
- Use `@admin.action(description="...")` decorator for admin actions (see `accounts/admin.py` lines 13, 23, 70, 81)
- Custom admin forms for user creation/change: `AdminUserCreationForm`, `AdminUserChangeForm` in `accounts/forms.py`
- Override `BaseUserAdmin` with custom `fieldsets`, `add_fieldsets`, `list_display`, `ordering`

**Model Patterns:**
- Use `BigAutoField` as default primary key (`DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'`)
- Implement `__str__` on all models
- Use `extra_fields.setdefault()` pattern for setting defaults in manager methods

**Settings:**
- Single settings file at `backend/settings.py` (no split into base/dev/prod)
- Environment variables read via `os.environ.get()` with fallback defaults (see CORS config)
- `python-dotenv` is in requirements but no explicit `load_dotenv()` call in settings

## API Patterns

**URL Structure:**
- All API endpoints prefixed with `api/`: `api/auth/`, `api/schema/`, `api/docs/`
- Auth endpoints delegated to `dj_rest_auth`: `api/auth/` and `api/auth/registration/`
- Schema/docs at `api/schema/` (OpenAPI JSON) and `api/docs/` (Swagger UI)

**Serializers:**
- Extend `serializers.Serializer` for custom registration (not `ModelSerializer`) at `accounts/serializers.py`
- Extend library serializers for customization: `EmailOnlyLoginSerializer(LoginSerializer)` at `accounts/serializers.py` line 66
- Field-level validation via `validate_<fieldname>` methods
- Cross-field validation via `validate()` method
- Use `gettext_lazy` (`_()`) for all user-facing validation messages

**Authentication:**
- Token-based auth via `rest_framework.authtoken`
- Session and Basic authentication configured as defaults in `REST_FRAMEWORK`
- allauth handles email verification, account management
- Custom serializers registered via `REST_AUTH` setting in `backend/settings.py`

**Error Handling in Serializers:**
- Catch Django `ValidationError` and re-raise as DRF `serializers.ValidationError`
- Use `serializers.as_serializer_error(exc)` for conversion (see `accounts/serializers.py` line 59)

---

*Convention analysis: 2026-03-30*
