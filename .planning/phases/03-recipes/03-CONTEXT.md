# Phase 3: Recipes - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers the recipe blog: a browsable, searchable, filterable list of vegan recipes with full detail pages, category navigation, and Schema.org JSON-LD markup for Google rich snippets. Admin manages recipes via Django admin. All pages extend base.html from Phase 1 with the established brand system.

New capabilities NOT in scope: ratings, comments, printing, social sharing, suggested recipes, serving-size scaling — these are v2.

</domain>

<decisions>
## Implementation Decisions

### Recipe List Page Layout
- **D-01:** 3-column card grid (Bootstrap col-lg-4, col-md-6, col-12). Standard blog grid — familiar pattern, reuses `.kk-section` layout rhythm.
- **D-02:** Each card shows: photo thumbnail, category badge, title, short description (1-2 sentence excerpt), and prep time (⏱ 30 min).
- **D-03:** Category filter bar at the top of the list — horizontal row of clickable pills: "Wszystkie | Śniadania | Obiady | Desery | Przekąski" (+ any other categories). Active pill highlighted in brand olive/sage color.

### Claude's Discretion
- Exact category list (admin-managed or hardcoded — pick what fits a small site best)
- Pagination vs load-more (standard Django paginator recommended)
- Recipe detail page layout (full-width or constrained column)
- Search implementation approach (form submit vs AJAX — simple form submit fine for v1)
- Ingredient storage (structured rows vs textarea — researcher should evaluate Django admin UX tradeoff)
- Difficulty field inclusion (not requested — omit unless needed for admin)
- Image storage (local media/ upload via Django FileField)
- Slug generation for recipe URLs

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `.planning/PROJECT.md` — Project vision, core value, constraints (Polish-only, Django templates, personal pickup)
- `.planning/REQUIREMENTS.md` — PRZE-01 through PRZE-06 (all recipe requirements)
- `.planning/ROADMAP.md` — Phase 3 success criteria (5 items)

### Prior Phase Outputs
- `.planning/phases/01-foundation/01-CONTEXT.md` — Brand decisions: sage/olive/cream palette, Lora/Nunito fonts, warm organic feel
- `.planning/phases/02-landing/02-CONTEXT.md` — Copywriting tone (D-12), content patterns, section layout decisions
- `.planning/phases/02-landing/02-01-SUMMARY.md` — CSS classes established: `.kk-section`, `.kk-section-alt`, `.kk-btn-primary`, `.kk-feature-icon`, `.kk-link-arrow`

### Codebase Reference
- `static/css/main.css` — CSS variables and existing component classes
- `core/urls.py` — URL patterns to extend (recipes need their own app and URL namespace)
- `templates/base.html` — Template structure to extend

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.kk-section` / `.kk-section-alt`: Alternating section backgrounds — reuse for recipe list page sections
- `.kk-btn-primary`: CTA button style — reuse for "Czytaj więcej" card CTAs
- Bootstrap 5 card component: Existing card patterns in Phase 2 feature cards — extend for recipe cards
- CSS variables: `--kk-sage`, `--kk-olive`, `--kk-olive-dark`, `--kk-cream` — use for category badge colors and active filter pill

### Established Patterns
- Views: function-based views in Django (no class-based views used yet — keep consistent)
- URLs: `path()` with named URLs, separate app URL files included from `backend/urls.py`
- Templates: `{% extends 'base.html' %}` with `{% block content %}` pattern
- No ORM models yet — Phase 3 introduces first Django models with migrations

### Integration Points
- `backend/urls.py`: Add `include('recipes.urls', namespace='recipes')` for `/przepisy/` prefix
- `templates/includes/_navbar.html`: "Przepisy" link is currently a placeholder — wire to `{% url 'recipes:list' %}` after this phase
- Django admin: Register Recipe and Category models (PRZE-06)

</code_context>

<specifics>
## Specific Ideas

- Category filter pills should use brand colors for active state (olive/sage) — consistent with existing nav active state pattern from Phase 2 (D-03 there: `request.resolver_match.url_name`)
- Cards: photo on top, content below — standard Bootstrap card structure. Photo aspect ratio should be consistent (e.g., 4:3 or 16:9 via CSS `object-fit: cover`)
- Warm, personal tone for any placeholder/empty-state copy — consistent with Phase 2 copywriting (D-12)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-recipes*
*Context gathered: 2026-03-31*
