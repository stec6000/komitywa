---
quick_id: 260508-ibb
mode: quick-full
type: execute
wave: 1
autonomous: true
depends_on: []
files_modified:
  - recipes/models.py
  - recipes/admin.py
  - recipes/views.py
  - recipes/migrations/0004_add_tags_servings_difficulty_notes.py
  - templates/recipes/list.html
  - templates/recipes/detail.html
  - recipes/tests.py

requirements:
  - QUICK-260508-ibb

must_haves:
  truths:
    - "Tag model exists in recipes app with name + slug, M2M to Recipe via tags field, related_name=recipes"
    - "Recipe model has servings (PositiveSmallIntegerField default 1), difficulty (CharField choices latwy/sredni/trudny default latwy), notes (TextField blank default empty)"
    - "Migration 0004 creates Tag + new fields, seeds 8 starter tags, backfills servings/difficulty on 11 existing recipes, and applies the locked tag mapping. Re-running migrate is a no-op."
    - "Recipe list page renders a second tag-row filter under the existing categories filter; clicking a tag toggles ?tag=<slug>; multiple tags use AND (intersection)"
    - "?tag=foo&tag=bar narrows to recipes that have BOTH foo and bar (AND semantics, distinct queryset)"
    - "Recipe card on /przepisy/ shows servings (porcje) next to prep_time and a small line of tags under category"
    - "Recipe detail aside shows servings, difficulty, and tag pills; main column renders 'Od autora' section only when notes is non-empty"
    - "Detail JSON-LD schema includes recipeYield (string of servings) and keywords (comma-joined tag names) when tags exist"
    - "Admin: Tag is registered with prepopulated slug; RecipeAdmin uses filter_horizontal for tags, lists tags in list_filter and list_display, and includes tags/servings/difficulty/notes in fieldsets"
    - "All Polish copy in new code is ASCII-Polish (no diacritics)"
    - "Test suite passes including new tests for AND-tag-filter, backfill values, and JSON-LD recipeYield + keywords"
  artifacts:
    - path: "recipes/models.py"
      provides: "Tag model + Recipe.tags M2M + servings/difficulty/notes fields"
      contains: "class Tag"
    - path: "recipes/migrations/0004_add_tags_servings_difficulty_notes.py"
      provides: "Single migration: CreateModel(Tag) + AddField x4 + RunPython seed/backfill"
      contains: "0004_add_tags_servings_difficulty_notes"
    - path: "recipes/admin.py"
      provides: "TagAdmin registration + RecipeAdmin updates (filter_horizontal, list_filter, list_display, fieldsets)"
      contains: "@admin.register(Tag)"
    - path: "recipes/views.py"
      provides: "recipe_list reads getlist('tag') and chains AND filter; recipe_detail JSON-LD adds recipeYield + keywords"
      contains: "getlist(\"tag\")"
    - path: "templates/recipes/list.html"
      provides: "Second tag-row for tags + tag chips + servings on cards"
      contains: "Filtr tagow"
    - path: "templates/recipes/detail.html"
      provides: "Tag pills + servings + difficulty in aside; 'Od autora' notes section"
      contains: "Od autora"
    - path: "recipes/tests.py"
      provides: "Tests for AND filter, backfill, JSON-LD additions"
      contains: "TestRecipeTags"
  key_links:
    - from: "templates/recipes/list.html (tag chip <a>)"
      to: "recipes/views.py (getlist('tag') filter)"
      via: "?tag=<slug> repeatable"
      pattern: "getlist\\(\"tag\"\\)"
    - from: "recipes/views.py (recipe_detail schema dict)"
      to: "templates/recipes/detail.html (ld+json script)"
      via: "schema_json context with recipeYield + keywords"
      pattern: "recipeYield"
    - from: "recipes/migrations/0004 RunPython"
      to: "Recipe.tags M2M (created in same migration)"
      via: "tag_map.set(...) inside seed function"
      pattern: "0004_add_tags_servings_difficulty_notes"
---

<objective>
Add a Tag system (own model + M2M with Recipe) plus three new Recipe fields (servings, difficulty, notes) end-to-end: schema, admin, views (with AND multi-tag filter via repeatable ?tag= param), templates (list filter row + cards, detail aside + author notes section), schema.org JSON-LD additions (recipeYield, keywords), and tests. One combined migration handles schema changes and seeds 8 starter tags + backfills the 11 existing recipes per the locked mapping.

Purpose: enable richer recipe discovery (tag-based filtering) and richer per-recipe metadata (servings, difficulty, optional author notes) that surface in cards, detail pages, and structured data.

Output: Updated models/admin/views/templates + a single idempotent migration + new tests, all ASCII-Polish.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@./CLAUDE.md
@recipes/models.py
@recipes/admin.py
@recipes/views.py
@recipes/urls.py
@recipes/migrations/0002_seed_recipe_catalog.py
@recipes/migrations/0003_add_krem_z_bialej_fasoli.py
@templates/recipes/list.html
@templates/recipes/detail.html
@recipes/tests.py

<interfaces>
<!-- Existing exports the executor must integrate with -->

From recipes/models.py (current state, before this plan):
```python
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    # related_name on Recipe.category = "recipes"

class Recipe(models.Model):
    title, slug, category (FK -> Category, related_name="recipes"),
    description, ingredients_text, steps_text,
    prep_time (PositiveSmallIntegerField),
    image (ImageField, optional), is_published, created_at, updated_at
    # Recipe.objects.filter(is_published=True).select_related("category") is the canonical queryset
```

From recipes/views.py (current state):
```python
def recipe_list(request):
    # filters: ?kategoria=<slug>, ?q=<text>; uses Paginator(12)
    # context: page_obj, categories, active_category, query

def recipe_detail(request, slug):
    # schema dict has: @context, @type=Recipe, name, description,
    # prepTime (ISO 8601 PT<n>M), recipeIngredient[], recipeInstructions[],
    # datePublished, author, image (if any)
    # rendered via mark_safe(json.dumps(schema, ensure_ascii=False))
```

CSS classes already available (DO NOT add new CSS):
- `.tag-row` — flex-wrap row container, gap 10px, mb 30px
- `.tag` — pill style; `.tag.active` for current selection
- `.recipe-card`, `.recipe-img`, `.recipe-body`, `.recipe-kicker`, `.recipe-name`, `.recipe-meta` — already styled
- `.kk-detail-sidebar` — aside container on detail
- `.kk-prep-time`, `.kk-category-badge` — chip styles next to title
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Tag model + Recipe field additions + admin + single combined migration with seed/backfill</name>
  <files>recipes/models.py, recipes/admin.py, recipes/migrations/0004_add_tags_servings_difficulty_notes.py</files>

  <behavior>
    - Tag model has name (CharField unique max_length=50), slug (SlugField unique max_length=50), Meta.ordering=["name"], __str__ returns name.
    - Recipe gains: tags (M2M to Tag, blank=True, related_name="recipes"), servings (PositiveSmallIntegerField default=1, help_text="Liczba porcji"), difficulty (CharField max_length=10, choices [latwy/sredni/trudny], default="latwy"), notes (TextField blank=True, default="").
    - Running `migrate recipes 0004` creates Tag table, adds 4 fields/M2M to Recipe, seeds 8 starter Tag rows idempotently (update_or_create on slug), and backfills the 11 existing recipes with the locked servings + difficulty values and tag mappings. Re-running migrate (or migrating to 0004 a second time) is a no-op.
    - Reverse migration removes 4 fields and the Tag table cleanly.
    - Admin: Tag registered with list_display=("name","slug") and prepopulated_fields={"slug":("name",)}. RecipeAdmin gets filter_horizontal=("tags",); list_display includes "tags"; list_filter includes "tags" (after "category"); fieldsets (or default fields list) include tags, servings, difficulty, notes.
  </behavior>

  <action>
**Step 1.1 — `recipes/models.py`:** add `Tag` class above `Recipe` and append the 4 new fields to `Recipe`. Final shape:

```python
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    # unchanged
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Kategoria"
        verbose_name_plural = "Kategorie"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tagi"
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
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="recipes",
    )
    description = models.TextField(
        help_text="Krotki opis (1-2 zdania) -- wyswietlany na karcie"
    )
    ingredients_text = models.TextField(
        help_text="Skladniki -- kazdy w nowej linii"
    )
    steps_text = models.TextField(
        help_text="Kroki przygotowania -- kazdy w nowej linii"
    )
    prep_time = models.PositiveSmallIntegerField(
        help_text="Czas przygotowania w minutach"
    )
    servings = models.PositiveSmallIntegerField(
        default=1,
        help_text="Liczba porcji",
    )
    difficulty = models.CharField(
        max_length=10,
        choices=[
            ("latwy", "latwy"),
            ("sredni", "sredni"),
            ("trudny", "trudny"),
        ],
        default="latwy",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Opcjonalne notatki autora",
    )
    image = models.ImageField(
        upload_to="recipes/",
        blank=True,
        null=True,
        help_text="Zdjecie przepisu",
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

**Step 1.2 — `recipes/admin.py`:** register `Tag`, extend `RecipeAdmin` with the new fields. Replace the file contents with:

```python
from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Recipe, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "slug"]


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "category",
        "servings",
        "difficulty",
        "prep_time",
        "is_published",
        "created_at",
        "image_preview",
    ]
    list_filter = ["category", "tags", "difficulty", "is_published"]
    search_fields = ["title", "ingredients_text"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["image_preview", "created_at", "updated_at"]
    filter_horizontal = ("tags",)
    fieldsets = (
        (None, {
            "fields": (
                "title",
                "slug",
                "category",
                "tags",
                "description",
                "ingredients_text",
                "steps_text",
            ),
        }),
        ("Metadane", {
            "fields": (
                "prep_time",
                "servings",
                "difficulty",
                "notes",
                "is_published",
            ),
        }),
        ("Zdjecie", {
            "fields": ("image", "image_preview"),
        }),
        ("Czas", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:60px;">',
                obj.image.url,
            )
        return "---"

    image_preview.short_description = "Podglad"
```

**Step 1.3 — Generate the migration:** Do NOT run `makemigrations` blindly. Hand-author `recipes/migrations/0004_add_tags_servings_difficulty_notes.py` so the seed/backfill runs in the same migration. The schema operations must come BEFORE the `RunPython` step so the data step can reference `Recipe.tags`, `servings`, `difficulty`, `notes`. File contents:

```python
from django.db import migrations, models


STARTER_TAGS = [
    {"slug": "tofu", "name": "tofu"},
    {"slug": "bezglutenowe", "name": "bezglutenowe"},
    {"slug": "szybkie", "name": "szybkie"},
    {"slug": "pieczone", "name": "pieczone"},
    {"slug": "na-zimno", "name": "na-zimno"},
    {"slug": "ciecierzyca", "name": "ciecierzyca"},
    {"slug": "fasola", "name": "fasola"},
    {"slug": "soczewica", "name": "soczewica"},
]


# slug -> (servings, difficulty, [tag_slugs])
RECIPE_BACKFILL = {
    "hummus-z-pieczona-ciecierzyca-i-warzywami": (4, "latwy", ["ciecierzyca", "bezglutenowe", "na-zimno"]),
    "curry-z-tofu-brokulem-i-mleczkiem-kokosowym": (3, "sredni", ["tofu", "bezglutenowe"]),
    "chili-sin-carne-z-czarna-fasola": (4, "latwy", ["fasola", "bezglutenowe"]),
    "smoothie-bowl-z-mango-i-bananem": (1, "latwy", ["szybkie", "bezglutenowe", "na-zimno"]),
    "placuszki-owsiano-bananowe-z-borowkami": (2, "latwy", ["szybkie"]),
    "buddha-bowl-z-tofu-ryzem-i-pieczona-papryka": (2, "latwy", ["tofu", "pieczone", "bezglutenowe"]),
    "salatka-z-ciecierzyca-pieczonym-batatem-i-pestkami": (2, "latwy", ["ciecierzyca", "pieczone", "bezglutenowe"]),
    "krem-pomidorowy-z-czerwonej-soczewicy": (4, "latwy", ["soczewica", "bezglutenowe", "szybkie"]),
    "chlebek-bananowy-z-orzechami-wloskimi": (8, "sredni", ["pieczone"]),
    "makaron-z-pesto-pietruszkowo-bazyliowym": (2, "latwy", ["szybkie"]),
    "krem-z-bialej-fasoli-ze-szparagami": (2, "latwy", ["fasola", "tofu", "pieczone", "bezglutenowe"]),
}


def seed_tags_and_backfill(apps, schema_editor):
    Tag = apps.get_model("recipes", "Tag")
    Recipe = apps.get_model("recipes", "Recipe")

    tag_by_slug = {}
    for tag in STARTER_TAGS:
        obj, _ = Tag.objects.update_or_create(
            slug=tag["slug"],
            defaults={"name": tag["name"]},
        )
        tag_by_slug[tag["slug"]] = obj

    for slug, (servings, difficulty, tag_slugs) in RECIPE_BACKFILL.items():
        try:
            recipe = Recipe.objects.get(slug=slug)
        except Recipe.DoesNotExist:
            # Idempotent: skip if a recipe was renamed/removed in a future state.
            continue
        recipe.servings = servings
        recipe.difficulty = difficulty
        recipe.save(update_fields=["servings", "difficulty"])
        recipe.tags.set([tag_by_slug[s] for s in tag_slugs])


def unseed_tags_and_backfill(apps, schema_editor):
    Tag = apps.get_model("recipes", "Tag")
    Recipe = apps.get_model("recipes", "Recipe")
    # Clear M2M links on recipes and delete starter tags.
    for recipe in Recipe.objects.filter(slug__in=RECIPE_BACKFILL.keys()):
        recipe.tags.clear()
    Tag.objects.filter(slug__in=[t["slug"] for t in STARTER_TAGS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0003_add_krem_z_bialej_fasoli"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True)),
                ("slug", models.SlugField(max_length=50, unique=True)),
            ],
            options={
                "verbose_name": "Tag",
                "verbose_name_plural": "Tagi",
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="recipe",
            name="tags",
            field=models.ManyToManyField(
                blank=True,
                related_name="recipes",
                to="recipes.tag",
            ),
        ),
        migrations.AddField(
            model_name="recipe",
            name="servings",
            field=models.PositiveSmallIntegerField(default=1, help_text="Liczba porcji"),
        ),
        migrations.AddField(
            model_name="recipe",
            name="difficulty",
            field=models.CharField(
                choices=[("latwy", "latwy"), ("sredni", "sredni"), ("trudny", "trudny")],
                default="latwy",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="recipe",
            name="notes",
            field=models.TextField(blank=True, default="", help_text="Opcjonalne notatki autora"),
        ),
        migrations.RunPython(seed_tags_and_backfill, unseed_tags_and_backfill),
    ]
```

**Step 1.4 — Apply and sanity-check the migration:**

```bash
.venv/bin/python manage.py migrate recipes 0004
.venv/bin/python manage.py migrate recipes 0004   # second run = no-op
```

Notes:
- Do NOT run `makemigrations` after writing 0004; if you do and Django proposes a new auto-migration, that means the model file diverges from the migration -- reconcile back to the spec above.
- ASCII-Polish only (no `latwy`->`łatwy` etc.).
  </action>

  <verify>
<automated>.venv/bin/python manage.py makemigrations recipes --check --dry-run && .venv/bin/python manage.py migrate recipes 0004 && .venv/bin/python -c "import django, os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings'); django.setup(); from recipes.models import Recipe, Tag; assert Tag.objects.count() >= 8, 'tags not seeded'; r = Recipe.objects.get(slug='krem-z-bialej-fasoli-ze-szparagami'); assert r.servings == 2 and r.difficulty == 'latwy', f'backfill failed: {r.servings}/{r.difficulty}'; assert set(r.tags.values_list('slug', flat=True)) == {'fasola','tofu','pieczone','bezglutenowe'}, f'tag mapping failed: {list(r.tags.values_list(\"slug\", flat=True))}'; print('OK')"</automated>
  </verify>

  <done>
- `recipes/models.py` defines `Tag` and the 4 new Recipe fields exactly as specified.
- `recipes/admin.py` registers `Tag`, includes `tags`, `servings`, `difficulty`, `notes` in RecipeAdmin (filter_horizontal, list_filter, list_display, fieldsets).
- `recipes/migrations/0004_add_tags_servings_difficulty_notes.py` exists and applies cleanly. `makemigrations --check --dry-run` reports no missing migrations.
- 8 starter tags seeded; 11 recipes backfilled with servings/difficulty + tag mapping per the locked tables.
- Re-running `migrate recipes 0004` is a no-op (no errors, no rewrites).
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: View layer — AND tag filter (?tag= getlist) + schema.org additions (recipeYield, keywords)</name>
  <files>recipes/views.py</files>

  <behavior>
    - GET /przepisy/ accepts repeatable `?tag=<slug>` -- combined with existing `?kategoria=` and `?q=` via AND. Empty tag list = no tag filter.
    - Multi-tag filter is intersection: ?tag=tofu&tag=szybkie returns only recipes that have BOTH. Implemented by chaining `.filter(tags__slug=...)` calls and then `.distinct()`.
    - Context for list view exposes `tags` (all Tag objects) and `active_tags` (list of slugs from getlist) so templates can render both rows.
    - Detail view JSON-LD adds `recipeYield` (str of recipe.servings) and `keywords` (comma-joined tag names) only when there is at least one tag.
  </behavior>

  <action>
Replace `recipes/views.py` with:

```python
import json

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.utils.safestring import mark_safe

from .models import Category, Recipe, Tag


def recipe_list(request):
    recipes = (
        Recipe.objects.filter(is_published=True)
        .select_related("category")
        .prefetch_related("tags")
    )

    active_category = request.GET.get("kategoria", "")
    if active_category:
        recipes = recipes.filter(category__slug=active_category)

    active_tags = [t for t in request.GET.getlist("tag") if t]
    # AND semantics: chain .filter() per tag so each must match.
    for tag_slug in active_tags:
        recipes = recipes.filter(tags__slug=tag_slug)
    if active_tags:
        recipes = recipes.distinct()

    query = request.GET.get("q", "").strip()
    if query:
        recipes = recipes.filter(
            Q(title__icontains=query) | Q(ingredients_text__icontains=query)
        )

    paginator = Paginator(recipes, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()
    tags = Tag.objects.all()

    return render(request, "recipes/list.html", {
        "page_obj": page_obj,
        "categories": categories,
        "tags": tags,
        "active_category": active_category,
        "active_tags": active_tags,
        "query": query,
    })


def recipe_detail(request, slug):
    recipe = get_object_or_404(
        Recipe.objects.prefetch_related("tags"),
        slug=slug,
        is_published=True,
    )

    schema = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": recipe.title,
        "description": recipe.description,
        "prepTime": f"PT{recipe.prep_time}M",
        "recipeYield": str(recipe.servings),
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

    tag_names = list(recipe.tags.values_list("name", flat=True))
    if tag_names:
        schema["keywords"] = ", ".join(tag_names)

    schema_json = mark_safe(json.dumps(schema, ensure_ascii=False))

    return render(request, "recipes/detail.html", {
        "recipe": recipe,
        "schema_json": schema_json,
    })
```

Notes:
- Keep ordering of context keys stable so templates can rely on them.
- AND filter implementation MUST chain `.filter(tags__slug=...)` per slug -- a single `tags__slug__in=[...]` would yield OR, not AND.
- `prefetch_related("tags")` avoids N+1 in list view; `select_related` cannot follow M2M.
  </action>

  <verify>
<automated>.venv/bin/python -m py_compile recipes/views.py && .venv/bin/python manage.py check</automated>
  </verify>

  <done>
- `recipe_list` reads `request.GET.getlist("tag")`, applies AND filter via chained `.filter().distinct()`, and exposes `tags` + `active_tags` in context.
- `recipe_detail` JSON-LD always emits `recipeYield`; emits `keywords` only when there is at least one tag.
- `manage.py check` passes with no errors.
  </done>
</task>

<task type="auto">
  <name>Task 3: Templates — list (tag filter row + tag chips on cards + servings) and detail (aside tags/servings/difficulty + 'Od autora' notes)</name>
  <files>templates/recipes/list.html, templates/recipes/detail.html</files>

  <action>
**Step 3.1 — `templates/recipes/list.html`:** insert a SECOND `.tag-row` (for tags) immediately after the existing categories `.tag-row`, add a tags line on each card under `.recipe-kicker`, and add a `· N porcji` span in `.recipe-meta`. Critically, all paginator and filter links must preserve `?tag=` repeats (use a tag-querystring snippet).

Reuse the existing `.tag` / `.tag-row` styles. Implement a small inline {% with %} block that builds the persistent querystring fragment for tags so we don't duplicate logic. Replace the file with:

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Przepiśnik — Kuchenna Komitywa{% endblock %}

{% block content %}
<section class="kk-section" aria-label="Przepiśnik">
    <div class="wrap">
        <div class="section-head">
            <div>
                <div class="section-number">II. · przepiśnik</div>
                <h2 class="section-title">Przepisy z zeszytu<span class="section-annotation">— klikaj żeby otworzyć</span></h2>
            </div>
            <div class="section-meta">
                {{ page_obj.paginator.count }} przepis{{ page_obj.paginator.count|pluralize:"y,ów" }}
                {% if active_category or query or active_tags %} · filtr aktywny{% endif %}
            </div>
        </div>

        {# Build a stable suffix for active tag params: &tag=foo&tag=bar #}
        {% spaceless %}
        {% with tag_qs="" %}
        {% for t in active_tags %}{% with tag_qs=tag_qs|add:"&tag="|add:t %}{% endwith %}{% endfor %}
        {% endwith %}
        {% endspaceless %}

        <form method="get" action="{% url 'recipes:list' %}" class="kk-search-bar">
            {% if active_category %}
            <input type="hidden" name="kategoria" value="{{ active_category }}">
            {% endif %}
            {% for t in active_tags %}
            <input type="hidden" name="tag" value="{{ t }}">
            {% endfor %}
            <label for="q" class="visually-hidden">Szukaj przepisów</label>
            <div class="input-group">
                <input type="search" id="q" name="q" value="{{ query }}" placeholder="szukaj przepisu…">
                <button type="submit">szukaj</button>
            </div>
        </form>

        <div class="tag-row" role="navigation" aria-label="Filtr kategorii">
            <a href="{% url 'recipes:list' %}?{% for t in active_tags %}tag={{ t }}&{% endfor %}{% if query %}q={{ query }}{% endif %}"
               class="tag {% if not active_category %}active{% endif %}"
               {% if not active_category %}aria-current="page"{% endif %}>wszystko</a>
            {% for cat in categories %}
            <a href="{% url 'recipes:list' %}?kategoria={{ cat.slug }}{% for t in active_tags %}&tag={{ t }}{% endfor %}{% if query %}&q={{ query }}{% endif %}"
               class="tag {% if active_category == cat.slug %}active{% endif %}"
               {% if active_category == cat.slug %}aria-current="page"{% endif %}>{{ cat.name|lower }}</a>
            {% endfor %}
        </div>

        <div class="tag-row" role="navigation" aria-label="Filtr tagow" style="margin-top:-10px;">
            {% for t in tags %}
            {% if t.slug in active_tags %}
                {# Active -> link toggles OFF this tag (keeps the rest) #}
                <a href="{% url 'recipes:list' %}?{% if active_category %}kategoria={{ active_category }}&{% endif %}{% for at in active_tags %}{% if at != t.slug %}tag={{ at }}&{% endif %}{% endfor %}{% if query %}q={{ query }}{% endif %}"
                   class="tag active"
                   aria-current="page"
                   aria-label="Wylacz tag {{ t.name }}">#{{ t.name }}</a>
            {% else %}
                {# Inactive -> link adds this tag to the active set #}
                <a href="{% url 'recipes:list' %}?{% if active_category %}kategoria={{ active_category }}&{% endif %}{% for at in active_tags %}tag={{ at }}&{% endfor %}tag={{ t.slug }}{% if query %}&q={{ query }}{% endif %}"
                   class="tag"
                   aria-label="Dodaj tag {{ t.name }}">#{{ t.name }}</a>
            {% endif %}
            {% endfor %}
        </div>

        {% if page_obj.object_list %}
        <div class="recipe-grid">
            {% for recipe in page_obj %}
            <a class="recipe-card" href="{% url 'recipes:detail' slug=recipe.slug %}" aria-label="Otwórz przepis: {{ recipe.title }}">
                <div class="recipe-img{% if recipe.image %} recipe-img--photo{% endif %}">
                    <div class="num-stamp">{{ forloop.counter|stringformat:"02d" }}</div>
                    <div class="time-stamp">{{ recipe.prep_time }} min</div>
                    {% if recipe.image %}
                    <img src="{{ recipe.image.url }}" alt="">
                    {% endif %}
                </div>
                <div class="recipe-body">
                    {% if recipe.category %}
                    <div class="recipe-kicker">{{ recipe.category.name|lower }}</div>
                    {% endif %}
                    <div class="recipe-name">{{ recipe.title }}</div>
                    {% with recipe_tags=recipe.tags.all %}
                    {% if recipe_tags %}
                    <div class="recipe-meta" aria-label="Tagi przepisu">
                        {% for t in recipe_tags %}<span>#{{ t.name }}</span>{% endfor %}
                    </div>
                    {% endif %}
                    {% endwith %}
                    <div class="recipe-meta">
                        {% if recipe.category %}<span>{{ recipe.category.name|lower }}</span>{% endif %}
                        <span>· {{ recipe.prep_time }} min</span>
                        <span>· {{ recipe.servings }} porc{{ recipe.servings|pluralize:"ja,je,ji" }}</span>
                    </div>
                </div>
            </a>
            {% endfor %}
        </div>

        {% if page_obj.has_other_pages %}
        <nav aria-label="Paginacja przepisów">
            <ul class="kk-pagination">
                {% if page_obj.has_previous %}
                <li class="page-item">
                    <a class="page-link" href="?page={{ page_obj.previous_page_number }}{% if active_category %}&kategoria={{ active_category }}{% endif %}{% for t in active_tags %}&tag={{ t }}{% endfor %}{% if query %}&q={{ query }}{% endif %}" aria-label="Poprzednia strona">«</a>
                </li>
                {% endif %}
                {% for num in page_obj.paginator.page_range %}
                <li class="page-item {% if page_obj.number == num %}active{% endif %}">
                    <a class="page-link" href="?page={{ num }}{% if active_category %}&kategoria={{ active_category }}{% endif %}{% for t in active_tags %}&tag={{ t }}{% endfor %}{% if query %}&q={{ query }}{% endif %}">{{ num }}</a>
                </li>
                {% endfor %}
                {% if page_obj.has_next %}
                <li class="page-item">
                    <a class="page-link" href="?page={{ page_obj.next_page_number }}{% if active_category %}&kategoria={{ active_category }}{% endif %}{% for t in active_tags %}&tag={{ t }}{% endfor %}{% if query %}&q={{ query }}{% endif %}" aria-label="Następna strona">»</a>
                </li>
                {% endif %}
            </ul>
        </nav>
        {% endif %}

        {% else %}
        <div class="kk-empty-state">
            {% if query %}
            <h2>Nic nie znaleziono</h2>
            <p>Nie znaleźliśmy przepisów pasujących do „{{ query }}". Spróbuj innego słowa lub przejrzyj wszystkie.</p>
            <a href="{% url 'recipes:list' %}" class="kk-link-arrow">wszystkie przepisy →</a>
            {% elif active_category or active_tags %}
            <h2>Pusta selekcja</h2>
            <p>Tu jeszcze nic nie ma. Sprawdź inne kategorie albo wszystkie przepisy.</p>
            <a href="{% url 'recipes:list' %}" class="kk-link-arrow">wszystkie przepisy →</a>
            {% else %}
            <h2>Wkrótce…</h2>
            <p>Dopisuję pierwsze przepisy. Wróć za chwilę.</p>
            {% endif %}
        </div>
        {% endif %}
    </div>
</section>
{% endblock %}
```

Key invariants for list.html:
- Existing categories `.tag-row` still uses category logic only (kategoria + q kept; tags appended).
- New tags `.tag-row` toggles tags by adding/removing the slug from `?tag=` (preserves kategoria and q).
- All template-rendered Polish copy is ASCII-Polish (no diacritics in new strings: "Filtr tagow", "Wylacz", "Dodaj"). Existing strings with diacritics (Przepiśnik, etc.) stay untouched.
- `recipe.servings|pluralize:"ja,je,ji"` -> 1 porcja, 2-4 porcje, 5+ porcji. Django `pluralize` accepts comma-separated forms only for two-form plural; for the Polish 3-form case we accept a small approximation -- if the pluralize filter does not accept 3 args, fall back to:
  ```html
  <span>· {{ recipe.servings }} porcj{% if recipe.servings == 1 %}a{% elif recipe.servings < 5 %}e{% else %}i{% endif %}</span>
  ```
  Use the fallback. (Django's `pluralize` only supports 2-form: singular,plural. So write the conditional inline.)

**Step 3.2 — `templates/recipes/detail.html`:** add tag pills + servings + difficulty in the aside, and add an "Od autora" section in the main column rendered only if `recipe.notes`. Replace the file with:

```html
{% extends "base.html" %}
{% load static %}

{% block title %}{{ recipe.title }} — Kuchenna Komitywa{% endblock %}

{% block content %}
<section class="kk-section" aria-label="Przepis">
    <div class="wrap">
        <div class="row">
            <div class="col-lg-8">
                {% if recipe.image %}
                <div class="kk-detail-hero">
                    <img src="{{ recipe.image.url }}" alt="{{ recipe.title }}">
                </div>
                {% endif %}

                {% if recipe.category %}
                <div class="hero-eyebrow">{{ recipe.category.name|lower }}</div>
                {% endif %}

                <h1>{{ recipe.title }}</h1>

                <div class="d-flex flex-wrap gap-2 mb-4" style="align-items: center;">
                    <span class="kk-prep-time">⏱ {{ recipe.prep_time }} min</span>
                    <span class="kk-prep-time">🍽 {{ recipe.servings }} porcj{% if recipe.servings == 1 %}a{% elif recipe.servings < 5 %}e{% else %}i{% endif %}</span>
                    <span class="kk-prep-time">★ {{ recipe.difficulty }}</span>
                    {% if recipe.category %}
                    <span class="kk-category-badge">{{ recipe.category.name|lower }}</span>
                    {% endif %}
                    <span style="font-family: var(--font-body); font-style: italic; color: var(--ink-faded); font-size: 15px;">{{ recipe.created_at|date:"j E Y" }}</span>
                </div>

                <p class="lead">{{ recipe.description }}</p>

                <h2>Składniki</h2>
                <div class="kk-ingredients">{{ recipe.ingredients_text|linebreaksbr }}</div>

                <h2>Sposób przygotowania</h2>
                <div class="kk-steps">{{ recipe.steps_text|linebreaksbr }}</div>

                {% if recipe.notes %}
                <h2>Od autora</h2>
                <div class="kk-notes">{{ recipe.notes|linebreaksbr }}</div>
                {% endif %}
            </div>

            <div class="col-lg-4">
                <aside class="kk-detail-sidebar">
                    <div class="featured-label" style="position: static; display: inline-block; margin-bottom: 16px;">notatnik</div>
                    <div class="mb-3">
                        <div class="hero-eyebrow" style="font-size: 22px; margin-bottom: 4px;">czas</div>
                        <div style="font-family: var(--font-display); font-size: 28px;">{{ recipe.prep_time }} min</div>
                    </div>
                    <div class="mb-3">
                        <div class="hero-eyebrow" style="font-size: 22px; margin-bottom: 4px;">porcje</div>
                        <div style="font-family: var(--font-display); font-size: 28px;">{{ recipe.servings }}</div>
                    </div>
                    <div class="mb-3">
                        <div class="hero-eyebrow" style="font-size: 22px; margin-bottom: 4px;">poziom</div>
                        <div style="font-family: var(--font-display); font-size: 22px;">{{ recipe.difficulty }}</div>
                    </div>
                    {% if recipe.category %}
                    <div class="mb-3">
                        <div class="hero-eyebrow" style="font-size: 22px; margin-bottom: 4px;">kategoria</div>
                        <div style="font-family: var(--font-display); font-size: 22px;">{{ recipe.category.name }}</div>
                    </div>
                    {% endif %}
                    {% with recipe_tags=recipe.tags.all %}
                    {% if recipe_tags %}
                    <div class="mb-3">
                        <div class="hero-eyebrow" style="font-size: 22px; margin-bottom: 4px;">tagi</div>
                        <div class="tag-row" style="margin-bottom: 0;">
                            {% for t in recipe_tags %}
                            <a href="{% url 'recipes:list' %}?tag={{ t.slug }}" class="tag">#{{ t.name }}</a>
                            {% endfor %}
                        </div>
                    </div>
                    {% endif %}
                    {% endwith %}
                    <p style="margin-top: 24px; padding-top: 16px; border-top: 1px dashed var(--ink-soft);">
                        <a href="{% url 'recipes:list' %}" class="kk-link-arrow">← wróć do przepiśnika</a>
                    </p>
                </aside>
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block extra_js %}
<script type="application/ld+json">{% autoescape off %}{{ schema_json }}{% endautoescape %}</script>
{% endblock %}
```

Key invariants for detail.html:
- Existing categories pill `.kk-category-badge` stays.
- Tags rendered in aside use `.tag-row` + `.tag` (existing CSS, no new rules).
- "Od autora" block is conditional on truthy `recipe.notes`.
- New copy in the aside uses ASCII-Polish: "porcje", "poziom", "tagi". (Existing "kategoria", "wróć", "notatnik" stay untouched.)
  </action>

  <verify>
<automated>.venv/bin/python manage.py check && .venv/bin/python -c "from django.template import engines; eng = engines['django']; eng.get_template('recipes/list.html'); eng.get_template('recipes/detail.html'); print('templates parse OK')"</automated>
  </verify>

  <done>
- list.html renders a categories `.tag-row` and a tags `.tag-row` (in that order), preserves `?kategoria`, `?q`, and repeated `?tag=` across pagination/filter links.
- Each card shows tags (when present) + `· N porcji` next to category and prep_time.
- detail.html aside renders porcje, poziom, and tags pills (when present); main column shows "Od autora" only if notes is non-empty.
- Both templates parse without TemplateSyntaxError.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 4: Tests — AND tag filter, backfill values, JSON-LD recipeYield + keywords</name>
  <files>recipes/tests.py</files>

  <behavior>
    - New TestCase `TestRecipeTags` covers:
      - `?tag=foo` returns recipes with foo.
      - `?tag=foo&tag=bar` returns ONLY recipes with both (AND, not OR).
      - `?tag=foo&kategoria=zupy` AND-combines.
    - New TestCase `TestRecipeBackfill` confirms backfilled servings/difficulty + tag mapping for two anchor recipes from the migration (use ones that exist post-0004 -- `krem-z-bialej-fasoli-ze-szparagami` and `chlebek-bananowy-z-orzechami-wloskimi`).
    - Extend `TestSchemaOrgMarkup` (or add `TestSchemaOrgExtras`) for `recipeYield` always present + `keywords` present when tags exist + `keywords` absent when no tags.
  </behavior>

  <action>
Append to `recipes/tests.py` (do NOT remove existing tests). Add the following classes after the existing `TestSchemaOrgMarkup` class but before `TestRecipeAdmin`:

```python
class TestRecipeTags(TestCase):

    def setUp(self):
        from recipes.models import Tag
        self.tofu = Tag.objects.create(name="tofu", slug="tofu")
        self.szybkie = Tag.objects.create(name="szybkie", slug="szybkie")
        self.cat = Category.objects.create(name="Obiady", slug="obiady-tags")

        self.r_tofu_szybkie = Recipe.objects.create(
            title="Tofu Szybkie",
            slug="tofu-szybkie",
            category=self.cat,
            description="oba tagi",
            ingredients_text="x",
            steps_text="y",
            prep_time=10,
            servings=2,
            difficulty="latwy",
        )
        self.r_tofu_szybkie.tags.add(self.tofu, self.szybkie)

        self.r_tofu_only = Recipe.objects.create(
            title="Tofu Wolne",
            slug="tofu-wolne",
            category=self.cat,
            description="tylko tofu",
            ingredients_text="x",
            steps_text="y",
            prep_time=40,
            servings=2,
            difficulty="latwy",
        )
        self.r_tofu_only.tags.add(self.tofu)

        self.r_szybkie_only = Recipe.objects.create(
            title="Szybkie Bez Tofu",
            slug="szybkie-bez-tofu",
            category=self.cat,
            description="tylko szybkie",
            ingredients_text="x",
            steps_text="y",
            prep_time=8,
            servings=1,
            difficulty="latwy",
        )
        self.r_szybkie_only.tags.add(self.szybkie)

    def test_single_tag_filter(self):
        response = self.client.get("/przepisy/?tag=tofu")
        self.assertContains(response, "Tofu Szybkie")
        self.assertContains(response, "Tofu Wolne")
        self.assertNotContains(response, "Szybkie Bez Tofu")

    def test_multi_tag_filter_uses_and(self):
        response = self.client.get("/przepisy/?tag=tofu&tag=szybkie")
        self.assertContains(response, "Tofu Szybkie")
        self.assertNotContains(response, "Tofu Wolne")
        self.assertNotContains(response, "Szybkie Bez Tofu")

    def test_tag_filter_combines_with_category_via_and(self):
        other_cat = Category.objects.create(name="Salatki", slug="salatki-tags")
        Recipe.objects.create(
            title="Tofu z innej kategorii",
            slug="tofu-inna-kategoria",
            category=other_cat,
            description="x",
            ingredients_text="x",
            steps_text="y",
            prep_time=10,
            servings=1,
            difficulty="latwy",
        ).tags.add(self.tofu)
        response = self.client.get("/przepisy/?tag=tofu&kategoria=obiady-tags")
        self.assertContains(response, "Tofu Szybkie")
        self.assertContains(response, "Tofu Wolne")
        self.assertNotContains(response, "Tofu z innej kategorii")


class TestRecipeBackfill(TestCase):
    """Verifies that migration 0004 backfilled the locked values on real seeded recipes."""

    def test_krem_z_bialej_fasoli_backfill(self):
        recipe = Recipe.objects.get(slug="krem-z-bialej-fasoli-ze-szparagami")
        self.assertEqual(recipe.servings, 2)
        self.assertEqual(recipe.difficulty, "latwy")
        self.assertEqual(
            set(recipe.tags.values_list("slug", flat=True)),
            {"fasola", "tofu", "pieczone", "bezglutenowe"},
        )

    def test_chlebek_bananowy_backfill(self):
        recipe = Recipe.objects.get(slug="chlebek-bananowy-z-orzechami-wloskimi")
        self.assertEqual(recipe.servings, 8)
        self.assertEqual(recipe.difficulty, "sredni")
        self.assertEqual(
            set(recipe.tags.values_list("slug", flat=True)),
            {"pieczone"},
        )

    def test_starter_tags_seeded(self):
        from recipes.models import Tag
        slugs = set(Tag.objects.values_list("slug", flat=True))
        for required in [
            "tofu", "bezglutenowe", "szybkie", "pieczone",
            "na-zimno", "ciecierzyca", "fasola", "soczewica",
        ]:
            self.assertIn(required, slugs)


class TestSchemaOrgExtras(TestCase):

    def setUp(self):
        from recipes.models import Tag
        self.cat = Category.objects.create(name="Desery", slug="desery-extras")
        self.tag = Tag.objects.create(name="szybkie-extras", slug="szybkie-extras")
        self.with_tags = Recipe.objects.create(
            title="Z Tagami",
            slug="z-tagami-schema",
            category=self.cat,
            description="x",
            ingredients_text="a",
            steps_text="b",
            prep_time=15,
            servings=4,
            difficulty="latwy",
        )
        self.with_tags.tags.add(self.tag)
        self.without_tags = Recipe.objects.create(
            title="Bez Tagow",
            slug="bez-tagow-schema",
            category=self.cat,
            description="x",
            ingredients_text="a",
            steps_text="b",
            prep_time=10,
            servings=2,
            difficulty="latwy",
        )

    def test_recipe_yield_present(self):
        response = self.client.get("/przepisy/z-tagami-schema/")
        self.assertContains(response, '"recipeYield": "4"')

    def test_keywords_present_when_tags(self):
        response = self.client.get("/przepisy/z-tagami-schema/")
        self.assertContains(response, '"keywords"')
        self.assertContains(response, "szybkie-extras")

    def test_keywords_absent_when_no_tags(self):
        response = self.client.get("/przepisy/bez-tagow-schema/")
        self.assertNotContains(response, '"keywords"')
        # recipeYield should still be present.
        self.assertContains(response, '"recipeYield": "2"')
```

Notes:
- Reuse existing `Recipe`/`Category` imports at the top of the file (already present); add `from recipes.models import Tag` inside test methods or at module top to avoid touching the existing import block (the existing top-of-file import is `from recipes.models import Category, Recipe` -- safe to extend it to include `Tag` if you prefer; either form is fine).
- ASCII-Polish only in test data strings.
- The `TestRecipeBackfill` class relies on the seeded migration data -- it runs against the test DB which executes ALL migrations, so 0004's RunPython runs and the seeded recipes plus backfill are present.
  </action>

  <verify>
<automated>.venv/bin/python manage.py test recipes -v 2 2>&1 | tail -40</automated>
  </verify>

  <done>
- All existing tests still pass.
- New tests pass: TestRecipeTags (3 tests), TestRecipeBackfill (3 tests), TestSchemaOrgExtras (3 tests).
- No regressions in TestRecipeList / TestRecipeDetail / TestCategoryFilter / TestSchemaOrgMarkup / TestRecipeAdmin.
  </done>
</task>

<task type="auto">
  <name>Task 5: End-to-end verification — migrate, makemigrations check, full test suite, manual smoke URL list</name>
  <files></files>

  <action>
Run the full verification battery from the project root, in order:

```bash
# 1. Schema is up-to-date (no model/migration drift).
.venv/bin/python manage.py makemigrations --check --dry-run

# 2. Apply migrations cleanly (idempotent on re-run).
.venv/bin/python manage.py migrate

# 3. Django's own checks (URL conf, admin, templates, settings).
.venv/bin/python manage.py check

# 4. Full test suite must pass.
.venv/bin/python manage.py test recipes -v 2

# 5. Quick admin/forms smoke (do not commit data; just exercise the codepaths).
.venv/bin/python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings')
django.setup()
from django.contrib import admin
from recipes.models import Recipe, Tag
recipe_admin = admin.site._registry[Recipe]
tag_admin = admin.site._registry[Tag]
assert 'tags' in recipe_admin.filter_horizontal, recipe_admin.filter_horizontal
assert 'tags' in recipe_admin.list_filter, recipe_admin.list_filter
assert 'tags' in [f for fs in recipe_admin.fieldsets for f in fs[1]['fields']], recipe_admin.fieldsets
print('admin wiring OK')
"
```

If any step fails, fix and re-run from step 1. ASCII-Polish requirement: grep for accidental diacritics in NEW code (existing copy in templates is excluded -- only check files this plan modified that are PYTHON):

```bash
grep -nP "[\xc4\x85\xc4\x87\xc4\x99\xc5\x82\xc5\x84\xc3\xb3\xc5\x9b\xc5\xba\xc5\xbc]" recipes/models.py recipes/admin.py recipes/views.py recipes/migrations/0004_add_tags_servings_difficulty_notes.py recipes/tests.py || echo "ASCII-Polish OK in Python files"
```

Smoke URLs to eyeball after `runserver` (optional manual check, NOT required for autonomous pass):
- `/przepisy/` -- two filter rows, cards show servings + tags.
- `/przepisy/?tag=tofu` -- only tofu recipes.
- `/przepisy/?tag=tofu&tag=bezglutenowe` -- intersection.
- `/przepisy/krem-z-bialej-fasoli-ze-szparagami/` -- aside has porcje (2), poziom (latwy), tagi (#fasola #tofu #pieczone #bezglutenowe). View source -> JSON-LD has `"recipeYield": "2"` and `"keywords": "fasola, tofu, pieczone, bezglutenowe"` (or in admin order).
  </action>

  <verify>
<automated>.venv/bin/python manage.py makemigrations --check --dry-run && .venv/bin/python manage.py check && .venv/bin/python manage.py test recipes -v 1 2>&1 | tail -20</automated>
  </verify>

  <done>
- `makemigrations --check --dry-run` reports no changes (model and migration are in sync).
- `manage.py check` reports no issues.
- All recipes tests pass (existing + 9 new).
- ASCII-Polish grep produces no hits in the Python files this plan touched.
  </done>
</task>

</tasks>

<verification>
- `python manage.py makemigrations --check --dry-run` -- exit 0, no diff.
- `python manage.py migrate` -- 0004 applies; second run is no-op.
- `python manage.py test recipes` -- all green (existing + new tests).
- `python manage.py check` -- 0 issues.
- Admin: `/admin/recipes/recipe/` shows tags column + filter; `/admin/recipes/tag/` lists 8 starter tags.
- Detail JSON-LD contains `"recipeYield"` and `"keywords"` (when tags) -- verified via TestSchemaOrgExtras.
- AND tag filter -- verified via TestRecipeTags.
</verification>

<success_criteria>
1. Migration 0004 is the SINGLE migration adding Tag, the M2M, and the 3 scalar fields, plus the seed/backfill RunPython.
2. The 8 starter tags exist after migrate; the 11 listed recipes have the locked servings/difficulty + tag mapping.
3. `?tag=` is repeatable and AND-filters; combines correctly with `?kategoria=` and `?q=` (also AND).
4. List page shows two filter rows (categories first, tags second), cards show tags + `· N porcji`.
5. Detail page aside shows porcje + poziom + tag pills; "Od autora" section appears only when notes is non-empty.
6. Detail JSON-LD has `recipeYield` always; `keywords` only when at least one tag.
7. Admin: Tag registered with prepopulated slug; RecipeAdmin uses filter_horizontal=("tags",), tags in list_display + list_filter, all 4 new fields appear in fieldsets.
8. All NEW Polish copy is ASCII-Polish.
9. All tests (existing + new) pass; `manage.py check` clean.
</success_criteria>

<output>
After completion, create `.planning/quick/260508-ibb-recipe-dodaj-tagi-m2m-tag-servings-diffi/260508-ibb-SUMMARY.md` documenting:
- What was added (Tag model, 3 fields, single migration with seed/backfill, view AND filter, template chrome, JSON-LD additions, tests).
- Files modified.
- Migration apply/rollback notes.
- Any deviations from the plan and why.
</output>
