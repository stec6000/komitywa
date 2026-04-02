---
phase: 04-shop
plan: 01
subsystem: database
tags: [django, models, session-cart, admin, forms]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: Django project skeleton, accounts app, settings.py
provides:
  - ProductCategory, Product, Order models with migrations
  - Session-based Cart class with ebook quantity lock
  - cart_count context processor for navbar badge
  - CheckoutForm with LEGAL-04 consent fields
  - Admin configuration for all shop models
  - URL routing for /sklep/, /koszyk/, /zamowienie/
  - Test scaffold (29 tests) covering SHOP-01 through SHOP-06
  - 3 seeded product categories via data migration
affects: [04-02, 04-03, 05-payments]

# Tech tracking
tech-stack:
  added: []
  patterns: [session-cart-pattern, data-migration-seeding, tdd-red-green]

key-files:
  created:
    - shop/models.py
    - shop/cart.py
    - shop/context_processors.py
    - shop/forms.py
    - shop/admin.py
    - shop/urls.py
    - shop/views.py
    - shop/migrations/0001_initial.py
    - shop/migrations/0002_seed_categories.py
    - shop/tests/test_models.py
    - shop/tests/test_cart.py
    - shop/tests/test_views.py
    - shop/templates/shop/list.html
    - shop/templates/shop/detail.html
    - shop/templates/shop/cart.html
    - shop/templates/shop/checkout.html
    - shop/templates/shop/checkout_confirm.html
  modified:
    - backend/settings.py
    - backend/urls.py

key-decisions:
  - "All shop URLs in single shop/urls.py mounted at root with explicit path prefixes to match UI-SPEC URLs"
  - "Tests use get_or_create for categories to avoid conflicts with seed migration data"

patterns-established:
  - "Session cart: store product_id as str key with quantity and price as str in request.session"
  - "Ebook quantity lock: product.type == 'ebook' always sets quantity to 1"
  - "Data migration seeding: get_or_create pattern with reverse migration for idempotent seeds"

requirements-completed: [SHOP-01, SHOP-06]

# Metrics
duration: 4min
completed: 2026-04-02
---

# Phase 04 Plan 01: Shop App Foundation Summary

**Django shop app with ProductCategory/Product/Order models, session-based Cart with ebook quantity lock, CheckoutForm with LEGAL-04 consent fields, and 29 passing tests**

## Performance

- **Duration:** 3m 51s
- **Started:** 2026-04-02T13:20:17Z
- **Completed:** 2026-04-02T13:24:08Z
- **Tasks:** 1 (TDD: red + green)
- **Files modified:** 22

## Accomplishments
- ProductCategory, Product, Order models fully migrated with all required fields
- Session-based Cart class with ebook quantity lock (D-06), add/remove/update/clear/iterate
- CheckoutForm with 6 fields including two LEGAL-04 consent BooleanFields
- Admin registered for all 3 models with list_display, list_filter, search_fields, prepopulated_fields
- All UI-SPEC URLs registered (/sklep/, /koszyk/, /zamowienie/) with stub views returning 200
- 3 default categories seeded via data migration (Ebooki, Dania w sloiku, Ciasta)
- 29 passing tests covering models, cart operations, forms, views, and admin

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Test scaffold** - `1ab20b2` (test)
2. **Task 1 GREEN: Full implementation** - `6f1caa4` (feat)

## Files Created/Modified
- `shop/models.py` - ProductCategory, Product, Order models
- `shop/cart.py` - Session-based Cart class with ebook quantity lock
- `shop/context_processors.py` - cart_count for navbar badge
- `shop/forms.py` - CheckoutForm with LEGAL-04 consent fields
- `shop/admin.py` - Admin for ProductCategory, Product, Order
- `shop/urls.py` - All shop URL patterns matching UI-SPEC
- `shop/views.py` - Stub views returning 200
- `shop/migrations/0001_initial.py` - Schema migration
- `shop/migrations/0002_seed_categories.py` - Seed 3 categories
- `shop/tests/test_models.py` - Model tests (7 tests)
- `shop/tests/test_cart.py` - Cart and context processor tests (11 tests)
- `shop/tests/test_views.py` - View, form, and admin tests (11 tests)
- `shop/templates/shop/*.html` - 5 stub templates
- `backend/settings.py` - Added shop to INSTALLED_APPS and context processor
- `backend/urls.py` - Added shop URL include

## Decisions Made
- All shop URLs placed in a single `shop/urls.py` with explicit path prefixes (`sklep/`, `koszyk/`, `zamowienie/`) mounted at root in `backend/urls.py`, keeping everything in the `shop` namespace while matching UI-SPEC URLs exactly
- Tests use `get_or_create` for ProductCategory to avoid UNIQUE constraint conflicts with seed migration data that runs in the test database

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test data conflicts with seed migration**
- **Found during:** Task 1 GREEN phase
- **Issue:** Tests creating ProductCategory with slug="ebooki" conflicted with seed migration 0002 which also creates that slug, causing IntegrityError
- **Fix:** Changed tests to use `get_or_create` instead of `create` for categories, and used unique slugs in ordering test
- **Files modified:** shop/tests/test_models.py, shop/tests/test_cart.py, shop/tests/test_views.py
- **Verification:** All 29 tests pass
- **Committed in:** 6f1caa4

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary fix for test/migration coexistence. No scope creep.

## Issues Encountered
None beyond the seed migration conflict documented above.

## Known Stubs
- `shop/views.py` - All 8 views are stubs (render empty template or redirect). This is intentional per plan -- real implementation comes in Plans 02 and 03.
- `shop/templates/shop/*.html` - 5 minimal stub templates without base.html extension. Real templates come in Plan 02.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All models and cart logic ready for Plan 02 (catalog views and templates)
- URL routing established for Plan 03 (checkout flow)
- Test scaffold ready for expansion as views get real implementation

---
*Phase: 04-shop*
*Completed: 2026-04-02*
