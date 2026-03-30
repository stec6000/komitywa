# Stack Research

**Domain:** Vegan food business website (Django e-commerce + blog + newsletter)
**Researched:** 2026-03-30
**Confidence:** HIGH

## Recommended Stack

### Core Technologies (Already In Place)

| Technology | Version | Purpose | Status |
|------------|---------|---------|--------|
| Django | 5.2.x | Web framework | Existing |
| Django REST Framework | latest | API layer (keep for admin/future mobile) | Existing |
| django-allauth | latest | Authentication, email verification | Existing |
| dj-rest-auth | latest | REST auth endpoints | Existing |
| drf-spectacular | latest | API documentation | Existing |
| django-cors-headers | latest | CORS handling | Existing |
| python-dotenv | latest | Environment variables (unused, needs setup) | Existing (unconfigured) |

### New Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| django-oscar | 3.2.x | E-commerce framework | Full-featured Django e-commerce: catalog, basket, checkout, order management. Best maintained Django e-commerce package. |
| django-oscar-przelewy24 or custom | - | Przelewy24 payment gateway | Oscar has payment plugin architecture; Przelewy24 may need custom plugin via their REST API |
| Pillow | 10.x | Image processing | Required for recipe photos, product images, ebook covers. Django ImageField dependency. |
| django-ckeditor-5 or django-tinymce | latest | Rich text editor | Recipe content, product descriptions, blog posts need WYSIWYG editing in admin |
| django-mailchimp-v1.3 or django-newsletter | latest | Newsletter management | Subscriber collection, campaign management, email sending |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| easy-thumbnails | 2.9+ | Image thumbnails | Recipe cards, product listings, responsive images |
| django-meta | 2.4+ | SEO meta tags | All public pages need proper meta tags, Open Graph |
| django-sitemaps | built-in | XML sitemap | SEO: recipe pages, product pages, blog posts |
| django-compressor | 4.x | CSS/JS compression | Production asset optimization |
| django-htmx | 1.x | Interactive UI without JS framework | Dynamic filtering, cart updates, search-as-you-type |
| weasyprint or xhtml2pdf | latest | PDF generation | Ebook delivery (if generating PDFs) |
| celery + redis | 5.x | Async task queue | Email sending, order processing, newsletter dispatch |
| django-crispy-forms | 2.x | Form rendering | Checkout forms, newsletter signup, contact forms |
| crispy-bootstrap5 | 2024.x | Bootstrap 5 form templates | Crispy forms with Bootstrap 5 styling |

### Frontend Stack

| Technology | Purpose | Notes |
|------------|---------|-------|
| Bootstrap 5 | CSS framework | Responsive, mobile-first, good component library |
| htmx | Dynamic interactions | Cart updates, search, filters without full SPA |
| Alpine.js (optional) | Lightweight JS | Dropdowns, modals, toggles if htmx not enough |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| django-debug-toolbar | Development debugging | SQL queries, templates, cache analysis |
| django-extensions | Management commands | shell_plus, runserver_plus, show_urls |
| black | Code formatting | Consistent Python style |
| ruff | Linting | Fast Python linter |
| pre-commit | Git hooks | Run linting/formatting before commits |

## Installation

```bash
# Core e-commerce
pip install django-oscar Pillow

# Rich text
pip install django-ckeditor-5

# Newsletter
pip install django-newsletter  # or mailchimp integration

# Frontend enhancements
pip install django-htmx django-crispy-forms crispy-bootstrap5

# Images & SEO
pip install easy-thumbnails django-meta

# Asset management
pip install django-compressor

# Async tasks
pip install celery redis

# Dev tools
pip install django-debug-toolbar django-extensions black ruff pre-commit
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| django-oscar | Saleor | If you want GraphQL-first headless e-commerce (overkill for Django templates) |
| django-oscar | django-shop | If oscar is too heavy; django-shop is lighter but less maintained |
| django-oscar | Custom models | If only selling 2-3 product types with simple checkout (consider for v1 simplicity) |
| Bootstrap 5 | Tailwind CSS | If you prefer utility-first CSS; requires build step |
| htmx | Alpine.js only | If interactions are purely client-side (no server roundtrips) |
| celery | django-q2 | If you want simpler async without Redis dependency |
| django-newsletter | Mailchimp API | If you want hosted newsletter with analytics (external dependency) |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| React/Vue/Angular | Overkill for content site; hurts SEO; decision already made for Django templates | htmx + Alpine.js for interactivity |
| Saleor | GraphQL headless e-commerce, doesn't integrate with Django templates | django-oscar or custom models |
| django-shop | Poorly maintained, last significant update was years ago | django-oscar or custom |
| Stripe alone | User chose Przelewy24 for Polish market (BLIK, local banks) | Przelewy24 API integration |
| SendGrid/Mailgun for newsletter | Adds external dependency; django-newsletter or Mailchimp is better fit | django-newsletter or Mailchimp |

## Key Decision: Oscar vs Custom E-commerce

For this project with only 2 product types (ebooks + physical products) and simple checkout:

**Option A: django-oscar** — Full e-commerce framework, handles catalog, basket, checkout, orders out of the box. Pros: battle-tested, extensible. Cons: heavy for simple needs, learning curve.

**Option B: Custom models** — Build Product, Order, Cart models from scratch. Pros: lightweight, exactly what you need. Cons: more code to write, must handle edge cases yourself.

**Recommendation:** Start with custom models for v1 (simpler, fewer dependencies, faster to build for 2 product types). Migrate to Oscar if catalog grows complex.

## Sources

- Django Oscar documentation (django-oscar.readthedocs.io)
- Przelewy24 REST API documentation (developers.przelewy24.pl)
- Django packages ecosystem review
- htmx documentation (htmx.org)

---
*Stack research for: vegan food business website*
*Researched: 2026-03-30*
