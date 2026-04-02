---
phase: 04-shop
plan: 02
subsystem: ui
tags: [django-templates, css, catalog, pagination, cart, product-detail]

# Dependency graph
requires:
  - phase: 04-01
    provides: Product/ProductCategory models, Cart session class, shop URLs, seed categories
  - phase: 03-recipes
    provides: Filter pill CSS, pagination CSS, recipe list/detail template patterns
provides:
  - Product catalog page with category filter pills, card grid, pagination
  - Product detail page with two-column layout, delivery notes, add-to-cart form
  - Shop CSS classes (product card, badge-digital, price, delivery note, detail sidebar/hero)
affects: [04-03-cart-checkout]

# Tech tracking
tech-stack:
  added: []
  patterns: [product-card-component, detail-two-column-layout, filter-pill-reuse]

key-files:
  created:
    - templates/shop/list.html
    - templates/shop/detail.html
  modified:
    - shop/views.py
    - static/css/main.css

key-decisions:
  - "Moved shop templates from app-level (shop/templates/shop/) to project-level (templates/shop/) to match recipes pattern"

patterns-established:
  - "Product card with kk-product-card BEM classes reuses same structure as recipe card"
  - "Detail page two-column layout (col-lg-8 + col-lg-4 sidebar) with kk-detail-sidebar"
  - "Delivery note varies by product type (ebook vs physical) using kk-delivery-note class"

requirements-completed: [SHOP-01, SHOP-02, SHOP-03]

# Metrics
duration: 3min
completed: 2026-04-02
---

# Phase 04 Plan 02: Product Catalog & Detail Summary

**Product catalog with category filter pills, paginated card grid, and detail page with delivery notes and add-to-cart POST form**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-02T13:28:55Z
- **Completed:** 2026-04-02T13:31:55Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Product catalog page at /sklep/ with filter pills (Wszystkie + seeded categories), 3-column card grid, pagination, and empty states
- Product detail page at /sklep/<slug>/ with two-column layout, hero image, delivery notes per type, and working add-to-cart POST form
- Full shop CSS: product card, digital badge, price, delivery note, detail sidebar, detail hero image

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement product_list, product_detail, and cart_add views** - `2fa8baa` (feat)
2. **Task 2: Create product catalog template, product detail template, and all shop CSS** - `4accd6d` (feat)

## Files Created/Modified
- `shop/views.py` - Full product_list (paginated, category-filtered), product_detail (get_object_or_404), cart_add (@require_POST)
- `templates/shop/list.html` - Product catalog page with filter pills, card grid, pagination, empty states
- `templates/shop/detail.html` - Product detail page with two-column layout, delivery notes, add-to-cart form
- `static/css/main.css` - Added shop CSS: product card, badge-digital, price, delivery note, detail sidebar, detail hero

## Decisions Made
- Moved shop templates from app-level (shop/templates/shop/) to project-level (templates/shop/) directory to match the established recipes template pattern

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Removed app-level stub templates**
- **Found during:** Task 2
- **Issue:** Plan 01 created stub templates at shop/templates/shop/*.html; project-level templates at templates/shop/*.html would shadow them but leaving stubs creates confusion
- **Fix:** Deleted shop/templates/shop/list.html and shop/templates/shop/detail.html after creating project-level replacements
- **Files modified:** shop/templates/shop/list.html (deleted), shop/templates/shop/detail.html (deleted)
- **Verification:** All 29 shop tests pass
- **Committed in:** 4accd6d (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Cleanup of stub templates necessary to avoid template resolution confusion. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Catalog and detail pages complete, ready for Plan 03 (cart view, checkout flow)
- Cart add endpoint works, redirects to shop:cart (stub view returns 200)
- All CSS classes established for shop components

---
*Phase: 04-shop*
*Completed: 2026-04-02*
