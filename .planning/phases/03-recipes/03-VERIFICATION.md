---
phase: 03-recipes
verified: 2026-04-01T00:00:00Z
status: passed
score: 11/11 must-haves verified
re_verification: false
---

# Phase 03: Recipes Verification Report

**Phase Goal:** Visitors can browse, search, and read vegan recipes with rich content, and the site generates structured data for Google rich snippets
**Verified:** 2026-04-01
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | recipes app exists and is registered in INSTALLED_APPS | VERIFIED | `"recipes"` at line 60 of `backend/settings.py` |
| 2 | Category and Recipe models exist with all required fields | VERIFIED | `recipes/models.py` — both models present with all 11 fields on Recipe |
| 3 | Admin can create, edit, and delete recipes and categories | VERIFIED | `@admin.register(Recipe)` and `@admin.register(Category)` with `prepopulated_fields`, `list_filter`, `search_fields`, `image_preview` |
| 4 | Visitor sees a 3-column card grid of recipes with thumbnails, category badges, titles, excerpts, and prep times | VERIFIED | `list.html` renders Bootstrap col-lg-4 cards with `.kk-recipe-card`, `.kk-category-badge`, `prep_time`, `description|truncatechars:120` |
| 5 | Visitor can filter recipes by clicking category pills and only see recipes from that category | VERIFIED | `recipe_list` filters via `request.GET.get("kategoria")` → `category__slug=active_category`; `TestCategoryFilter` passes |
| 6 | Visitor can search recipes by title or ingredients and see matching results | VERIFIED | `recipe_list` applies `Q(title__icontains=query) | Q(ingredients_text__icontains=query)`; `TestRecipeSearch` passes |
| 7 | Pagination works and preserves filter/search query params across pages | VERIFIED | `Paginator(recipes, 9)` in view; pagination block in template preserves `kategoria` and `q` params |
| 8 | Empty states show appropriate Polish messages | VERIFIED | Template has three distinct empty-state branches: "Nic nie znaleziono" (search), "Brak przepisow w tej kategorii" (filter), "Brak przepisow" (default) |
| 9 | Visitor can read a full recipe with image, ingredients, steps, and prep time | VERIFIED | `detail.html` renders hero image, `ingredients_text|linebreaksbr`, `steps_text|linebreaksbr`, prep time in both content and sidebar; `TestRecipeDetail` passes |
| 10 | Recipe detail page source contains Schema.org JSON-LD with @type Recipe | VERIFIED | `recipe_detail` view builds schema dict with `"@type": "Recipe"` and serializes via `mark_safe(json.dumps(...))`; JSON-LD rendered in `{% block extra_js %}`; `TestSchemaOrgMarkup` passes |
| 11 | Navbar Przepisy link uses `{% url 'recipes:list' %}` and shows active state on recipe pages | VERIFIED | `_navbar.html` line 12: `href="{% url 'recipes:list' %}"` with `{% if request.resolver_match.app_name == 'recipes' %}active{% endif %}` |

**Score:** 11/11 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `recipes/models.py` | Category and Recipe models | VERIFIED | Both classes present; all fields: title, slug, category, description, ingredients_text, steps_text, prep_time, image, is_published, created_at, updated_at |
| `recipes/admin.py` | Admin registration for Category and Recipe | VERIFIED | `@admin.register(Category)`, `@admin.register(Recipe)` with prepopulated_fields, list_filter, search_fields, image_preview |
| `recipes/tests.py` | 6 test classes with real assertions | VERIFIED | All 6 classes present: TestRecipeList, TestRecipeDetail, TestCategoryFilter, TestRecipeSearch, TestSchemaOrgMarkup, TestRecipeAdmin |
| `recipes/urls.py` | URL patterns for list and detail | VERIFIED | `app_name = "recipes"`, `name="list"`, `name="detail"` |
| `backend/urls.py` | recipes URL include under /przepisy/ | VERIFIED | `path("przepisy/", include("recipes.urls", namespace="recipes"))` at line 14, before `core.urls` |
| `templates/recipes/list.html` | Full recipe list page with cards, filter bar, search, pagination | VERIFIED | Contains `kk-recipe-card`, `kk-filter-pill`, `kk-filter-pill--active`, `kk-category-badge`, `kk-search-bar`, `kk-pagination`, `aria-label="Paginacja przepisow"` |
| `recipes/views.py` | recipe_list with filtering, search, pagination; recipe_detail with JSON-LD | VERIFIED | Both views fully implemented with Paginator, Q objects, select_related, mark_safe, json.dumps, Schema.org schema dict |
| `static/css/main.css` | Recipe card, filter pill, search bar, pagination CSS | VERIFIED | Phase 3 section present with `.kk-recipe-card`, `.kk-recipe-card__img-wrapper` (padding-top: 75%), `.kk-category-badge`, `.kk-filter-pill`, `.kk-filter-pill--active`, `.kk-pagination` |
| `templates/recipes/detail.html` | Full recipe detail page with hero image, ingredients, steps, JSON-LD | VERIFIED | col-lg-8/col-lg-4 layout, hero image, ingredients, steps, sidebar, `application/ld+json` in `{% block extra_js %}` |
| `recipes/migrations/0001_initial.py` | Database schema migration | VERIFIED | File exists; Django test runner applies it successfully (20 tests pass) |
| `templates/includes/_navbar.html` | Wired Przepisy link with active state | VERIFIED | `{% url 'recipes:list' %}` with `request.resolver_match.app_name == 'recipes'` active state; placeholder `href="#"` removed |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `backend/settings.py` | recipes app | INSTALLED_APPS | VERIFIED | `"recipes"` present at line 60 (tool returned false negative — pattern matched correctly on manual inspection) |
| `backend/urls.py` | `recipes/urls.py` | include with namespace | VERIFIED | `include("recipes.urls", namespace="recipes")` at line 14 (tool regex false negative — confirmed in file) |
| `recipes/views.py` | `recipes/models.py` | model import | VERIFIED | `from .models import Category, Recipe` |
| `templates/recipes/list.html` | `recipes/views.py` | template context variables | VERIFIED | `page_obj`, `active_category`, `query`, `categories` all present in template |
| `recipes/views.py` | `recipes/models.py` | queryset with select_related, Q objects | VERIFIED | `select_related("category")`, `Q(title__icontains=query)`, `Q(ingredients_text__icontains=query)` |
| `templates/recipes/list.html` | `static/css/main.css` | CSS classes | VERIFIED | `kk-recipe-card`, `kk-filter-pill`, `kk-category-badge` used in template and defined in CSS |
| `recipes/views.py` | `templates/recipes/detail.html` | schema_json context variable | VERIFIED | `mark_safe(json.dumps(schema, ensure_ascii=False))` passed as `"schema_json"` in context |
| `templates/recipes/detail.html` | `base.html` | block extra_js with ld+json | VERIFIED | `{% block extra_js %}<script type="application/ld+json">` at lines 73-75 (tool regex false negative — multiline pattern) |
| `templates/includes/_navbar.html` | `recipes/urls.py` | `{% url 'recipes:list' %}` | VERIFIED | `href="{% url 'recipes:list' %}"` at line 12 |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| `templates/recipes/list.html` | `page_obj` | `Recipe.objects.filter(is_published=True).select_related("category")` → `Paginator` | Yes — live DB query | FLOWING |
| `templates/recipes/list.html` | `categories` | `Category.objects.all()` | Yes — live DB query | FLOWING |
| `templates/recipes/detail.html` | `recipe` | `get_object_or_404(Recipe, slug=slug, is_published=True)` | Yes — live DB query | FLOWING |
| `templates/recipes/detail.html` | `schema_json` | Built from `recipe` object fields | Yes — derived from DB record | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All 20 recipe tests pass | `python3 manage.py test recipes --verbosity=1` | 20 tests, 0 failures, 0 errors | PASS |
| TestRecipeList (4 tests) | included above | ok | PASS |
| TestRecipeDetail (5 tests) | included above | ok | PASS |
| TestCategoryFilter (2 tests) | included above | ok | PASS |
| TestRecipeSearch (3 tests) | included above | ok | PASS |
| TestSchemaOrgMarkup (3 tests) | included above | ok | PASS |
| TestRecipeAdmin (3 tests) | included above | ok | PASS |
| Migration schema valid | Django test runner applies 0001_initial during test run | Applied successfully | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PRZE-01 | 03-01, 03-02 | Uzytkownik moze przegladac liste przepisow z miniaturkami | SATISFIED | Recipe list with card grid, image thumbnails, `kk-recipe-card__img-wrapper`; TestRecipeList passes |
| PRZE-02 | 03-01, 03-03 | Uzytkownik moze otworzyc pelny przepis ze zdjeciami, skladnikami, krokami i czasem przygotowania | SATISFIED | `detail.html` renders hero image, `ingredients_text|linebreaksbr`, `steps_text|linebreaksbr`, `prep_time`; TestRecipeDetail passes |
| PRZE-03 | 03-02 | Uzytkownik moze filtrowac przepisy wedlug kategorii | SATISFIED | `recipe_list` filters by `?kategoria=<slug>`; category pills in `list.html`; TestCategoryFilter passes |
| PRZE-04 | 03-02 | Uzytkownik moze wyszukiwac przepisy po tytule i skladnikach | SATISFIED | `Q(title__icontains=query) | Q(ingredients_text__icontains=query)`; search form in `list.html`; TestRecipeSearch passes |
| PRZE-05 | 03-03 | Strona przepisu zawiera Schema.org JSON-LD markup | SATISFIED | `recipe_detail` builds full Schema.org dict with @type Recipe, recipeIngredient, recipeInstructions (HowToStep), prepTime, author, absolute image URL; TestSchemaOrgMarkup passes |
| PRZE-06 | 03-01 | Admin moze dodawac, edytowac i usuwac przepisy z panelu administracyjnego | SATISFIED | `RecipeAdmin` with `prepopulated_fields`, `list_filter`, `search_fields`, `readonly_fields`, `image_preview`; TestRecipeAdmin passes |

No orphaned requirements — all 6 PRZE requirements are claimed by plans and verified.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `templates/recipes/list.html` | 16 | `placeholder="Szukaj przepisow..."` | INFO | HTML input placeholder attribute — not a code stub |
| `templates/recipes/list.html` | 44 | `kk-recipe-card__img-placeholder` | INFO | CSS class for no-image fallback — expected feature, not a stub |

No blockers or warnings found. The two INFO items are intentional HTML attributes/class names, not code stubs.

---

### Human Verification Required

#### 1. Visual Recipe Card Layout

**Test:** Open `/przepisy/` in a browser with at least one published recipe in the database. Run `python3 manage.py migrate && python3 manage.py createsuperuser` first, then create a test recipe via `/admin/`.
**Expected:** 3-column card grid at desktop (col-lg-4), 2-column at tablet (col-md-6), 1-column on mobile. Cards show 4:3 image crop (or sage placeholder), category badge overlaid on image, title, truncated description, prep time, and "Czytaj wiecej" arrow link.
**Why human:** Visual layout, aspect ratio enforcement, and Bootstrap responsive breakpoints cannot be verified from template code alone.

#### 2. Navbar Active State

**Test:** Visit `/przepisy/` and `/przepisy/<slug>/` in a browser.
**Expected:** "Przepisy" nav link has `active` class on both pages; no other nav link is active.
**Why human:** CSS active state rendering requires a live browser; `request.resolver_match.app_name` logic works correctly in tests but visual styling depends on CSS rules in `main.css`.

#### 3. Schema.org Rich Snippet Eligibility

**Test:** Paste a detail page URL into Google's Rich Results Test (https://search.google.com/test/rich-results).
**Expected:** Google recognises the page as a `Recipe` rich result with name, prepTime, ingredients, and instructions.
**Why human:** Rich results validation requires Google's parser; the JSON-LD structure has been verified programmatically but external service validation cannot be automated here.

---

### Notes

- The development `db.sqlite3` has no applied migrations (fresh environment). This is not a gap — `python3 manage.py migrate` will apply all migrations correctly. The test suite creates and destroys an in-memory test DB, confirming migrations are valid.
- Two deprecation warnings about `ACCOUNT_EMAIL_REQUIRED` and `ACCOUNT_USERNAME_REQUIRED` in `backend/settings.py` are pre-existing from Phase 1/2 and are not introduced by Phase 3.
- gsd-tools reported 3 key link failures; all 3 are confirmed false negatives caused by regex limitations (single-line matching can't cross lines, `"recipes"` in INSTALLED_APPS not matching from `backend/settings.py` file reference).

---

_Verified: 2026-04-01_
_Verifier: Claude (gsd-verifier)_
