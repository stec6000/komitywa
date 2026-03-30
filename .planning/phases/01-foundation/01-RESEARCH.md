# Phase 1: Foundation - Research

**Researched:** 2026-03-30
**Domain:** Django template infrastructure, environment configuration, Bootstrap 5 responsive design, cookie consent (RODO)
**Confidence:** HIGH

## Summary

This phase transforms the existing API-only Django 5.2 backend into a server-rendered HTML application with proper template hierarchy, environment-based configuration, static/media file handling, Bootstrap 5 responsive layout, and a RODO-compliant cookie consent banner. The existing codebase already has `python-dotenv` in requirements (unused), a hardcoded SECRET_KEY, and no template directories configured.

The primary technical challenges are: (1) migrating hardcoded secrets to `.env` without breaking existing functionality, (2) setting up a proper template hierarchy with `base.html` that all future phases build on, (3) integrating Bootstrap 5 with custom warm/natural branding (greens, beiges, organic feel), and (4) implementing a simple cookie consent banner compliant with RODO (Polish GDPR).

**Primary recommendation:** Use `django-environ` for env configuration (replaces unused `python-dotenv`), Bootstrap 5.3.x via CDN for rapid setup, custom CSS variables for brand colors, Google Fonts (Lora + Nunito) for warm typography, and a lightweight custom cookie consent implementation (vanilla JS + localStorage) given the simple accept/reject requirement.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Main nav links: Przepisy, Sklep, O nas, Kontakt
- **D-02:** Logo in nav links to landing page (strona glowna)
- **D-03:** Cart icon with item count badge in navigation
- **D-05:** Minimal bottom bar style cookie banner (not modal, not full-screen)
- **D-06:** Two buttons: "Akceptuj" and "Odrzuc" (simple accept/reject, no granular settings)
- **D-07:** Must comply with RODO -- remember user choice, don't re-show after decision
- **D-08:** Climate/vibe: Warm and natural -- like a home kitchen, organic shapes, cozy feeling
- **D-09:** Color palette: Greens + beiges -- sage, olive, cream, natural earth tones
- **D-11:** Overall design should feel handcrafted, inviting, organic -- not corporate or cold

### Claude's Discretion
- **D-04:** Mobile menu implementation style (hamburger or bottom bar)
- **D-10:** Typography -- choose fonts that match the warm/natural kitchen vibe
- Specific Bootstrap 5 customization approach (SCSS variables vs CSS custom properties)
- Cookie consent implementation method (custom vs library)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FOUND-01 | Aplikacja uzywa zmiennych srodowiskowych (.env) zamiast hardkodowanych sekretow | django-environ setup, .env template, settings.py migration pattern |
| FOUND-02 | Strona renderuje szablony Django z base.html (naglowek, stopka, nawigacja) | Template hierarchy pattern, base.html structure, template tags |
| FOUND-03 | Strona jest responsywna na urzadzeniach mobilnych (Bootstrap 5) | Bootstrap 5.3.x CDN integration, responsive grid, breakpoints |
| FOUND-04 | Pliki statyczne (CSS, JS, obrazy) sa poprawnie serwowane | STATIC_URL, STATICFILES_DIRS, collectstatic, django.contrib.staticfiles |
| FOUND-05 | Upload mediow (zdjecia, pliki) dziala poprawnie | MEDIA_ROOT, MEDIA_URL, URL patterns for dev serving |
| LEGAL-03 | Strona wyswietla cookie consent banner | Custom vanilla JS banner, localStorage persistence, RODO compliance |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Stack:** Django 5.2 + Django templates (no SPA)
- **Language:** Polish only (all UI text in Polish)
- **String quotes:** Use double quotes for all new string literals
- **Imports:** Use `from X import Y` style, relative imports within same app
- **Settings:** Single settings file at `backend/settings.py`
- **GSD Workflow:** All edits through GSD commands

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django | 5.2.x (installed) | Web framework | Already in project, locked constraint |
| django-environ | 0.11.2 | Environment variable management | Django-specific, type casting, replaces unused python-dotenv |
| Bootstrap | 5.3.8 (CDN) | Responsive CSS framework | Industry standard, locked decision (D-08/D-09 achievable via customization) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Google Fonts (Lora + Nunito) | CDN | Typography | Warm serif headings + friendly sans-serif body text |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| django-environ | python-dotenv (already in requirements.txt) | python-dotenv only loads .env to os.environ; django-environ adds type casting (bool, int, list), database URL parsing, and Django-specific helpers. Worth the switch. |
| Bootstrap 5 CDN | django-bootstrap5 package | django-bootstrap5 adds template tags for forms but adds dependency; CDN is simpler for this phase which only needs layout, not form rendering |
| Bootstrap 5 CDN | Local static files | CDN is faster for dev; can migrate to static later for production offline support |
| Custom cookie banner | django-cookie-consent 0.8.0 | Library is overkill for simple accept/reject; adds models, migrations, admin UI for managing cookie groups -- unnecessary when requirement is just two buttons |

**Installation:**
```bash
pip install django-environ
# Remove python-dotenv from requirements.txt (replaced by django-environ)
```

**Version verification:**
- django-environ: 0.11.2 (verified via pip install --dry-run 2026-03-30)
- Bootstrap: 5.3.8 (verified via getbootstrap.com 2026-03-30)
- django-cookie-consent: 0.8.0 (evaluated and rejected -- overkill for simple banner)

## Architecture Patterns

### Recommended Project Structure
```
komitywa/
├── backend/
│   ├── settings.py          # Modified: env vars, template dirs, static/media config
│   ├── urls.py              # Modified: add static/media URL patterns, template views
│   ├── wsgi.py
│   └── asgi.py
├── templates/                # NEW: project-level templates
│   ├── base.html            # Master template: head, nav, content block, footer, cookie banner
│   ├── includes/
│   │   ├── _navbar.html     # Navigation partial (D-01 through D-04)
│   │   ├── _footer.html     # Footer partial
│   │   └── _cookie_banner.html  # Cookie consent banner partial (D-05, D-06)
│   └── pages/
│       └── home.html        # Placeholder home page (extends base.html)
├── static/                   # NEW: project-level static files
│   ├── css/
│   │   └── main.css         # Custom styles: brand colors, typography, overrides
│   ├── js/
│   │   └── cookie_consent.js # Cookie banner logic (D-07)
│   └── images/              # Brand images, logo placeholder
├── media/                    # NEW: user-uploaded files (gitignored)
├── accounts/                 # Existing app (unchanged in this phase)
├── .env                      # NEW: environment variables (gitignored)
├── .env.example              # NEW: template for .env (committed)
├── requirements.txt          # Modified: django-environ replaces python-dotenv
└── manage.py
```

### Pattern 1: Environment Configuration with django-environ
**What:** Replace hardcoded secrets with environment variables loaded from `.env`
**When to use:** All sensitive settings (SECRET_KEY, DEBUG, ALLOWED_HOSTS, DATABASE_URL)
**Example:**
```python
# backend/settings.py - top of file
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)

environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
```

### Pattern 2: Template Hierarchy with Block Structure
**What:** Single base.html with named blocks that child templates override
**When to use:** Every page in the application
**Example:**
```html
{# templates/base.html #}
{% load static %}
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}Kuchenna Komitywa{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css"
          rel="stylesheet"
          integrity="sha384-..." crossorigin="anonymous">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Lora:wght@400;600;700&family=Nunito:wght@400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{% static 'css/main.css' %}">
    {% block extra_css %}{% endblock %}
</head>
<body>
    {% include "includes/_navbar.html" %}
    <main>
        {% block content %}{% endblock %}
    </main>
    {% include "includes/_footer.html" %}
    {% include "includes/_cookie_banner.html" %}
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"
            integrity="sha384-..." crossorigin="anonymous"></script>
    <script src="{% static 'js/cookie_consent.js' %}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### Pattern 3: Cookie Consent with localStorage
**What:** Simple bottom bar with Akceptuj/Odrzuc, persisted in localStorage
**When to use:** Every page load (check localStorage, show if no decision stored)
**Example:**
```javascript
// static/js/cookie_consent.js
(function() {
    const CONSENT_KEY = "cookie_consent";
    const consent = localStorage.getItem(CONSENT_KEY);

    if (consent !== null) return; // Already decided, don't show

    const banner = document.getElementById("cookie-banner");
    if (!banner) return;
    banner.style.display = "block";

    document.getElementById("cookie-accept").addEventListener("click", function() {
        localStorage.setItem(CONSENT_KEY, "accepted");
        banner.style.display = "none";
    });

    document.getElementById("cookie-reject").addEventListener("click", function() {
        localStorage.setItem(CONSENT_KEY, "rejected");
        banner.style.display = "none";
    });
})();
```

### Pattern 4: Static and Media File Configuration
**What:** Configure Django to serve static and media files in development
**When to use:** Settings and URL configuration
**Example:**
```python
# backend/settings.py
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

```python
# backend/urls.py - add at bottom
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### Pattern 5: Brand Color System with CSS Custom Properties
**What:** Define brand colors as CSS custom properties, override Bootstrap defaults
**When to use:** All custom styling
**Example:**
```css
/* static/css/main.css */
:root {
    /* Brand palette: warm greens + beiges */
    --kk-sage: #9CAF88;
    --kk-olive: #6B7F5E;
    --kk-olive-dark: #4A5A40;
    --kk-cream: #F5F0E8;
    --kk-warm-white: #FDFBF7;
    --kk-beige: #D4C5A9;
    --kk-earth: #8B7355;
    --kk-text: #3D3D3D;
    --kk-text-light: #6B6B6B;

    /* Typography */
    --kk-font-heading: "Lora", serif;
    --kk-font-body: "Nunito", sans-serif;
}

body {
    font-family: var(--kk-font-body);
    color: var(--kk-text);
    background-color: var(--kk-warm-white);
}

h1, h2, h3, h4, h5, h6 {
    font-family: var(--kk-font-heading);
    color: var(--kk-olive-dark);
}
```

### Anti-Patterns to Avoid
- **Hardcoding secrets in settings.py:** Use env vars for SECRET_KEY, DEBUG, database credentials. The current codebase has this problem -- must be fixed.
- **Putting templates inside app directories when they are project-wide:** Use project-level `templates/` directory for base.html and shared includes.
- **Using Bootstrap classes without custom brand layer:** Always define brand CSS custom properties first, then use them in custom classes. Do not rely solely on Bootstrap utility classes for brand identity.
- **Serving media files without the DEBUG check:** `static()` URL patterns for media must be wrapped in `if settings.DEBUG` -- production uses a web server.
- **Missing `{% load static %}` tag:** Every template that references static files must load the tag.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Responsive grid system | Custom CSS grid/flexbox layout | Bootstrap 5 grid | Hundreds of edge cases across devices, breakpoints, gutters |
| Environment variable parsing | Custom os.environ.get() with type casting | django-environ | Type casting, default values, database URL parsing, .env loading |
| CSS reset / normalization | Custom reset stylesheet | Bootstrap's Reboot | Cross-browser consistency already handled |
| Icon system for nav | Custom SVG icon management | Bootstrap Icons (CDN) | Cart icon (D-03), hamburger menu, consistent icon set |

**Key insight:** This phase is about infrastructure, not content. Every choice should optimize for "how easily can future phases add pages" rather than pixel-perfect design of the skeleton itself.

## Common Pitfalls

### Pitfall 1: Forgetting to Add Template Directory to TEMPLATES Setting
**What goes wrong:** Django cannot find base.html or any project-level templates, returning TemplateDoesNotExist errors.
**Why it happens:** The current settings.py has `'DIRS': []` -- an empty list.
**How to avoid:** Set `'DIRS': [BASE_DIR / "templates"]` in the TEMPLATES configuration.
**Warning signs:** TemplateDoesNotExist exception on any page load.

### Pitfall 2: SECRET_KEY Missing from .env on Fresh Clone
**What goes wrong:** Application crashes on startup with ImproperlyConfigured error.
**Why it happens:** `.env` is gitignored (correctly), but developer forgets to create it.
**How to avoid:** Create `.env.example` with all required variables (without values for secrets). Add a comment in settings.py or a startup check.
**Warning signs:** ImproperlyConfigured: Set the SECRET_KEY environment variable.

### Pitfall 3: Static Files Not Loading in Development
**What goes wrong:** CSS/JS 404 errors, unstyled pages.
**Why it happens:** `STATICFILES_DIRS` not configured, or `{% load static %}` missing from templates.
**How to avoid:** (1) Set STATICFILES_DIRS pointing to project `static/` directory. (2) Ensure `django.contrib.staticfiles` is in INSTALLED_APPS (already is). (3) Always use `{% static 'path' %}` tag, never hardcode paths.
**Warning signs:** 404 responses for `/static/css/main.css` in browser dev tools.

### Pitfall 4: Bootstrap CDN Integrity Hash Mismatch
**What goes wrong:** Browser refuses to load Bootstrap CSS/JS due to SRI (Subresource Integrity) check failure.
**Why it happens:** Copy-pasting integrity hash from wrong Bootstrap version.
**How to avoid:** Always get the CDN link + integrity hash from the official Bootstrap 5.3 download page for the exact version being used.
**Warning signs:** Console error about integrity check failure, Bootstrap not loading.

### Pitfall 5: LANGUAGE_CODE Still Set to 'en-us'
**What goes wrong:** Django built-in templates, admin, and form validation messages appear in English instead of Polish.
**Why it happens:** Default Django setting not updated for Polish-only project.
**How to avoid:** Set `LANGUAGE_CODE = "pl"` and `TIME_ZONE = "Europe/Warsaw"` in settings.py.
**Warning signs:** Admin interface showing English labels.

### Pitfall 6: Cookie Banner Re-appearing After Page Navigation
**What goes wrong:** Cookie banner flashes on every page load even after user has made a choice.
**Why it happens:** JavaScript runs before checking localStorage, or banner is initially visible and JS hides it too late.
**How to avoid:** Set banner to `display: none` in CSS by default. JS reveals it only if no consent found in localStorage.
**Warning signs:** Banner briefly flashing on navigation.

## Code Examples

### django-environ .env File Template
```bash
# .env.example -- copy to .env and fill in values
SECRET_KEY=change-me-to-a-random-string
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Settings.py Migration Pattern
```python
# backend/settings.py -- key changes
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Templates -- add project templates directory
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Internationalization -- Polish
LANGUAGE_CODE = "pl"
TIME_ZONE = "Europe/Warsaw"

# Static files
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

### Navigation Partial (D-01 through D-04)
```html
{# templates/includes/_navbar.html #}
{% load static %}
<nav class="navbar navbar-expand-lg" style="background-color: var(--kk-cream);">
    <div class="container">
        <a class="navbar-brand" href="{% url 'home' %}">
            <span class="brand-text">Kuchenna Komitywa</span>
        </a>
        <button class="navbar-toggler" type="button"
                data-bs-toggle="collapse" data-bs-target="#mainNav">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="mainNav">
            <ul class="navbar-nav ms-auto">
                <li class="nav-item"><a class="nav-link" href="#">Przepisy</a></li>
                <li class="nav-item"><a class="nav-link" href="#">Sklep</a></li>
                <li class="nav-item"><a class="nav-link" href="#">O nas</a></li>
                <li class="nav-item"><a class="nav-link" href="#">Kontakt</a></li>
            </ul>
            <a class="nav-link position-relative ms-3" href="#">
                <i class="bi bi-cart3"></i>
                <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
                    0
                </span>
            </a>
        </div>
    </div>
</nav>
```

### Cookie Banner Partial (D-05, D-06)
```html
{# templates/includes/_cookie_banner.html #}
<div id="cookie-banner" class="cookie-banner" style="display: none;">
    <div class="container d-flex justify-content-between align-items-center py-3">
        <p class="mb-0 me-3">
            Ta strona korzysta z plikow cookie w celu zapewnienia najlepszej jakosci uslug.
        </p>
        <div class="d-flex gap-2 flex-shrink-0">
            <button id="cookie-reject" class="btn btn-outline-secondary btn-sm">Odrzuc</button>
            <button id="cookie-accept" class="btn btn-success btn-sm">Akceptuj</button>
        </div>
    </div>
</div>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| python-dotenv + os.environ.get() | django-environ with type casting | django-environ 0.11.x (2024) | Cleaner settings, built-in type coercion |
| Bootstrap 4 | Bootstrap 5.3 with CSS custom properties | Bootstrap 5.3 (2023+) | No jQuery dependency, native dark mode support, CSS variables |
| GDPR cookie popups with full category management | Simple accept/reject for minimal cookie use | Ongoing trend | Simpler sites need simpler consent UX |

**Deprecated/outdated:**
- `python-dotenv` for Django: Works but offers no Django-specific features. django-environ is the community standard.
- Bootstrap 4: No longer receiving updates. Bootstrap 5.3.x is current.
- jQuery: Bootstrap 5 dropped jQuery dependency entirely.

## Open Questions

1. **Bootstrap CDN integrity hashes**
   - What we know: Bootstrap 5.3.8 is current. CDN links available from official site.
   - What's unclear: Exact SRI integrity hash values must be fetched from official CDN page at implementation time.
   - Recommendation: Fetch from https://getbootstrap.com/docs/5.3/getting-started/introduction/ during implementation.

2. **Logo asset**
   - What we know: D-02 says logo links to home page. D-08 says warm/natural vibe.
   - What's unclear: No logo exists yet. Visual identity is being created from scratch.
   - Recommendation: Use text-based logo ("Kuchenna Komitywa" in heading font) as placeholder. Replace with image when brand assets are created.

3. **Mobile menu style (D-04 -- Claude's Discretion)**
   - What we know: Hamburger is Bootstrap's default; bottom bar would require custom implementation.
   - Recommendation: Use Bootstrap's standard hamburger collapse menu. It fits the warm/natural brand, is well-tested on all devices, and requires zero custom JS. Bottom bar would add complexity with no clear UX benefit for a food/recipe site.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ | Django 5.2 | Partial | 3.11.11 via pyenv (active: 3.8.18) | Must switch pyenv to 3.11.11 or create virtualenv with it |
| pip | Package management | Yes | 25.0.1 | -- |
| Bootstrap 5.3 | FOUND-03 | CDN (no install needed) | 5.3.8 | -- |
| Google Fonts | Typography | CDN (no install needed) | -- | -- |

**Missing dependencies with no fallback:**
- Python version mismatch: Active Python is 3.8.18 but Django 5.2 requires 3.10+. Pyenv has 3.11.11 available. Phase plan must include creating a virtualenv with Python 3.11.11.

**Missing dependencies with fallback:**
- None

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Django TestCase (built-in, no extra dependency) |
| Config file | None needed (Django's default test runner) |
| Quick run command | `python manage.py test --verbosity=2` |
| Full suite command | `python manage.py test --verbosity=2` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FOUND-01 | Settings load from env vars, no hardcoded secrets | unit | `python manage.py test core.tests.TestEnvironmentConfig -v2` | No -- Wave 0 |
| FOUND-02 | base.html renders with nav, footer | integration | `python manage.py test core.tests.TestBaseTemplate -v2` | No -- Wave 0 |
| FOUND-03 | Pages return 200, contain Bootstrap CSS link | integration | `python manage.py test core.tests.TestResponsiveLayout -v2` | No -- Wave 0 |
| FOUND-04 | Static files referenced in templates resolve to valid URLs | integration | `python manage.py test core.tests.TestStaticFiles -v2` | No -- Wave 0 |
| FOUND-05 | MEDIA_ROOT exists and is writable, media URL pattern configured | unit | `python manage.py test core.tests.TestMediaConfig -v2` | No -- Wave 0 |
| LEGAL-03 | Cookie banner HTML present in page response | integration | `python manage.py test core.tests.TestCookieBanner -v2` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `python manage.py test --verbosity=2`
- **Per wave merge:** `python manage.py test --verbosity=2`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] New Django app `core` (or test module) for foundation tests
- [ ] `core/tests.py` or `tests/test_foundation.py` -- covers FOUND-01 through FOUND-05, LEGAL-03
- [ ] No framework install needed (Django TestCase already available)

## Sources

### Primary (HIGH confidence)
- Current codebase: `backend/settings.py`, `backend/urls.py`, `requirements.txt`, `.gitignore` -- direct inspection
- django-environ 0.11.2 -- verified via `pip install --dry-run` and official docs
- Bootstrap 5.3.8 -- verified via getbootstrap.com/docs/versions/
- pyenv versions -- verified 3.11.11 available on machine

### Secondary (MEDIUM confidence)
- [django-environ quick start](https://django-environ.readthedocs.io/en/latest/quickstart.html) -- setup pattern
- [django-cookie-consent docs](https://django-cookie-consent.readthedocs.io/) -- evaluated and rejected for this use case
- [Google Fonts](https://fonts.google.com/) -- Lora + Nunito pairing for warm/natural kitchen vibe
- [BentoBox Design font pairings](https://medium.com/bentobox-design/font-pairings-our-favorite-google-fonts-for-restaurants-d157e4c5e5fd) -- restaurant/food font recommendations

### Tertiary (LOW confidence)
- Specific Bootstrap 5.3.8 CDN integrity hashes -- must be verified from official page at implementation time

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all packages verified, versions confirmed, codebase inspected
- Architecture: HIGH -- standard Django template patterns, well-documented in official docs
- Pitfalls: HIGH -- derived from direct inspection of current settings.py issues (hardcoded secrets, empty DIRS, en-us locale)

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (stable technologies, no fast-moving APIs)
