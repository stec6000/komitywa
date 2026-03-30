# Architecture Research

**Domain:** Vegan food business website (Django e-commerce + blog + newsletter)
**Researched:** 2026-03-30
**Confidence:** HIGH

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Django Templates (Frontend)               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Landing  │ │ Recipes  │ │  Shop    │ │Newsletter│       │
│  │  Page    │ │  Blog    │ │ +Cart    │ │  Signup  │       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │
│       │            │            │            │              │
├───────┴────────────┴────────────┴────────────┴──────────────┤
│                    Django Views Layer                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  pages   │ │ recipes  │ │   shop   │ │newsletter│       │
│  │  views   │ │  views   │ │  views   │ │  views   │       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │
│       │            │            │            │              │
├───────┴────────────┴────────────┴────────────┴──────────────┤
│                    Django Models Layer                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ accounts │ │ recipes  │ │   shop   │ │newsletter│       │
│  │ (exists) │ │ (new)    │ │  (new)   │ │  (new)   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                    External Services                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                     │
│  │Przelewy24│ │  Email   │ │  Media   │                     │
│  │ Payments │ │  (SMTP)  │ │ Storage  │                     │
│  └──────────┘ └──────────┘ └──────────┘                     │
└──────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | Implementation |
|-----------|----------------|----------------|
| accounts (existing) | User auth, registration, login, password reset | Keep existing allauth + dj-rest-auth; add session-based auth for templates |
| pages | Static/semi-static pages: landing, about, contact | Django views + templates, minimal models (maybe for team members, testimonials) |
| recipes | Recipe CRUD, categories, tags, search, Schema.org markup | Recipe model with ingredients, steps, times; Category/Tag models; full-text search |
| shop | Product catalog, cart, checkout, orders, ebook delivery | Product model (base + Ebook/PhysicalProduct), Cart/CartItem, Order/OrderItem models |
| newsletter | Subscriber management, signup forms | Subscriber model, signup view, integration with email backend or external service |
| payments | Przelewy24 integration, payment verification, webhooks | Payment model, P24 API client, webhook handler, payment status tracking |

## Recommended Project Structure

```
komitywa/
├── accounts/              # Existing — user auth
│   ├── models.py          # Custom User model (keep)
│   ├── views.py           # Add template-based login/register views
│   ├── serializers.py     # Keep for API
│   └── templates/
│       └── accounts/      # Login, register, profile templates
├── pages/                 # NEW — static pages
│   ├── views.py           # Landing, about, contact views
│   └── templates/
│       └── pages/         # landing.html, about.html, contact.html
├── recipes/               # NEW — recipe blog
│   ├── models.py          # Recipe, Category, Tag, Ingredient
│   ├── views.py           # List, detail, search, by-category
│   ├── admin.py           # Recipe admin with inline ingredients/steps
│   └── templates/
│       └── recipes/       # list.html, detail.html, category.html
├── shop/                  # NEW — e-commerce
│   ├── models.py          # Product, Ebook, PhysicalProduct, Cart, Order
│   ├── views.py           # Catalog, cart, checkout, order confirmation
│   ├── payments.py        # Przelewy24 API integration
│   ├── admin.py           # Product/order management
│   └── templates/
│       └── shop/          # product_list.html, cart.html, checkout.html
├── newsletter/            # NEW — newsletter
│   ├── models.py          # Subscriber
│   ├── views.py           # Subscribe, unsubscribe, confirm
│   └── templates/
│       └── newsletter/    # signup form partial, confirmation
├── templates/             # Global templates
│   ├── base.html          # Base layout (nav, footer, Bootstrap)
│   ├── includes/          # Reusable partials (nav, footer, newsletter widget)
│   └── errors/            # 404.html, 500.html
├── static/                # Static assets
│   ├── css/               # Custom CSS (Bootstrap overrides)
│   ├── js/                # htmx, Alpine.js, custom JS
│   └── images/            # Brand assets, icons
├── media/                 # User uploads (recipe photos, product images)
├── backend/               # Existing — Django project config
│   ├── settings.py        # Update with new apps, media config
│   ├── urls.py            # Add new app URL patterns
│   └── ...
└── manage.py
```

## Architectural Patterns

### Pattern 1: Django MTV (Model-Template-View)

**What:** Standard Django pattern — models define data, views handle logic, templates render HTML.
**When to use:** All pages — landing, recipes, shop, newsletter.
**Trade-offs:** Simple, well-documented, great for SEO. Less interactive than SPA but htmx bridges the gap.

### Pattern 2: Template Inheritance

**What:** Base template with blocks; child templates extend and override blocks.
**When to use:** Every page. base.html defines layout, nav, footer. Page templates fill content blocks.

```html
<!-- base.html -->
{% block content %}{% endblock %}
{% block extra_js %}{% endblock %}

<!-- recipes/detail.html -->
{% extends "base.html" %}
{% block content %}
  <article>{{ recipe.title }}</article>
{% endblock %}
```

### Pattern 3: htmx for Dynamic Interactions

**What:** Server-rendered HTML fragments swapped into the page via AJAX.
**When to use:** Cart add/remove, recipe search, newsletter signup, product filtering.
**Trade-offs:** No JS framework needed; server does the work. Slightly more server load per interaction.

```html
<button hx-post="/shop/cart/add/{{ product.id }}/"
        hx-target="#cart-count"
        hx-swap="innerHTML">
  Dodaj do koszyka
</button>
```

### Pattern 4: Model Inheritance for Products

**What:** Base Product model with Ebook and PhysicalProduct subtypes.
**When to use:** Shop models — shared fields (name, price, description) on base, specific fields on subtypes.

```python
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to='products/')

class Ebook(Product):
    pdf_file = models.FileField(upload_to='ebooks/')
    page_count = models.PositiveIntegerField()

class PhysicalProduct(Product):
    pickup_instructions = models.TextField()
    available_quantity = models.PositiveIntegerField()
```

## Data Flow

### Recipe Browsing

```
User visits /przepisy/
    ↓
recipes.views.RecipeListView → Recipe.objects.filter(published=True)
    ↓
Template renders recipe cards with thumbnails
    ↓
User clicks recipe → /przepisy/slug/
    ↓
recipes.views.RecipeDetailView → Recipe with ingredients, steps
    ↓
Template renders full recipe + Schema.org JSON-LD
```

### Purchase Flow

```
User browses /sklep/
    ↓
shop.views.ProductListView → Products by category (ebooks, dania, ciasta)
    ↓
User adds to cart (htmx POST) → shop.views.cart_add
    ↓
Cart stored in session (anonymous) or DB (logged in)
    ↓
User goes to /sklep/koszyk/ → shop.views.CartView
    ↓
User proceeds to /sklep/zamowienie/ → shop.views.CheckoutView
    ↓
Form: email, name, pickup preference (for physical products)
    ↓
Payment redirect → Przelewy24 API (register transaction)
    ↓
User pays on P24 → P24 sends webhook to /sklep/p24/webhook/
    ↓
shop.payments.verify_payment → Order.status = 'paid'
    ↓
If ebook: send PDF to email (Celery task)
If physical: mark for pickup preparation
    ↓
Redirect to /sklep/zamowienie/potwierdzenie/
```

### Newsletter Signup

```
User fills email in footer widget (on every page)
    ↓
htmx POST → newsletter.views.subscribe
    ↓
Create Subscriber(email, confirmed=False)
    ↓
Send confirmation email (Celery task)
    ↓
User clicks link → newsletter.views.confirm → confirmed=True
```

## Migration Strategy: API-only → Templates

The existing backend is API-only. To add Django templates:

1. **Keep existing API endpoints** — they work and can serve future mobile app
2. **Add `SessionAuthentication`** as primary for template views (already configured in DRF settings)
3. **Add allauth template views** alongside REST auth — allauth already has built-in templates
4. **Configure `TEMPLATES` setting** — add template dirs, context processors
5. **Add `django.contrib.staticfiles`** — for serving static assets in development
6. **Keep accounts app dual-purpose** — REST API for external clients, template views for web users

### Build Order (Dependencies)

```
Phase 1: Foundation & Templates Setup
    ├── base.html, static files, Bootstrap
    ├── Settings update (templates, static, media)
    └── Template-based auth (allauth templates)

Phase 2: Landing Page & Static Pages
    ├── pages app
    └── Brand identity / CSS theme

Phase 3: Recipe Blog
    ├── recipes app (models, views, templates)
    ├── Admin interface for recipe management
    └── SEO (Schema.org, sitemap)

Phase 4: Shop & Products
    ├── shop app (product models, catalog views)
    ├── Cart (session-based)
    └── Product admin

Phase 5: Payments & Orders
    ├── Przelewy24 integration
    ├── Order model & checkout flow
    ├── Ebook email delivery
    └── Order management admin

Phase 6: Newsletter
    ├── newsletter app
    ├── Subscriber model & confirmation flow
    └── Footer widget on all pages

Phase 7: Polish & Production
    ├── SEO optimization
    ├── Performance (image optimization, caching)
    ├── Security hardening
    └── Production deployment config
```

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Przelewy24 | REST API + webhooks | Register transaction → redirect → webhook verification. Sandbox available for testing. |
| SMTP (email) | Django email backend | Ebook delivery, newsletter confirmation, order confirmation, password reset |
| Media storage | Local filesystem (dev) / S3 (prod) | Recipe photos, product images, ebook PDFs |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| accounts ↔ shop | Foreign key (User → Order) | Orders linked to users, guest checkout via email |
| recipes ↔ shop | Loose (no FK) | Recipes can link to ebook products via slug/manual reference |
| shop ↔ payments | Direct import | payments.py is part of shop app, handles P24 API |
| newsletter ↔ accounts | Independent | Newsletter subscribers != registered users (separate model) |

## Sources

- Django documentation (djangoproject.com)
- Przelewy24 developer docs (developers.przelewy24.pl)
- htmx documentation (htmx.org)
- Django e-commerce patterns (various community resources)

---
*Architecture research for: vegan food business website*
*Researched: 2026-03-30*
