# Technology Stack

**Analysis Date:** 2026-03-30

## Languages

**Primary:**
- Python 3.x - All backend code (Django project)

## Runtime

**Environment:**
- Python 3.x (exact version not pinned; no `.python-version` or `runtime.txt` present)
- Django settings module: `backend.settings`

**Package Manager:**
- pip
- Lockfile: missing (no `requirements.lock`, `Pipfile.lock`, or `poetry.lock`; only unpinned `requirements.txt`)

## Frameworks

**Core:**
- Django 5.2.x - Web framework (version from `backend/settings.py` generated comment: "using Django 5.2.11")
- Django REST Framework (djangorestframework) - REST API layer, configured in `backend/settings.py` under `REST_FRAMEWORK`
- django-allauth - Authentication and account management
- dj-rest-auth - REST API authentication endpoints (login, logout, registration)

**API Documentation:**
- drf-spectacular - OpenAPI 3 schema generation and Swagger UI

**Build/Dev:**
- `manage.py` - Standard Django management CLI (entry point at `manage.py`)

## Key Dependencies

All dependencies are declared in `requirements.txt` without version pins:

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

**Environment Variables:**
- `CORS_ALLOWED_ORIGINS` - Comma-separated allowed origins (defaults to `http://localhost:3000`, `http://127.0.0.1:3000`)
- `DJANGO_SETTINGS_MODULE` - Set to `backend.settings` in `manage.py`

**Key Config Files:**
- `backend/settings.py` - All Django settings (database, auth, REST framework, CORS, installed apps)
- `requirements.txt` - Python dependencies (unpinned)

**Django Settings Module:** `backend.settings` (set in `manage.py`)

**WSGI Application:** `backend.wsgi.application` (defined in `backend/settings.py`)

## Database

- SQLite3 (default Django config)
- Database file: `db.sqlite3` at project root
- Configured in `backend/settings.py` lines 89-94

## Platform Requirements

**Development:**
- Python 3.x with pip
- No containerization files (no `Dockerfile`, `docker-compose.yml`)
- No CI/CD configuration detected

**Production:**
- Not configured for production (hardcoded `SECRET_KEY`, `DEBUG = True`, SQLite database)
- WSGI entry point available at `backend/wsgi.application`
- ASGI entry point available at `backend/asgi.py`

---

*Stack analysis: 2026-03-30*
