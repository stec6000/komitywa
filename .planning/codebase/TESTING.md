# Testing Patterns

**Analysis Date:** 2026-03-30

## Test Framework

**Runner:**
- Django's built-in test framework (`django.test.TestCase`)
- No pytest configuration detected (though `.gitignore` includes `.pytest_cache/`, pytest is not in `requirements.txt`)
- Config: uses default Django test runner configured via `manage.py`

**Assertion Library:**
- Django's `TestCase` assertions: `assertEqual`, `assertIn`, `assertTrue`
- No additional assertion libraries

**Run Commands:**
```bash
python manage.py test                    # Run all tests
python manage.py test accounts           # Run tests for accounts app
python manage.py test accounts.tests.AccountsAuthTests.test_register_success  # Run single test
```

## Test File Organization

**Location:**
- Co-located within each Django app: `accounts/tests.py`
- Single test file per app (standard Django convention)

**Naming:**
- Test files: `tests.py` (Django default)
- Test classes: descriptive name + `Tests` suffix: `AccountsAuthTests`
- Test methods: `test_` prefix with descriptive snake_case: `test_register_success`, `test_register_duplicate_email_returns_400`

**Method naming pattern:**
- Success cases: `test_<action>_success` (e.g., `test_register_success`, `test_login_success`)
- Failure cases: `test_<action>_<condition>_returns_<status_code>` (e.g., `test_register_duplicate_email_returns_400`, `test_login_invalid_credentials_returns_400`)

## Test Structure

**Suite Organization:**
```python
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(
    ACCOUNT_EMAIL_VERIFICATION="none",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class AccountsAuthTests(TestCase):
    def setUp(self):
        self.register_url = reverse("rest_register")
        self.login_url = reverse("rest_login")
        self.user_model = get_user_model()

    def test_register_success(self):
        response = self.client.post(
            self.register_url,
            {
                "email": "user1@example.com",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
            },
        )
        self.assertIn(response.status_code, (201, 204))
        self.assertTrue(
            self.user_model.objects.filter(email__iexact="user1@example.com").exists()
        )
```

**Key Patterns:**
- `@override_settings()` decorator on test classes to disable email verification and use in-memory email backend for testing
- `setUp` method resolves URLs via `reverse()` and stores as instance attributes
- `self.client` (Django test client) for HTTP requests -- no DRF `APIClient`
- `get_user_model()` stored as `self.user_model` for creating test users

## Test Data Patterns

**User Creation:**
```python
# Create users directly via the custom manager
self.user_model.objects.create_user(
    email="login@example.com",
    password="StrongPass123",
)
```

**Request Payloads:**
- Inline dictionaries passed directly to `self.client.post()`
- No shared fixtures, factories, or factory libraries (e.g., factory_boy)
- Test email addresses use `@example.com` domain
- Password pattern: `StrongPass123` (meets Django password validators)

## Mocking

**Framework:** None detected

**Current approach:**
- `@override_settings()` to swap Django settings for test isolation
- `EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"` to prevent real emails
- `ACCOUNT_EMAIL_VERIFICATION="none"` to bypass allauth email verification flow
- No use of `unittest.mock`, `patch`, or any mocking library

**Prescriptive guidance:**
- Use `@override_settings()` to modify Django settings in tests
- Use `django.core.mail.backends.locmem.EmailBackend` for email-related tests
- When mocking is needed, use `unittest.mock.patch` from the standard library

## Coverage

**Requirements:** None enforced

**Tools:** `.gitignore` includes `.coverage` and `htmlcov/`, indicating coverage.py is intended but not in `requirements.txt`

**To add coverage support:**
```bash
pip install coverage
coverage run manage.py test
coverage report
coverage html                # generates htmlcov/
```

## Test Types

**Unit Tests:**
- Not present as separate category

**Integration Tests:**
- All existing tests are integration-level: they exercise the full HTTP request/response cycle through Django's test client
- Tests hit real serializers, views, models, and database (SQLite)
- File: `accounts/tests.py`

**E2E Tests:**
- Not present. No Selenium, Playwright, or similar framework

## What Is Tested

**`accounts/tests.py` -- `AccountsAuthTests` (5 tests):**
| Test | What it verifies |
|------|-----------------|
| `test_register_success` | POST to registration endpoint creates user, returns 201/204 |
| `test_register_duplicate_email_returns_400` | Duplicate email registration rejected with 400 |
| `test_register_password_mismatch_returns_400` | Mismatched passwords rejected with 400 |
| `test_login_success` | Valid credentials return 200 with auth token key |
| `test_login_invalid_credentials_returns_400` | Wrong password returns 400 |

## Test Coverage Gaps

**Untested areas:**
- `accounts/admin.py`: Admin actions (`activate_users`, `deactivate_users`, `mark_email_verified`, `mark_email_primary`) and custom `UserAdmin` configuration have no tests
- `accounts/models.py`: `UserManager.create_superuser` validation logic (is_staff/is_superuser checks, ValueError raises) not directly tested
- `accounts/models.py`: `User.__str__` method not tested
- `accounts/forms.py`: `EmailOnlySignupForm`, `AdminUserCreationForm`, `AdminUserChangeForm` have no dedicated tests
- Password reset flow (provided by dj-rest-auth) not tested
- Logout endpoint not tested
- Token expiry/refresh behavior not tested
- CORS configuration not tested

## Assertion Patterns

**Status Code Checks:**
```python
# Exact match
self.assertEqual(response.status_code, 400)

# Multiple acceptable codes
self.assertIn(response.status_code, (201, 204))
```

**Database State Checks:**
```python
self.assertTrue(
    self.user_model.objects.filter(email__iexact="user1@example.com").exists()
)
```

**Response Body Checks:**
```python
if response.content:
    data = response.json()
    self.assertIn("key", data)
```

## Writing New Tests

**Follow this pattern for new API tests:**
1. Create a test class extending `django.test.TestCase`
2. Apply `@override_settings(ACCOUNT_EMAIL_VERIFICATION="none", EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")` if auth-related
3. Use `setUp` to resolve URLs with `reverse()` and store `get_user_model()`
4. Name success tests `test_<action>_success`
5. Name failure tests `test_<action>_<condition>_returns_<status_code>`
6. Use `self.client.post()` / `self.client.get()` for HTTP calls
7. Assert status codes and database state, not just response content

---

*Testing analysis: 2026-03-30*
