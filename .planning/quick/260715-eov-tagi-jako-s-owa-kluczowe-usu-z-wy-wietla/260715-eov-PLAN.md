---
phase: quick-260715-eov
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - templates/recipes/detail.html
  - templates/recipes/list.html
  - recipes/views.py
autonomous: true
requirements: [EOV-TAGS-01]

must_haves:
  truths:
    - "Rendered recipe pages show tag names without the '#' prefix"
    - "Recipe JSON-LD includes recipeCategory when the recipe has a category"
    - "Recipe JSON-LD keywords contain the category name alongside tag names (no duplicates)"
  artifacts:
    - path: "templates/recipes/detail.html"
      provides: "Tag link rendering without '#'"
      contains: "{{ t.name }}"
    - path: "templates/recipes/list.html"
      provides: "Tag link/span rendering without '#'"
      contains: "{{ t.name }}"
    - path: "recipes/views.py"
      provides: "recipeCategory + category-in-keywords JSON-LD"
      contains: "recipeCategory"
  key_links:
    - from: "recipes/views.py"
      to: "schema keywords/recipeCategory"
      via: "recipe.category.name"
      pattern: "recipeCategory"
---

<objective>
Treat tags as keywords: remove the displayed "#" prefix from recipe tags across all
4 template locations, and enrich the recipe JSON-LD with `recipeCategory` plus the
category name inside `keywords`.

Purpose: Cleaner tag presentation and richer structured data (SEO) that treats the
category as a first-class keyword.
Output: Updated `detail.html`, `list.html`, and `recipes/views.py`.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md

<interfaces>
<!-- Exact current lines the executor edits. No exploration needed. -->

templates/recipes/detail.html:47
  <a href="{% url 'recipes:list' %}?tag={{ t.slug }}" class="tag">#{{ t.name }}</a>

templates/recipes/list.html:51
  aria-label="Wylacz tag {{ t.name }}">#{{ t.name }}</a>

templates/recipes/list.html:56
  aria-label="Dodaj tag {{ t.name }}">#{{ t.name }}</a>

templates/recipes/list.html:80
  {% for t in recipe_tags %}<span>#{{ t.name }}</span>{% endfor %}

recipes/views.py (recipe_detail, ~lines 82-84 — existing keywords block):
  tag_names = list(recipe.tags.values_list("name", flat=True))
  if tag_names:
      schema["keywords"] = ", ".join(tag_names)
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Remove '#' prefix from displayed tags in both templates</name>
  <files>templates/recipes/detail.html, templates/recipes/list.html</files>
  <action>
    Remove the literal `#` character immediately before `{{ t.name }}` in exactly
    4 places, leaving links/spans and all other markup unchanged:
    - detail.html:47 — `class="tag">#{{ t.name }}</a>` becomes `class="tag">{{ t.name }}</a>`
    - list.html:51 — `...tag {{ t.name }}">#{{ t.name }}</a>` (the second, rendered occurrence) becomes `{{ t.name }}</a>`
    - list.html:56 — same edit as list.html:51 (rendered `#{{ t.name }}` → `{{ t.name }}`)
    - list.html:80 — `<span>#{{ t.name }}</span>` becomes `<span>{{ t.name }}</span>`
    Do NOT touch the `aria-label` text (it already has no `#`). Do NOT alter hrefs,
    classes, or loop structure.
  </action>
  <verify>
    <automated>! grep -rn '#{{ t.name }}' templates/recipes/ && grep -rc '{{ t.name }}' templates/recipes/detail.html templates/recipes/list.html</automated>
  </verify>
  <done>No `#{{ t.name }}` remains in templates/recipes/; `{{ t.name }}` still present in both files.</done>
</task>

<task type="auto">
  <name>Task 2: Add recipeCategory and category keyword to JSON-LD</name>
  <files>recipes/views.py</files>
  <action>
    In `recipe_detail`, extend the existing keywords/schema block (currently ~lines
    82-84). Build the keyword list from the category name followed by tag names,
    without duplicates and only including present values:
    - Collect `tag_names` as today via `recipe.tags.values_list("name", flat=True)`.
    - If `recipe.category` exists, set `schema["recipeCategory"] = recipe.category.name`.
    - Compose keywords as category name (if present) plus tag names, de-duplicated
      while preserving order (category first). Only set `schema["keywords"]` when the
      composed list is non-empty; join with ", ".
    Use a truthy check on `recipe.category` (FK may be nullable). Keep double-quote
    string style per CLAUDE.md.
  </action>
  <verify>
    <automated>python manage.py check</automated>
  </verify>
  <done>`recipeCategory` set when category present; `keywords` includes category name before tags with no duplicates; `manage.py check` passes.</done>
</task>

</tasks>

<verification>
- `python manage.py check` passes.
- `grep -rn '#{{ t.name }}' templates/recipes/` returns nothing.
- Manual/local render (runserver + curl of a recipe with a category and tags):
  HTML contains the tag name without a leading `#` (e.g. `tofu`, not `#tofu`);
  the embedded JSON-LD contains `"recipeCategory"` and a `"keywords"` value that
  starts with the category name followed by the tags.
</verification>

<success_criteria>
- All 4 template tag renders drop the `#` prefix with no other functional change.
- JSON-LD gains `recipeCategory` (when category present) and category-first,
  de-duplicated `keywords`.
- `python manage.py check` clean.
</success_criteria>

<output>
Create `.planning/quick/260715-eov-tagi-jako-s-owa-kluczowe-usu-z-wy-wietla/260715-eov-SUMMARY.md` when done
</output>
