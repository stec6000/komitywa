# Phase 4: Shop - Research

**Researched:** 2026-04-01
**Domain:** Django session-based shopping cart, product catalog, checkout form
**Confidence:** HIGH

## Summary

Phase 4 delivers a product catalog with category filtering (reusing Phase 3 patterns), product detail pages, a session-based shopping cart, a checkout form (without payment integration), and Django admin for product management. The architecture closely mirrors the `recipes` app -- same card grid, filter pills, admin patterns, and function-based views.

The session-based cart (`request.session['cart']`) is a well-established Django pattern. No third-party cart library is needed -- the requirements are simple enough (add/remove/quantity) that a small Cart helper class stored in the session handles everything. A context processor provides the cart item count globally for the navbar badge.

**Primary recommendation:** Create a `shop` Django app following exact patterns from the `recipes` app. Use a Cart class that wraps `request.session` for cart operations. Add a context processor for the global cart count badge.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Cart stored in Django sessions (`request.session['cart']` as `{product_id: quantity}` dict). No CartItem database model needed.
- **D-02:** Guest checkout -- no login required. Checkout form collects email directly.
- **D-03:** Single `Product` model with a `type` field (`ebook` / `physical`). Same card and detail templates for both types.
- **D-04:** Ebooks show a "Cyfrowy" badge. Detail page shows delivery note: "Po zakupie ebook zostanie wyslany na Twoj email."
- **D-05:** Physical products show "Odbior osobisty" delivery note on the detail page.
- **D-06:** Ebook quantity in cart is fixed at 1. No quantity controls for ebook cart items. Physical products have normal quantity controls.
- **D-07:** Unified product grid with category filter pills -- consistent with Phase 3 recipe pattern. Categories: "Wszystkie | Ebooki | Dania w sloiku | Ciasta".
- **D-08:** Dedicated `/koszyk/` page. Navbar cart icon links to this page.
- **D-09:** Checkout form on `/zamowienie/`. Collects: email, imie i nazwisko, telefon (optional), data odbioru. Ends with placeholder "Przejdz do platnosci" button.
- **D-10:** LEGAL-04 compliance: two required checkboxes -- zgoda na przetwarzanie danych osobowych, akceptacja regulaminu.
- **D-11:** 3-column card grid, product cards show: photo (4:3), category badge, name, short description excerpt, price. Ebooks additionally show "Cyfrowy" badge.
- **D-12:** Warm personal Polish copy tone. Empty cart: "Twoj koszyk jest pusty -- zapraszamy do sklepu!"

### Claude's Discretion
- Exact `Product` model field names and admin fieldset layout
- Cart badge update mechanism (redirect with GET param recommended)
- Checkout form field validation details (phone format, date format)
- Specific stock photo selection for product placeholders

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SHOP-01 | Uzytkownik moze przegladac katalog produktow z kategoriami (ebooki, dania w sloiku, ciasta) | Product model with type field, ProductCategory model, filter pills pattern from recipes app |
| SHOP-02 | Uzytkownik moze otworzyc strone produktu ze zdjeciami, opisem i cena | Product detail view with slug URL, image, description, price, delivery note per type |
| SHOP-03 | Uzytkownik moze dodac produkty do koszyka | Session-based Cart class with add method, POST view for add-to-cart |
| SHOP-04 | Uzytkownik moze przegladac i edytowac zawartosc koszyka (zmiana ilosci, usuwanie) | Dedicated /koszyk/ page, update/remove POST actions, ebook quantity locked at 1 |
| SHOP-05 | Uzytkownik moze przejsc do zamowienia z formularzem danych | /zamowienie/ page with Django Form, Order model stub, LEGAL-04 checkboxes |
| SHOP-06 | Admin moze zarzadzac produktami (dodawac, edytowac, ukrywac) z panelu | ProductAdmin with @admin.register pattern, is_active field, prepopulated slug |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django | 5.2.12 | Web framework | Already installed, project stack |
| Pillow | 9.0.1 | Image processing for ImageField | Already installed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Bootstrap 5.3.3 | CDN | UI grid, forms, cards | Already loaded in base.html |
| Bootstrap Icons 1.11.3 | CDN | bi-cart3, bi-plus, bi-dash icons | Already loaded in base.html |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Session cart dict | django-carton, dj-shop-cart | Overkill for this simple use case; adds dependency for 50 lines of code |
| Manual Product model | django-oscar, saleor | Full e-commerce frameworks; massive overkill for 3 product categories |

**Installation:**
No new packages needed. All dependencies are already installed.

## Architecture Patterns

### Recommended Project Structure
```
shop/
    __init__.py
    admin.py
    apps.py
    cart.py           # Cart class wrapping session
    context_processors.py  # cart_count for navbar badge
    forms.py          # CheckoutForm
    models.py         # ProductCategory, Product, Order
    tests.py
    urls.py
    views.py
templates/
    shop/
        list.html     # Product catalog with filter pills
        detail.html   # Product detail page
        cart.html     # Cart contents page
        checkout.html # Checkout form page
```

### Pattern 1: Session-Based Cart Class
**What:** A `Cart` class that encapsulates all session manipulation for the shopping cart.
**When to use:** Every view that reads or modifies the cart.
**Example:**
```python
# shop/cart.py
from decimal import Decimal
from django.conf import settings


class Cart:
    """Session-based shopping cart."""

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get("cart", {})
        self.cart = cart

    def add(self, product, quantity=1):
        """Add product to cart or update quantity."""
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                "quantity": 0,
                "price": str(product.price),
            }
        if product.type == "ebook":
            self.cart[product_id]["quantity"] = 1  # D-06: fixed at 1
        else:
            self.cart[product_id]["quantity"] += quantity
        self.save()

    def remove(self, product_id):
        """Remove product from cart."""
        product_id = str(product_id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def update_quantity(self, product_id, quantity):
        """Update quantity for a product."""
        product_id = str(product_id)
        if product_id in self.cart and quantity > 0:
            self.cart[product_id]["quantity"] = quantity
            self.save()

    def save(self):
        self.session["cart"] = self.cart
        self.session.modified = True

    def __len__(self):
        """Total number of items in cart."""
        return sum(item["quantity"] for item in self.cart.values())

    def get_total_price(self):
        return sum(
            Decimal(item["price"]) * item["quantity"]
            for item in self.cart.values()
        )

    def clear(self):
        del self.session["cart"]
        self.session.modified = True
```

### Pattern 2: Context Processor for Cart Count
**What:** A context processor that injects `cart_count` into every template.
**When to use:** Register in `settings.py` TEMPLATES context_processors.
**Example:**
```python
# shop/context_processors.py
def cart_count(request):
    cart = request.session.get("cart", {})
    count = sum(item["quantity"] for item in cart.values())
    return {"cart_count": count}
```

Register in `backend/settings.py`:
```python
"context_processors": [
    # ... existing processors
    "shop.context_processors.cart_count",
],
```

### Pattern 3: Product Catalog View (mirrors recipe_list)
**What:** Function-based view with category filter pills using GET param `?kategoria=slug`.
**When to use:** Product list at `/sklep/`.
**Example:**
```python
# shop/views.py
def product_list(request):
    products = Product.objects.filter(is_active=True).select_related("category")
    active_category = request.GET.get("kategoria", "")
    if active_category:
        products = products.filter(category__slug=active_category)

    paginator = Paginator(products, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    categories = ProductCategory.objects.all()
    return render(request, "shop/list.html", {
        "page_obj": page_obj,
        "categories": categories,
        "active_category": active_category,
    })
```

### Pattern 4: Add-to-Cart POST View
**What:** POST-only view that adds a product to the session cart and redirects back.
**When to use:** Form submit from product detail page or catalog card.
**Example:**
```python
# shop/views.py
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .cart import Cart
from .models import Product


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = Cart(request)
    cart.add(product)
    return redirect("shop:cart")
```

### Pattern 5: Checkout Form with LEGAL-04 Compliance
**What:** Django Form with email, name, phone, pickup date, and two required consent checkboxes.
**When to use:** `/zamowienie/` checkout page.
**Example:**
```python
# shop/forms.py
from django import forms


class CheckoutForm(forms.Form):
    email = forms.EmailField(label="Adres email")
    name = forms.CharField(max_length=200, label="Imie i nazwisko")
    phone = forms.CharField(
        max_length=20, required=False, label="Telefon (opcjonalnie)"
    )
    pickup_date = forms.CharField(
        max_length=100,
        label="Preferowana data odbioru",
        help_text="np. piatek 10 stycznia, godziny popoludniowe",
    )
    consent_data = forms.BooleanField(
        label="Wyrazam zgode na przetwarzanie moich danych osobowych"
              " w celu realizacji zamowienia",
    )
    consent_terms = forms.BooleanField(
        label="Akceptuje regulamin sklepu",
    )
```

### Anti-Patterns to Avoid
- **Storing cart in a database model before checkout:** D-01 explicitly locks cart to session only. No CartItem model.
- **Using AJAX for cart operations:** D-08 says keep it simple with redirects. No JavaScript fetch for cart updates.
- **Separate templates per product type:** D-03 says same card and detail templates for both ebook and physical. Use `{% if product.type == 'ebook' %}` conditionals.
- **Requiring login for cart/checkout:** D-02 explicitly says guest checkout, no login required.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Session management | Custom cookie handling | Django sessions (`request.session`) | Already configured, handles serialization, expiry, security |
| Form validation | Manual POST parsing | Django Forms (`forms.Form`) | CSRF protection, field validation, error rendering built-in |
| Image handling | Manual file upload | Django `ImageField` + Pillow | Already installed, handles upload path, validation |
| Pagination | Manual offset/limit | Django `Paginator` | Already used in recipes, handles edge cases |
| Slug generation | Manual URL-safe strings | `slugify()` + `prepopulated_fields` | Already used in recipes, handles Unicode |
| CSRF protection | Manual token generation | `{% csrf_token %}` in forms | Already enabled via CsrfViewMiddleware |

**Key insight:** This phase is almost entirely composed of patterns already established in the `recipes` app. The cart is the only genuinely new pattern, and it is a well-documented Django session pattern.

## Common Pitfalls

### Pitfall 1: session.modified Not Set After Mutation
**What goes wrong:** Cart changes do not persist across requests.
**Why it happens:** Django only saves the session if `request.session` was directly assigned. Mutating a nested dict inside the session does not trigger auto-save.
**How to avoid:** Always call `self.session.modified = True` after changing cart contents, or re-assign the dict: `self.session["cart"] = self.cart`.
**Warning signs:** Cart appears empty after redirect.

### Pitfall 2: Product ID Type Mismatch (int vs str)
**What goes wrong:** Product appears added but cannot be found in cart, or duplicates appear.
**Why it happens:** Session serializes dict keys as strings. Code may compare `int(product.id)` against `str(product_id)` from session.
**How to avoid:** Always convert product ID to `str()` when using as cart dict key. Be consistent in all cart methods.
**Warning signs:** Cart shows wrong item count, or same product added twice.

### Pitfall 3: Price Stored as Float in Session
**What goes wrong:** Rounding errors in cart totals (e.g., 29.990000000000002).
**Why it happens:** JSON serialization converts `Decimal` to `float`.
**How to avoid:** Store price as `str` in session, convert back to `Decimal` when calculating totals. Use `DecimalField` on the Product model.
**Warning signs:** Prices display with excessive decimal places.

### Pitfall 4: Missing CSRF Token on POST Forms
**What goes wrong:** 403 Forbidden when submitting add-to-cart or checkout form.
**Why it happens:** Forgetting `{% csrf_token %}` in the form template.
**How to avoid:** Every `<form method="post">` must include `{% csrf_token %}`.
**Warning signs:** 403 on any POST submission.

### Pitfall 5: Stale Product Data in Cart Session
**What goes wrong:** Cart shows old price after admin changes product price.
**Why it happens:** Price was stored in session at add-time and never refreshed.
**How to avoid:** When rendering the cart page, fetch current product data from DB and use live prices. Only use session for product_id and quantity. Store price in session for calculation convenience but always refresh from DB on cart view.
**Warning signs:** Cart total does not match current product prices.

### Pitfall 6: Deleted Product Still in Cart
**What goes wrong:** KeyError or 404 when rendering cart after admin deletes or hides a product.
**Why it happens:** Cart session still holds the product_id but Product no longer exists or is_active=False.
**How to avoid:** In cart view, filter products by `id__in=cart_ids, is_active=True`. Silently remove stale entries from session.
**Warning signs:** Cart page crashes or shows ghost items.

### Pitfall 7: Ebook Added Multiple Times
**What goes wrong:** User adds same ebook twice, cart shows quantity 2.
**Why it happens:** D-06 says ebook quantity is fixed at 1 but add logic does not enforce it.
**How to avoid:** In `Cart.add()`, check `product.type == "ebook"` and hard-set quantity to 1 regardless of input.
**Warning signs:** Ebook in cart with quantity > 1.

## Code Examples

### Product Model
```python
# shop/models.py
from django.db import models
from django.utils.text import slugify


class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Kategoria produktu"
        verbose_name_plural = "Kategorie produktow"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    TYPE_CHOICES = [
        ("ebook", "Ebook"),
        ("physical", "Produkt fizyczny"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default="physical",
    )
    description = models.TextField(
        help_text="Krotki opis (1-2 zdania) -- wyswietlany na karcie"
    )
    full_description = models.TextField(
        blank=True,
        help_text="Pelny opis -- wyswietlany na stronie produktu"
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Cena w PLN",
    )
    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True,
        help_text="Zdjecie produktu",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produkt"
        verbose_name_plural = "Produkty"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
```

### Order Stub Model (for checkout form persistence)
```python
# shop/models.py (continued)
class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Oczekujace na platnosc"),
        ("paid", "Oplacone"),
        ("completed", "Zrealizowane"),
        ("cancelled", "Anulowane"),
    ]

    email = models.EmailField()
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    pickup_date = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    total = models.DecimalField(max_digits=10, decimal_places=2)
    cart_snapshot = models.JSONField(
        help_text="Kopia koszyka w momencie zamowienia"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Zamowienie"
        verbose_name_plural = "Zamowienia"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Zamowienie #{self.id} - {self.email}"
```

### Navbar Cart Badge (updated _navbar.html)
```html
{# Replace the hardcoded badge count with context processor variable #}
<a class="nav-link position-relative ms-3" href="{% url 'shop:cart' %}" aria-label="Koszyk">
    <i class="bi bi-cart3"></i>
    <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill kk-badge {% if not cart_count %}kk-badge-dim{% endif %}">
        {{ cart_count|default:"0" }}
    </span>
</a>
```

### Product Card Template (adapted from kk-recipe-card)
```html
<div class="card h-100 kk-product-card">
    <div class="kk-product-card__img-wrapper">
        {% if product.image %}
        <img src="{{ product.image.url }}" alt="{{ product.title }}" class="kk-product-card__img">
        {% else %}
        <div class="kk-product-card__img-placeholder">
            <i class="bi bi-image" aria-hidden="true"></i>
        </div>
        {% endif %}
        {% if product.category %}
        <span class="kk-category-badge">{{ product.category.name }}</span>
        {% endif %}
        {% if product.type == "ebook" %}
        <span class="kk-badge kk-badge-digital">Cyfrowy</span>
        {% endif %}
    </div>
    <div class="card-body d-flex flex-column">
        <h3 class="card-title">{{ product.title }}</h3>
        <p class="card-text flex-grow-1">{{ product.description|truncatechars:120 }}</p>
        <div class="d-flex justify-content-between align-items-center mt-auto">
            <span class="kk-price">{{ product.price }} zl</span>
            <a href="{% url 'shop:detail' slug=product.slug %}" class="kk-link-arrow">Zobacz wiecej &rarr;</a>
        </div>
    </div>
</div>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Database-backed cart model | Session cart for simple stores | Django 1.x+ | Simpler for guest checkout, no user model dependency |
| Cookie-based cart | Session-based (server-side) | Standard practice | More secure, larger capacity, no client-side manipulation |
| django-carton library | Custom Cart class | Library last updated 2020 | Better to own 50 lines than depend on unmaintained package |

**Deprecated/outdated:**
- `django-cart` package: Last PyPI release is old. Not recommended.
- `django-carton`: Last commit 2020. Use custom Cart class instead.
- `django-oscar` / `saleor`: Full e-commerce frameworks -- massively overscoped for this project.

## Open Questions

1. **Order model scope for Phase 4 vs Phase 5**
   - What we know: D-09 says checkout form ends with placeholder button. Phase 5 wires payment.
   - What's unclear: Should Phase 4 create the Order model and save order stubs, or should the form just render without persistence?
   - Recommendation: Create the Order model in Phase 4 and save the order stub on form submit. This gives Phase 5 a clean starting point -- it just needs to add payment status updates. The checkout view saves the order, clears the cart, and shows a "Czekamy na platnosc" placeholder page.

2. **Product categories: separate model vs choices field**
   - What we know: D-07 lists fixed categories: "Ebooki | Dania w sloiku | Ciasta"
   - What's unclear: Whether categories will expand in the future.
   - Recommendation: Use a `ProductCategory` model (like `recipes.Category`) for consistency and admin flexibility. Pre-populate with the three required categories via data migration.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Django TestCase (built-in unittest) |
| Config file | manage.py (DJANGO_SETTINGS_MODULE=backend.settings) |
| Quick run command | `python3 manage.py test shop -v2 --failfast` |
| Full suite command | `python3 manage.py test -v2` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SHOP-01 | Product catalog with category filter | unit | `python3 manage.py test shop.tests.TestProductList -v2 --failfast` | Wave 0 |
| SHOP-02 | Product detail page with image/desc/price | unit | `python3 manage.py test shop.tests.TestProductDetail -v2 --failfast` | Wave 0 |
| SHOP-03 | Add product to cart | unit | `python3 manage.py test shop.tests.TestCartAdd -v2 --failfast` | Wave 0 |
| SHOP-04 | View/edit cart contents | unit | `python3 manage.py test shop.tests.TestCartView -v2 --failfast` | Wave 0 |
| SHOP-05 | Checkout form with required fields | unit | `python3 manage.py test shop.tests.TestCheckout -v2 --failfast` | Wave 0 |
| SHOP-06 | Admin product management | unit | `python3 manage.py test shop.tests.TestProductAdmin -v2 --failfast` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python3 manage.py test shop -v2 --failfast`
- **Per wave merge:** `python3 manage.py test -v2`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `shop/tests.py` -- all test classes for SHOP-01 through SHOP-06
- [ ] `shop/` app directory -- does not exist yet, needs `startapp`

## Sources

### Primary (HIGH confidence)
- Existing codebase: `recipes/` app patterns (models, views, admin, tests, templates)
- Existing codebase: `static/css/main.css` CSS component classes
- Existing codebase: `backend/settings.py` session and template configuration
- Existing codebase: `templates/includes/_navbar.html` cart badge markup

### Secondary (MEDIUM confidence)
- [Django Sessions Concept and Implementation](https://www.linkedin.com/pulse/django-sessions-concept-implementation-making-shopping-junpeng-he) - session cart pattern
- [Django 2 by Example - Storing carts in sessions](https://www.oreilly.com/library/view/django-2-by/9781788472487/919897f5-4193-470b-9e22-765eb831ef01.xhtml) - Cart class pattern
- [Django Context Processors](https://dev.to/sarahhudaib/context-processors-in-django-15h2) - context processor pattern
- [Django Context Processors Guide](https://dpenedo.com/posts/django-context-and-making-it-global-with-context-processors/) - global context patterns

### Tertiary (LOW confidence)
None -- all patterns are well-established Django patterns with official documentation backing.

## Project Constraints (from CLAUDE.md)

- **Stack**: Django 5.2 + Django templates (no SPA)
- **Language**: Polish only -- all UI text in Polish
- **Delivery**: Ebooks via email (PDF), physical products pickup only
- **Naming**: `snake_case` for modules, `PascalCase` for classes, `Model + Admin/Form/Serializer` suffix
- **Strings**: Double quotes for all new string literals
- **Views**: Function-based views (no CBVs -- project convention)
- **Admin**: `@admin.register(Model)` decorator pattern
- **Imports**: Relative within app, absolute for cross-app
- **Models**: `__str__` on all models, `BigAutoField` default PK

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new dependencies needed, all patterns from existing codebase
- Architecture: HIGH - direct adaptation of recipes app patterns + well-documented Django session cart
- Pitfalls: HIGH - well-known Django session pitfalls, documented in multiple sources

**Research date:** 2026-04-01
**Valid until:** 2026-05-01 (stable Django patterns, no fast-moving dependencies)
