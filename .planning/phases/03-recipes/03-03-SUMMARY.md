---
phase: 03-recipes
plan: 03
subsystem: ui
tags: [django-templates, schema-org, json-ld, seo, bootstrap]

# Dependency graph
requires:
  - phase: 03-recipes-01
    provides: "Recipe/Category models, URL routes, stub views and templates"
provides:
  - "Full recipe detail page with hero image, ingredients, steps, sidebar"
  - "Schema.org JSON-LD markup for Google rich snippets"
  - "Wired navbar Przepisy link with active state"
affects: [04-ebooks, 05-shop]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Schema.org JSON-LD via mark_safe + json.dumps in view context", "Active navbar state via request.resolver_match.app_name"]

key-files:
  created: []
  modified:
    - "recipes/views.py"
    - "templates/recipes/detail.html"
    - "templates/includes/_navbar.html"

key-decisions:
  - "Detail-specific CSS in extra_css block to avoid conflicts with Plan 02 main.css ownership"
  - "Navbar active state uses app_name == 'recipes' (not url_name) for both list and detail pages"

patterns-established:
  - "Schema.org JSON-LD: build dict in view, serialize with mark_safe(json.dumps(...)), render in extra_js block with autoescape off"
  - "Navbar active detection: use request.resolver_match.app_name for app-wide active state"

requirements-completed: [PRZE-02, PRZE-05]

# Metrics
duration: 1min
completed: 2026-04-01
---

# Phase 3 Plan 3: Recipe Detail & Schema.org Summary

**Full recipe detail page with two-column layout, Schema.org JSON-LD for SEO, and wired navbar link with active state**

## Performance

- **Duration:** 1 min 26s
- **Started:** 2026-04-01T07:59:34Z
- **Completed:** 2026-04-01T08:01:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Recipe detail page with hero image, title, meta row (category badge, prep time, date), ingredients, steps, and sidebar
- Schema.org JSON-LD markup with @type Recipe, recipeIngredient array, HowToStep instructions, prepTime, absolute image URL
- Navbar Przepisy link wired to recipes:list URL with active state on all recipe pages

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement recipe_detail view with Schema.org JSON-LD** - `725179c` (feat)
2. **Task 2: Build full recipe detail template and wire navbar Przepisy link** - `2fe7557` (feat)

## Files Created/Modified
- `recipes/views.py` - Added json/mark_safe imports, built Schema.org JSON-LD dict with full structured data
- `templates/recipes/detail.html` - Full detail page with two-column layout, hero image, ingredients, steps, sidebar, JSON-LD in extra_js
- `templates/includes/_navbar.html` - Replaced placeholder Przepisy link with real URL and active state detection

## Decisions Made
- Used extra_css block for detail-specific styles to avoid conflicts with Plan 02 which owns main.css
- Navbar active state detection uses request.resolver_match.app_name == 'recipes' so it works on both list and detail pages

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Recipe reading experience complete (list + detail pages)
- Schema.org structured data ready for Google rich snippets
- All 20 recipe tests passing
- Ready for next phase (ebooks or shop)

---
*Phase: 03-recipes*
*Completed: 2026-04-01*
