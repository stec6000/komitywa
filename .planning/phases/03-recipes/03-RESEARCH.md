# Phase 3: Recipes - Research

**Researched:** 2026-03-31
**Domain:** Django recipe blog — models, views, templates, search, Schema.org JSON-LD
**Confidence:** HIGH

## Summary

Phase 3 introduces the first Django models and migrations in this project, creating a `recipes` app with `Category` and `Recipe` models, function-based views for list and detail pages, URL namespace `recipes:`, and Django admin management. The architecture is a classic Django blog pattern: model → queryset → view → template, with no external dependencies beyond Pillow (already installed at 9.0.1).

The recipe list page uses a 3-column Bootstrap card grid with URL-based category filtering (a `?kategoria=slug` GET parameter filters the queryset). Search uses a GET form submitting `?q=` with Django ORM `Q` objects across `title` and `ingredients` fields. Pagination uses Django's built-in `Paginator` (8–12 recipes per page). Schema.org JSON-LD is rendered inline in the `{% block extra_js %}` of the recipe detail template — no external library needed.

The single open design decision is **ingredient storage**: structured rows (separate `Ingredient` model with inline admin) vs. free-text textarea. Research recommends a simple `TextField` for ingredients and a `TextField` for steps, with one `Ingredient` model only if future per-ingredient features (scaling, shopping list) are needed. For v1 a single `ingredients_text` + `steps_text` field approach is faster to build, easier to admin, and sufficient for Schema.org markup.

**Primary recommendation:** Create a standalone `recipes` Django app with `Category` and `Recipe` models, function-based views, URL namespace, and inline-free admin. Use `ImageField` for photos (Pillow installed). Render Schema.org JSON-LD as a `<script type="application/ld+json">` tag in the detail template.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** 3-column card grid (Bootstrap col-lg-4, col-md-6, col-12)
- **D-02:** Each card shows: photo thumbnail, category badge, title, short description (1-2 sentence excerpt), prep time (⏱ 30 min)
- **D-03:** Category filter bar at top — horizontal row of clickable pills: "Wszystkie | Śniadania | Obiady | Desery | Przekąski" (+ any other categories). Active pill highlighted in brand olive/sage color.

### Claude's Discretion
- Exact category list (admin-managed or hardcoded — pick what fits a small site best)
- Pagination vs load-more (standard Django paginator recommended)
- Recipe detail page layout (full-width or constrained column)
- Search implementation approach (form submit vs AJAX — simple form submit fine for v1)
- Ingredient storage (structured rows vs textarea — researcher should evaluate Django admin UX tradeoff)
- Difficulty field inclusion (not requested — omit unless needed for admin)
- Image storage (local media/ upload via Django FileField)
- Slug generation for recipe URLs

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.

v2 deferred (from REQUIREMENTS.md): print view, social sharing, suggested recipes, serving-size scaling.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PRZE-01 | Użytkownik może przeglądać listę przepisów z miniaturkami | Recipe list view with card grid, ImageField thumbnails, Paginator |
| PRZE-02 | Użytkownik może otworzyć pełny przepis ze zdjęciami, składnikami, krokami i czasem przygotowania | Recipe detail view with full content fields; ImageField for photos |
| PRZE-03 | Użytkownik może filtrować przepisy według kategorii | Category model, GET param `?kategoria=`, queryset filter, active pill CSS |
| PRZE-04 | Użytkownik może wyszukiwać przepisy po tytule i składnikach | GET form with `?q=`, Q objects on `title` + `ingredients_text` |
| PRZE-05 | Strona przepisu zawiera Schema.org JSON-LD markup (rich snippets w Google) | `<script type="application/ld+json">` in detail template with Recipe schema |
| PRZE-06 | Admin może dodawać, edytować i usuwać przepisy z panelu administracyjnego | `@admin.register(Recipe)` with list_display, search_fields, image preview |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django | 5.2.12 (installed) | Models, views, URLs, admin, ORM | Already in project |
| Pillow | 9.0.1 (installed) | `ImageField` image storage and validation | Required by Django ImageField; already installed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Django Paginator | built-in | Page through recipe list | Always — standard Django pattern |
| Django Q objects | built-in | Full-text search across multiple fields | Search (PRZE-04) |
| `django.utils.text.slugify` | built-in | Auto-generate URL slugs from titles | Slug generation in `save()` |
| `mark_safe` / `json` | built-in | Serialize JSON-LD dict for template | Schema.org output |

No new pip packages required for this phase.

**Installation:** Nothing to install — Pillow is already present.

**Version verification:** `pip3 show pillow` → 9.0.1. `pip3 show django` → 5.2.12.

---

## Architecture Patterns

### Recommended Project Structure

```
recipes/
├── __init__.py
├── apps.py
├── admin.py
├── models.py
├── views.py
├── urls.py
├── tests.py
└── migrations/
    └── 0001_initial.py

templates/
└── recipes/
    ├── list.html
    └── detail.html

static/
└── css/
    └── main.css      (append recipe-specific CSS classes)

media/
└── recipes/          (uploaded images land here; .gitkeep already present)
```

### Pattern 1: Separate `recipes` App with URL Namespace

**What:** Create `recipes/` as a standalone Django app, register in `INSTALLED_APPS`, and include its URLs under `/przepisy/` with `namespace="recipes"`.

**When to use:** Any time a feature group has its own models — the recipes app is self-contained.

**Example:**

```python
# backend/urls.py — add this line
path("przepisy/", include("recipes.urls", namespace="recipes")),
```

```python
# recipes/urls.py
from django.urls import path
from . import views

app_name = "recipes"

urlpatterns = [
    path("", views.recipe_list, name="list"),
    path("<slug:slug>/", views.recipe_detail, name="detail"),
]
```

This enables `{% url 'recipes:list' %}` and `{% url 'recipes:detail' slug=recipe.slug %}` in templates — consistent with established pattern in `core/urls.py`.

### Pattern 2: Recipe and Category Models

**What:** `Category` (name, slug) + `Recipe` (ForeignKey to Category, all content fields).

**Recommended model design (full fields):**

```python
# recipes/models.py
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Kategoria"
        verbose_name_plural = "Kategorie"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recipes",
    )
    description = models.TextField(help_text="Krótki opis (1-2 zdania) — wyświetlany na karcie")
    ingredients_text = models.TextField(help_text="Składniki — każdy w nowej linii")
    steps_text = models.TextField(help_text="Kroki przygotowania — każdy w nowej linii")
    prep_time = models.PositiveSmallIntegerField(
        help_text="Czas przygotowania w minutach"
    )
    image = models.ImageField(
        upload_to="recipes/",
        blank=True,
        null=True,
        help_text="Zdjęcie przepisu",
    )
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Przepis"
        verbose_name_plural = "Przepisy"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
```

**Ingredient storage decision (Claude's Discretion):**
Recommendation is `ingredients_text = TextField`. Reasoning:

- v1 has no per-ingredient features (no scaling, no shopping list)
- A separate `Ingredient` model with inline admin adds 2x model complexity and a migration with no user-visible benefit in v1
- Schema.org `recipeIngredient` expects a list — split `ingredients_text` by newlines in the template/view, no extra model needed
- Admin UX: a single textarea is faster to use than managing inline rows for a small shop owner entering 10-15 ingredients

If Phase 5+ needs scaling, migrate to structured rows then. This is not a locked decision — it is a recommendation under Claude's Discretion.

### Pattern 3: Recipe List View with Filtering and Search

**What:** Single function-based view handles list, category filter, and search together.

```python
# recipes/views.py
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Category, Recipe

RECIPES_PER_PAGE = 9  # 3 columns × 3 rows


def recipe_list(request):
    recipes = Recipe.objects.filter(is_published=True).select_related("category")
    categories = Category.objects.all()

    # Category filter — GET param ?kategoria=<slug>
    active_category = request.GET.get("kategoria", "")
    if active_category:
        recipes = recipes.filter(category__slug=active_category)

    # Search — GET param ?q=<term>
    query = request.GET.get("q", "").strip()
    if query:
        recipes = recipes.filter(
            Q(title__icontains=query) | Q(ingredients_text__icontains=query)
        )

    paginator = Paginator(recipes, RECIPES_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "recipes/list.html", {
        "page_obj": page_obj,
        "categories": categories,
        "active_category": active_category,
        "query": query,
    })


def recipe_detail(request, slug):
    recipe = get_object_or_404(Recipe, slug=slug, is_published=True)
    return render(request, "recipes/detail.html", {"recipe": recipe})
```

**Why `select_related("category")`:** Avoids N+1 queries when rendering each card's category badge.

### Pattern 4: Category Filter Pills (Template)

**What:** Bootstrap pill buttons as anchor tags with `?kategoria=` GET params. Active state applied when current URL param matches.

```html
<!-- In recipes/list.html -->
<div class="kk-filter-pills mb-4">
  <a href="{% url 'recipes:list' %}"
     class="kk-filter-pill {% if not active_category %}kk-filter-pill--active{% endif %}">
    Wszystkie
  </a>
  {% for cat in categories %}
  <a href="{% url 'recipes:list' %}?kategoria={{ cat.slug }}"
     class="kk-filter-pill {% if active_category == cat.slug %}kk-filter-pill--active{% endif %}">
    {{ cat.name }}
  </a>
  {% endfor %}
</div>
```

**Why GET params, not session:** Simple, bookmarkable, shareable URLs. Search and filter combine cleanly: `?kategoria=desery&q=czekolada`. No server-side state needed.

**Why admin-managed categories (not hardcoded):** The CONTEXT.md leaves this to Claude's Discretion. Admin-managed is recommended because:
- Owner will add/rename categories over time ("Zupy", "Napoje", etc.)
- Hardcoded choices require code deploys for content changes
- `Category` model with admin is trivial to implement

Pre-populate via a data migration with the 4-5 initial categories (Śniadania, Obiady, Desery, Przekąski) so the site isn't empty on first deploy.

### Pattern 5: Schema.org JSON-LD (PRZE-05)

**What:** Inline `<script type="application/ld+json">` in the recipe detail template with Recipe schema. No external library needed.

Google's required fields for Recipe rich results (per Google Search Central documentation):
- `@context`: `"https://schema.org"`
- `@type`: `"Recipe"`
- `name`: recipe title
- `image`: absolute URL to recipe image (required for rich result eligibility)
- `recipeIngredient`: array of ingredient strings

Google's recommended fields (for enhanced rich result):
- `description`
- `prepTime`: ISO 8601 duration (e.g., `"PT30M"` for 30 minutes)
- `recipeInstructions`: array of `HowToStep` objects or plain strings
- `datePublished`
- `author`: `{"@type": "Organization", "name": "Kuchenna Komitywa"}`

**Implementation approach — build the dict in the view, pass to template:**

```python
# In recipe_detail view
import json
from django.templatetags.static import static

def recipe_detail(request, slug):
    recipe = get_object_or_404(Recipe, slug=slug, is_published=True)

    # Build Schema.org JSON-LD
    schema = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": recipe.title,
        "description": recipe.description,
        "prepTime": f"PT{recipe.prep_time}M",
        "recipeIngredient": [
            line.strip()
            for line in recipe.ingredients_text.splitlines()
            if line.strip()
        ],
        "recipeInstructions": [
            {"@type": "HowToStep", "text": step.strip()}
            for step in recipe.steps_text.splitlines()
            if step.strip()
        ],
        "datePublished": recipe.created_at.date().isoformat(),
        "author": {"@type": "Organization", "name": "Kuchenna Komitywa"},
    }
    if recipe.image:
        schema["image"] = request.build_absolute_uri(recipe.image.url)

    return render(request, "recipes/detail.html", {
        "recipe": recipe,
        "schema_json": json.dumps(schema, ensure_ascii=False),
    })
```

```html
<!-- In recipes/detail.html {% block extra_js %} -->
<script type="application/ld+json">{{ schema_json }}</script>
```

**IMPORTANT:** Use `{{ schema_json }}` without escaping — Django auto-escapes HTML entities in `{{ }}`. Use `{% autoescape off %}{{ schema_json }}{% endautoescape %}` or pass through `mark_safe()` in the view:

```python
from django.utils.safestring import mark_safe
# ...
"schema_json": mark_safe(json.dumps(schema, ensure_ascii=False)),
```

Using `mark_safe` here is safe because we control the dict entirely — no user input reaches it unvalidated.

### Pattern 6: Django Admin for Recipes

```python
# recipes/admin.py
from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Recipe


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "prep_time", "is_published", "created_at", "image_preview"]
    list_filter = ["category", "is_published"]
    search_fields = ["title", "ingredients_text"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["image_preview", "created_at", "updated_at"]

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:60px;">', obj.image.url)
        return "—"
    image_preview.short_description = "Podgląd"
```

`prepopulated_fields` auto-fills the slug from the title in the admin form — consistent with Django admin convention and project pattern (`get_user_model()`, `@admin.register`).

### Pattern 7: Template Inheritance

All recipe templates extend `base.html` using the established pattern:

```html
{% extends "base.html" %}
{% block title %}{{ recipe.title }} — Kuchenna Komitywa{% endblock %}
{% block content %}
  <!-- recipe content -->
{% endblock %}
{% block extra_js %}
  <script type="application/ld+json">{% autoescape off %}{{ schema_json }}{% endautoescape %}</script>
{% endblock %}
```

Recipe list template uses `.kk-section` for consistent section padding, Bootstrap card grid, and brand CSS variables already defined in `main.css`.

### Pattern 8: ImageField vs FileField

Use `ImageField` (not `FileField`) because:
- Django validates that uploaded file is a valid image (requires Pillow — already installed)
- Provides `width_field`/`height_field` hooks if needed later
- Semantically correct for recipe photos

```python
image = models.ImageField(upload_to="recipes/", blank=True, null=True)
```

Files land in `MEDIA_ROOT/recipes/` = `media/recipes/`. The `MEDIA_ROOT` and `MEDIA_URL` are already configured in `backend/settings.py` and the debug urlconf already serves media files in dev mode.

### Anti-Patterns to Avoid

- **N+1 queries in list view:** Always use `.select_related("category")` on the queryset. Without it, each card renders a separate SQL query to fetch the category name.
- **Slug collisions:** Auto-generating slug in `save()` without collision handling can create duplicate slugs if two recipes have the same title. Add a uniqueness suffix (`-2`, `-3`) or rely on the admin's `prepopulated_fields` and let the admin user manually handle collisions (acceptable for a small site with one editor).
- **Using `{% url %}` before the recipes app is registered:** The navbar currently uses `href="/przepisy/"` (plain string) — replace with `{% url 'recipes:list' %}` only after the `recipes` app and URL namespace are registered. Follow the same precedent as Phase 2 (plain string until real URL exists).
- **JSON-LD auto-escaping:** Passing `json.dumps()` output through Django's `{{ }}` template tag without `mark_safe` will escape `<`, `>`, `&` inside strings. Use `mark_safe()` on the pre-serialized string.
- **Storing absolute image URLs in JSON-LD:** Google requires full URLs. Use `request.build_absolute_uri(recipe.image.url)` — `recipe.image.url` alone gives a relative path.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pagination | Custom offset/limit logic | `django.core.paginator.Paginator` | Handles edge cases, orphan pages, page count; 3-line integration |
| Slug auto-generation | Custom slugify | `django.utils.text.slugify` | Handles Polish characters (ą→a, ę→e, etc.) and edge cases |
| Search across multiple fields | Raw SQL or multiple separate queries | `django.db.models.Q` objects with `|` operator | Clean, chainable, indexed |
| Schema.org serialization | Custom template tag or string interpolation | `json.dumps()` + `mark_safe` | Correct JSON escaping, no external dep |
| Image validation | Manual MIME type check | `models.ImageField` (Pillow) | Validates image integrity on upload |
| Admin slug auto-fill | JavaScript snippet | `prepopulated_fields` in ModelAdmin | Built-in Django admin feature |

**Key insight:** All tools needed for this phase are built into Django 5.2. No new pip packages are required.

---

## Common Pitfalls

### Pitfall 1: N+1 Queries on Recipe List
**What goes wrong:** Recipe list view renders 9 cards, each accessing `recipe.category.name` — Django executes 10 SQL queries (1 for recipes + 9 for categories).
**Why it happens:** ForeignKey fields are lazy-loaded by default.
**How to avoid:** `Recipe.objects.filter(...).select_related("category")` — fetches categories in a single JOIN.
**Warning signs:** Django Debug Toolbar shows duplicate queries; page load slows with more recipes.

### Pitfall 2: JSON-LD HTML Auto-Escaping
**What goes wrong:** `{{ schema_json }}` in template outputs `&lt;script&gt;` or escapes `"` inside JSON strings, producing invalid JSON-LD.
**Why it happens:** Django's auto-escaping converts `<`, `>`, `&`, `"` to HTML entities.
**How to avoid:** Wrap the JSON string with `mark_safe()` before passing to context, OR use `{% autoescape off %}{{ schema_json }}{% endautoescape %}`. The first approach is cleaner.
**Warning signs:** Browser dev tools show malformed JSON in the `<script type="application/ld+json">` tag; Google Rich Results Test reports parse error.

### Pitfall 3: Relative Image URL in Schema.org
**What goes wrong:** `"image": "/media/recipes/photo.jpg"` fails Google's Schema.org validation — image must be an absolute URL.
**Why it happens:** `recipe.image.url` returns a relative URL like `/media/recipes/photo.jpg`.
**How to avoid:** Use `request.build_absolute_uri(recipe.image.url)` in the view.
**Warning signs:** Google Rich Results Test reports "image URL is not absolute".

### Pitfall 4: Slug Collision on Auto-Generate
**What goes wrong:** Two recipes titled "Zupa Pomidorowa" both get slug `zupa-pomidorowa`; the second `save()` raises `IntegrityError` due to `unique=True`.
**Why it happens:** The `save()` method only generates a slug when `not self.slug`, but `slugify` is deterministic.
**How to avoid:** Use `prepopulated_fields = {"slug": ("title",)}` in admin — the editor sees and can modify the slug before saving. For this small site with one editor, that is sufficient. If automated bulk-import is needed, add suffix logic.
**Warning signs:** `IntegrityError: UNIQUE constraint failed: recipes_recipe.slug` in logs.

### Pitfall 5: Paginator Breaking with Combined Filter + Search
**What goes wrong:** Pagination links on filtered/searched results lose the `?kategoria=` or `?q=` params because the paginator template just generates `?page=2`.
**Why it happens:** Django's `page_obj` doesn't know about other GET params.
**How to avoid:** In the template, build paginator links that preserve existing GET params:

```html
<!-- Preserve filter/search params across pages -->
{% if page_obj.has_previous %}
  <a href="?page={{ page_obj.previous_page_number }}{% if active_category %}&kategoria={{ active_category }}{% endif %}{% if query %}&q={{ query }}{% endif %}">
    Poprzednia
  </a>
{% endif %}
```

Or use a template tag helper that copies all GET params and replaces only `page`.

### Pitfall 6: Missing `app_name` in `urls.py`
**What goes wrong:** `{% url 'recipes:list' %}` raises `NoReverseMatch` even after including the URL.
**Why it happens:** URL namespace requires `app_name = "recipes"` in the app's `urls.py`, not just `namespace="recipes"` in the `include()` call.
**How to avoid:** Set `app_name = "recipes"` at the top of `recipes/urls.py`. This is consistent with how Django namespacing works.

### Pitfall 7: `INSTALLED_APPS` Missing `recipes`
**What goes wrong:** Migrations fail, admin doesn't show recipe models, template loading from app templates directory fails.
**Why it happens:** Forgot to add `"recipes"` to `INSTALLED_APPS` in `backend/settings.py`.
**How to avoid:** Add `"recipes"` to `INSTALLED_APPS` as first task after creating the app.

---

## Code Examples

### Recipe Card (Bootstrap Card Grid, PRZE-01 / D-01 / D-02)

```html
<!-- recipes/list.html — inside .row -->
{% for recipe in page_obj %}
<div class="col-lg-4 col-md-6 col-12 mb-4">
  <div class="card h-100 kk-recipe-card">
    {% if recipe.image %}
    <img src="{{ recipe.image.url }}" class="card-img-top kk-recipe-thumb" alt="{{ recipe.title }}">
    {% else %}
    <div class="kk-recipe-thumb-placeholder"></div>
    {% endif %}
    <div class="card-body d-flex flex-column">
      {% if recipe.category %}
      <span class="badge kk-category-badge mb-2">{{ recipe.category.name }}</span>
      {% endif %}
      <h3 class="card-title h5">{{ recipe.title }}</h3>
      <p class="card-text text-muted flex-grow-1">{{ recipe.description|truncatechars:120 }}</p>
      <div class="d-flex justify-content-between align-items-center mt-3">
        <small class="text-muted"><i class="bi bi-clock"></i> {{ recipe.prep_time }} min</small>
        <a href="{% url 'recipes:detail' slug=recipe.slug %}" class="kk-btn-primary kk-btn-sm">
          Czytaj więcej
        </a>
      </div>
    </div>
  </div>
</div>
{% empty %}
<div class="col-12">
  <p class="text-center text-muted py-5">Nie znaleziono przepisów. Spróbuj innego wyszukiwania.</p>
</div>
{% endfor %}
```

### Search Form (PRZE-04)

```html
<form method="get" action="{% url 'recipes:list' %}" class="kk-search-form mb-4">
  {% if active_category %}
  <input type="hidden" name="kategoria" value="{{ active_category }}">
  {% endif %}
  <div class="input-group">
    <input type="search" name="q" value="{{ query }}" placeholder="Szukaj przepisów..." class="form-control">
    <button type="submit" class="btn kk-btn-primary">
      <i class="bi bi-search"></i>
    </button>
  </div>
</form>
```

Note: hidden `kategoria` input preserves the active category filter when searching within a category.

### Paginator with Preserved GET Params (Pitfall 5 fix)

```html
{% if page_obj.has_other_pages %}
<nav aria-label="Strony przepisów">
  <ul class="pagination justify-content-center">
    {% if page_obj.has_previous %}
    <li class="page-item">
      <a class="page-link" href="?page={{ page_obj.previous_page_number }}{% if active_category %}&kategoria={{ active_category }}{% endif %}{% if query %}&q={{ query }}{% endif %}">
        &laquo;
      </a>
    </li>
    {% endif %}
    {% for num in page_obj.paginator.page_range %}
    <li class="page-item {% if page_obj.number == num %}active{% endif %}">
      <a class="page-link" href="?page={{ num }}{% if active_category %}&kategoria={{ active_category }}{% endif %}{% if query %}&q={{ query }}{% endif %}">
        {{ num }}
      </a>
    </li>
    {% endfor %}
    {% if page_obj.has_next %}
    <li class="page-item">
      <a class="page-link" href="?page={{ page_obj.next_page_number }}{% if active_category %}&kategoria={{ active_category }}{% endif %}{% if query %}&q={{ query }}{% endif %}">
        &raquo;
      </a>
    </li>
    {% endif %}
  </ul>
</nav>
{% endif %}
```

### CSS Classes to Add to main.css

New classes needed for Phase 3 (append to `static/css/main.css`):

```css
/* ===========================
   Phase 3: Recipes
   =========================== */

/* Recipe card thumbnail — consistent 4:3 aspect ratio */
.kk-recipe-thumb {
    width: 100%;
    height: 220px;
    object-fit: cover;
}

.kk-recipe-thumb-placeholder {
    width: 100%;
    height: 220px;
    background-color: var(--kk-beige);
}

/* Category badge on recipe card */
.kk-category-badge {
    background-color: var(--kk-sage);
    color: #ffffff;
    font-family: var(--kk-font-body);
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    align-self: flex-start;
}

/* Small CTA button variant for cards */
.kk-btn-sm {
    padding: 6px 16px;
    font-size: 14px;
}

/* Category filter pills */
.kk-filter-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.kk-filter-pill {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 20px;
    border: 1px solid var(--kk-beige);
    background-color: var(--kk-warm-white);
    color: var(--kk-text);
    font-family: var(--kk-font-body);
    font-size: 14px;
    font-weight: 400;
    text-decoration: none;
    transition: all 200ms ease;
}

.kk-filter-pill:hover {
    background-color: var(--kk-sage);
    border-color: var(--kk-sage);
    color: #ffffff;
}

.kk-filter-pill--active {
    background-color: var(--kk-olive);
    border-color: var(--kk-olive);
    color: #ffffff;
    font-weight: 700;
}

/* Recipe card hover lift */
.kk-recipe-card {
    border: 1px solid var(--kk-beige);
    border-radius: 8px;
    overflow: hidden;
    transition: box-shadow 200ms ease, transform 200ms ease;
}

.kk-recipe-card:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.10);
    transform: translateY(-2px);
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Separate `Ingredient` model in v1 | Single `ingredients_text TextField` for v1 | Django ecosystem recommendation for simple blogs | Simpler admin, fewer migrations, sufficient for Schema.org |
| Hardcoded category choices in model | Admin-managed `Category` model | Standard Django pattern | Owner can add categories without code changes |
| JavaScript-based slug generation | Django `prepopulated_fields` in ModelAdmin | Django 1.x+ | Built-in, no custom JS needed |
| Separate Schema.org library | `json.dumps` + `mark_safe` inline | Modern Django practice | Zero dependencies, fully sufficient for Recipe schema |

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | Django runtime | ✓ | (system Python) | — |
| Django | Core framework | ✓ | 5.2.12 | — |
| Pillow | `ImageField` image uploads | ✓ | 9.0.1 | Could use `FileField` but loses image validation |
| SQLite3 | Database | ✓ | (built-in) | — |
| `media/` directory | Image upload target | ✓ | exists (with .gitkeep) | — |

No missing dependencies. All tools available.

---

## Validation Architecture

> `nyquist_validation` is `true` in `.planning/config.json` — this section is required.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Django TestCase (built-in, no extra package) |
| Config file | `backend/settings.py` (`DATABASES`, `INSTALLED_APPS`) |
| Quick run command | `python3 manage.py test recipes --verbosity=0` |
| Full suite command | `python3 manage.py test --verbosity=0` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PRZE-01 | GET `/przepisy/` returns 200; recipe cards render with thumbnail, category, title | unit (HTTP) | `python3 manage.py test recipes.tests.TestRecipeList -x` | ❌ Wave 0 |
| PRZE-02 | GET `/przepisy/<slug>/` returns 200 with ingredients, steps, prep_time | unit (HTTP) | `python3 manage.py test recipes.tests.TestRecipeDetail -x` | ❌ Wave 0 |
| PRZE-03 | GET `/przepisy/?kategoria=desery` returns only recipes in that category | unit (HTTP) | `python3 manage.py test recipes.tests.TestCategoryFilter -x` | ❌ Wave 0 |
| PRZE-04 | GET `/przepisy/?q=czekolada` returns recipes matching title or ingredients | unit (HTTP) | `python3 manage.py test recipes.tests.TestRecipeSearch -x` | ❌ Wave 0 |
| PRZE-05 | Recipe detail page source contains `"@type": "Recipe"` JSON-LD | unit (HTTP) | `python3 manage.py test recipes.tests.TestSchemaOrgMarkup -x` | ❌ Wave 0 |
| PRZE-06 | Recipe and Category appear in Django admin; admin can create/edit/delete | unit (admin) | `python3 manage.py test recipes.tests.TestRecipeAdmin -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python3 manage.py test recipes --verbosity=0`
- **Per wave merge:** `python3 manage.py test --verbosity=0`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `recipes/tests.py` — covers all 6 test classes above (PRZE-01 through PRZE-06)
- [ ] `recipes/migrations/0001_initial.py` — auto-generated after model definition
- [ ] `recipes/` app directory with `__init__.py`, `apps.py`, `models.py`, `views.py`, `urls.py`, `admin.py`
- [ ] `templates/recipes/list.html` and `templates/recipes/detail.html`

---

## Open Questions

1. **Paginator page count with long page_range**
   - What we know: Django `Paginator.page_range` returns all page numbers — with 100+ recipes this renders 10+ page links
   - What's unclear: Whether to limit page range to 5 surrounding pages
   - Recommendation: For v1 with a small site (likely < 50 recipes), render all pages. Add windowed pagination in v2 if needed.

2. **Empty-state for recipe list (no published recipes)**
   - What we know: The `{% empty %}` tag in the for loop handles zero results
   - What's unclear: Whether a more prominent empty-state design (illustration + CTA to contact) is wanted
   - Recommendation: Simple centered text with warm tone for v1 ("Przepisy wkrótce! Tymczasem zajrzyj do naszego sklepu."). User will replace with real content.

3. **Navbar "Przepisy" link activation**
   - What we know: `_navbar.html` uses `request.resolver_match.url_name` for active link detection (established pattern from Phase 2 context)
   - What's unclear: Whether the active check works across all recipe URLs (`list` and `detail`)
   - Recommendation: Check `request.resolver_match.app_name == 'recipes'` rather than a specific `url_name` — this marks the Przepisy nav link active on both list and detail pages.

---

## Project Constraints (from CLAUDE.md)

| Directive | Constraint |
|-----------|-----------|
| Stack | Django 5.2 + Django templates only. No SPA, no React/Vue. |
| Language | Polish only — all user-facing strings, template text, admin labels |
| Views pattern | Function-based views (no class-based views used yet — keep consistent) |
| String quotes | Double quotes for all new Python string literals |
| Import style | `from X import Y`; relative imports within app; `get_user_model()` not direct User import |
| Admin registration | `@admin.register(Model)` decorator pattern |
| Admin actions | `@admin.action(description="...")` decorator |
| Naming | `PascalCase` classes, `snake_case` functions/methods/variables |
| Media | `MEDIA_ROOT` / `MEDIA_URL` already configured — use directly |
| GSD workflow | Must work through GSD commands (execute-phase) — no direct edits outside workflow |

---

## Sources

### Primary (HIGH confidence)
- Django 5.2 official docs — Django `Paginator`, `Q` objects, `ImageField`, `prepopulated_fields`, `slugify`
- Schema.org Recipe spec — `https://schema.org/Recipe` (type, properties)
- Google Search Central — Recipe structured data requirements (required vs recommended fields)
- Codebase inspection — `backend/settings.py`, `core/views.py`, `core/urls.py`, `templates/base.html`, `static/css/main.css` (all read directly)

### Secondary (MEDIUM confidence)
- Phase 1 and 2 CONTEXT.md and SUMMARY files — established patterns, CSS classes, URL conventions
- Django admin `prepopulated_fields` documentation — slug auto-fill behavior

### Tertiary (LOW confidence)
None — all findings are from official Django docs or direct codebase inspection.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries are already installed and in active use in this project
- Architecture: HIGH — patterns derived from existing codebase (same FBV style, same URL include pattern, same template inheritance)
- Schema.org JSON-LD: HIGH — derived from official Schema.org and Google Search Central documentation
- Pitfalls: HIGH — all documented from known Django behaviors (N+1, auto-escaping, paginator GET params)

**Research date:** 2026-03-31
**Valid until:** 2026-09-30 (stable Django APIs; Schema.org requirements rarely change)
