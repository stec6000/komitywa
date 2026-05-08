---
quick_id: 260508-ibb
mode: quick-full
type: summary
plan: 260508-ibb
subsystem: recipes
tags:
  - recipes
  - tags
  - migration
  - schema-org
  - templates
dependency_graph:
  requires:
    - recipes app (Category, Recipe models)
    - migration 0003_add_krem_z_bialej_fasoli
  provides:
    - Tag model (recipes.Tag)
    - Recipe.tags M2M
    - Recipe.servings, Recipe.difficulty, Recipe.notes fields
    - Repeatable ?tag= AND filter in recipe_list view
    - JSON-LD recipeYield + keywords on detail page
  affects:
    - recipes/models.py
    - recipes/admin.py
    - recipes/views.py
    - recipes/migrations/0004_add_tags_servings_difficulty_notes.py
    - templates/recipes/list.html
    - templates/recipes/detail.html
    - recipes/tests.py
tech_stack:
  added: []
  patterns:
    - "AND-multi-filter via chained .filter(tags__slug=...).distinct()"
    - "Idempotent data migration (update_or_create + tags.set + save(update_fields=))"
    - "Schema.org Recipe JSON-LD extension (recipeYield, keywords)"
    - "Inline Polish 3-form pluralisation in templates (porcja/porcje/porcji)"
key_files:
  created:
    - recipes/migrations/0004_add_tags_servings_difficulty_notes.py
  modified:
    - recipes/models.py
    - recipes/admin.py
    - recipes/views.py
    - templates/recipes/list.html
    - templates/recipes/detail.html
    - recipes/tests.py
decisions:
  - "Single combined migration (schema + data) for atomic delivery; reverse migration cleans up tags + clears M2M"
  - "AND tag filter via chained .filter() per slug + .distinct(); single tags__slug__in= would yield OR"
  - "Polish pluralisation handled inline in templates (Django pluralize is 2-form only)"
  - "ASCII-Polish enforced in NEW Python code; existing Polish-diacritic copy in templates preserved"
metrics:
  tasks_completed: 5
  files_changed: 7
  lines_added: 564
  tests_added: 9
  tests_total_passing: 29
  completed: 2026-05-08
---

# Quick Task 260508-ibb: Tag system, servings, difficulty, notes — Summary

End-to-end addition of a Recipe Tag system (own model + M2M) plus three new metadata fields (servings, difficulty, notes), wired through schema, admin, views, templates, JSON-LD structured data, and tests, delivered as one idempotent data+schema migration.

## What was added

1. **Tag model** in `recipes/models.py` — `name` (unique CharField, max 50) + `slug` (unique SlugField, max 50), ordered by name.
2. **Recipe model extensions** — `tags` (M2M to Tag, blank, related_name="recipes"), `servings` (PositiveSmallIntegerField default 1), `difficulty` (CharField choices latwy/sredni/trudny default latwy), `notes` (TextField blank default "").
3. **Migration 0004** — single migration that:
   - creates Tag table (CreateModel) and adds 4 fields to Recipe (AddField x4),
   - seeds 8 starter tags via `update_or_create(slug=...)` (idempotent),
   - backfills the 11 existing recipes with the locked servings + difficulty + tag mapping (also idempotent: `Recipe.tags.set(...)` and `save(update_fields=...)`),
   - reverse migration clears M2M links on the seeded recipes and deletes the starter tags.
4. **Admin** — `TagAdmin` with prepopulated slug + search; `RecipeAdmin` extended with `filter_horizontal=("tags",)`, `list_filter=[category, tags, difficulty, is_published]`, `list_display` adds servings + difficulty, and explicit `fieldsets` covering all new fields ("Metadane" group: prep_time, servings, difficulty, notes, is_published).
5. **View layer** (`recipes/views.py`):
   - `recipe_list` reads `request.GET.getlist("tag")` and chains `.filter(tags__slug=...).distinct()` per slug to deliver AND semantics across multiple tags; combines AND with `?kategoria=` and `?q=`. Adds `prefetch_related("tags")` to avoid N+1.
   - Context exposes `tags` + `active_tags` for templates.
   - `recipe_detail` JSON-LD always emits `recipeYield` (str of servings); emits `keywords` (comma-joined tag names) only when at least one tag exists.
6. **Templates**:
   - `templates/recipes/list.html` — adds a SECOND `.tag-row` (tags) below the existing categories `.tag-row`. Active tag chips toggle off (preserving the rest); inactive chips append. All filter and pagination links preserve `?kategoria`, repeated `?tag=` slugs, and `?q=`. Each card shows tag pills under the kicker and `· N porcj{a/e/i}` next to category and prep_time.
   - `templates/recipes/detail.html` — aside displays `czas`, `porcje`, `poziom`, `kategoria`, and a tag-row with chips that link back to the filtered list. Main column renders an "Od autora" section only when `recipe.notes` is non-empty. Schema-org JSON-LD receives the new fields automatically via the view.
7. **Tests** (`recipes/tests.py`) — 9 new tests in 3 classes:
   - `TestRecipeTags` (3) — single-tag filter, AND multi-tag filter, AND combination of tag with category.
   - `TestRecipeBackfill` (3) — verifies migration 0004's backfill of two anchor recipes (`krem-z-bialej-fasoli-ze-szparagami` and `chlebek-bananowy-z-orzechami-wloskimi`) and presence of all 8 starter tags.
   - `TestSchemaOrgExtras` (3) — `recipeYield` always present; `keywords` present when tags; `keywords` absent when no tags.

## Files modified

| File | Change |
|------|--------|
| `recipes/models.py` | Added Tag model; added 4 fields to Recipe (tags M2M, servings, difficulty, notes) |
| `recipes/admin.py` | Registered TagAdmin; extended RecipeAdmin with filter_horizontal, list_filter, list_display, fieldsets |
| `recipes/migrations/0004_add_tags_servings_difficulty_notes.py` | NEW — schema + idempotent seed/backfill |
| `recipes/views.py` | recipe_list AND tag filter via getlist; recipe_detail JSON-LD recipeYield + keywords |
| `templates/recipes/list.html` | Second tag-row (tags), tag chips on cards, servings on cards, querystring preservation |
| `templates/recipes/detail.html` | Aside porcje/poziom/tagi; main column "Od autora" notes block |
| `recipes/tests.py` | TestRecipeTags, TestRecipeBackfill, TestSchemaOrgExtras (9 new tests) |

## Migration apply / rollback notes

- Forward: `.venv/bin/python manage.py migrate recipes 0004` — creates Tag, adds 4 Recipe fields, seeds 8 tags, backfills 11 recipes. Schema operations precede the RunPython so the data step can use the new fields.
- Idempotency verified: a second `migrate recipes 0004` is a no-op. The seed function uses `update_or_create(slug=...)` for tags and `Recipe.tags.set([...])` (which atomically replaces the M2M membership) so re-runs remain safe.
- Reverse: `.venv/bin/python manage.py migrate recipes 0003_add_krem_z_bialej_fasoli` — clears M2M links on the seeded recipes and deletes starter tags, then drops the 4 Recipe fields and the Tag table.
- `manage.py makemigrations recipes --check --dry-run` reports no diff (model and migration are in sync).

## Verification battery (final)

- `manage.py makemigrations recipes --check --dry-run` — no changes.
- `manage.py check` — 0 issues.
- `manage.py migrate` — applies cleanly; second run is no-op.
- `manage.py test recipes` — 29 tests, all pass (20 existing + 9 new).
- Admin wiring smoke check — `RecipeAdmin.filter_horizontal`, `list_filter`, and `fieldsets` all include `tags`/`servings`/`difficulty`/`notes`.
- Manual functional smoke (Django Client) — `/przepisy/`, `/przepisy/?tag=tofu`, `/przepisy/?tag=tofu&tag=bezglutenowe`, and `/przepisy/krem-z-bialej-fasoli-ze-szparagami/` all return 200; JSON-LD on the detail page contains `"recipeYield": "2"` and `"keywords"`.
- ASCII-Polish — grep shows zero diacritics in all 5 touched Python files (models, admin, views, migration 0004, tests). Templates retain pre-existing diacritic copy unchanged; new template copy ("Filtr tagow", "Wylacz", "Dodaj", "porcje", "poziom", "tagi") is ASCII-Polish.

## Deviations from plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Static files manifest required for test runs**
- **Found during:** Task 4 (initial test execution failed)
- **Issue:** `WhiteNoise CompressedManifestStaticFilesStorage` requires a generated manifest before any template using `{% static %}` can render. Running `manage.py test recipes` without first running `collectstatic` produced `ValueError: Missing staticfiles manifest entry for 'css/main.css'` for every test that hits a template.
- **Fix:** Ran `.venv/bin/python manage.py collectstatic --noinput` once — populated `public/static` with 503 post-processed files including the manifest. After that, all 29 tests pass.
- **Files modified:** None in code; this is a pre-existing project requirement to run collectstatic before tests when manifest storage is configured. Not committed (collected static is generated output, present locally only).
- **Commit:** N/A (no code change).

**No other deviations.** Plan executed exactly as written: 5 tasks, 4 atomic commits, 1 verification-only task.

### Out-of-scope items observed (NOT fixed)

- `manage.py makemigrations` (no app filter) reports pending auto-migrations in the `shop` app (`Change Meta options on order`, `Alter field` on several Product fields, etc.). These predate this plan and are unrelated to recipes — left untouched per SCOPE BOUNDARY rule.

## Self-Check: PASSED

Files created:
- FOUND: `recipes/migrations/0004_add_tags_servings_difficulty_notes.py`
- FOUND: `.planning/quick/260508-ibb-recipe-dodaj-tagi-m2m-tag-servings-diffi/260508-ibb-SUMMARY.md` (this file)

Files modified (verified via `git log -p`):
- FOUND: `recipes/models.py` (commit f6a7c34)
- FOUND: `recipes/admin.py` (commit f6a7c34)
- FOUND: `recipes/views.py` (commit 329f109)
- FOUND: `templates/recipes/list.html` (commit 4021dd2)
- FOUND: `templates/recipes/detail.html` (commit 4021dd2)
- FOUND: `recipes/tests.py` (commit ffa99b0)

Commits exist:
- FOUND: `f6a7c34` feat(recipes): add Tag model + servings/difficulty/notes fields
- FOUND: `329f109` feat(recipes): add tag filter (AND) + recipeYield/keywords in JSON-LD
- FOUND: `4021dd2` feat(recipes): tag chips on list/detail + servings & difficulty display
- FOUND: `ffa99b0` test(recipes): coverage for tag filter, backfill, JSON-LD

Verifications:
- `manage.py makemigrations recipes --check --dry-run` exits 0
- `manage.py check` reports 0 issues
- `manage.py test recipes` runs 29 tests, all pass
- ASCII-Polish grep on all 5 touched Python files returns zero diacritic matches
