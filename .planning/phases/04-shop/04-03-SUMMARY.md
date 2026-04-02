---
phase: 04-shop
plan: 03
subsystem: ui
tags: [django-templates, cart, checkout, forms, session, order]

requires:
  - phase: 04-shop-01
    provides: "Product/Order models, Cart session class, CheckoutForm, URLs, admin"
  - phase: 04-shop-02
    provides: "Product list/detail views, cart_add view, shop CSS, list/detail templates"
provides:
  - "Cart page with quantity controls, remove, empty state"
  - "Checkout form with LEGAL-04 consent checkboxes and Order persistence"
  - "Order confirmation placeholder page"
  - "Navbar wired to live shop URLs with dynamic cart badge"
affects: [05-payments, navbar, shop]

tech-stack:
  added: []
  patterns:
    - "POST-only cart mutations with @require_POST"
    - "Stale cart entry cleanup on cart_view"
    - "Empty cart redirect guard on checkout"
    - "Bootstrap widget attrs on Django form fields"

key-files:
  created:
    - templates/shop/cart.html
    - templates/shop/checkout.html
    - templates/shop/checkout_confirm.html
  modified:
    - shop/views.py
    - shop/forms.py
    - templates/includes/_navbar.html
    - static/css/main.css
    - shop/tests/test_views.py

key-decisions:
  - "Quantity +/- buttons submit pre-computed value via name=quantity on submit buttons"
  - "Ebook items show static '1' with no quantity controls (D-06)"
  - "Checkout confirmation is a placeholder for Phase 5 payment integration"

patterns-established:
  - "Cart item building: fetch products by session IDs, build products_map, remove stale"
  - "Form widget attrs in forms.py for Bootstrap styling consistency"

requirements-completed: [SHOP-03, SHOP-04, SHOP-05]

duration: 3min
completed: 2026-04-02
---

# Phase 04 Plan 03: Cart, Checkout, and Navbar Wiring Summary

**Session cart page with quantity controls, checkout form with LEGAL-04 consent and Order persistence, confirmation page, and navbar wired to live shop URLs with dynamic badge**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-02T18:34:42Z
- **Completed:** 2026-04-02T18:37:55Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Cart page displays items with thumbnails, quantity +/- controls (physical only), remove buttons, summary, and empty state
- Checkout form collects email, name, phone, pickup date, and two LEGAL-04 consent checkboxes with inline validation errors
- Order saved to database with cart_snapshot on valid submission, cart cleared, redirect to confirmation
- Navbar Sklep link and cart icon point to live URLs with active state and dynamic cart_count badge

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement cart views and checkout views** - `8362e6f` (feat)
2. **Task 2: Create templates and update navbar** - `84aeea2` (feat)

## Files Created/Modified
- `shop/views.py` - Full cart_view, cart_update, cart_remove, checkout, checkout_confirm implementations
- `shop/forms.py` - Added Bootstrap widget attrs to all CheckoutForm fields
- `shop/tests/test_views.py` - Updated checkout tests for empty cart redirect and order creation
- `templates/shop/cart.html` - Cart page with item list, quantity controls, summary, empty state
- `templates/shop/checkout.html` - Checkout form with order summary sidebar
- `templates/shop/checkout_confirm.html` - Order confirmation placeholder page
- `templates/includes/_navbar.html` - Sklep link and cart icon wired to live URLs with dynamic badge
- `static/css/main.css` - Cart item, quantity controls, cart summary, checkout form, order summary CSS

## Decisions Made
- Quantity +/- buttons use `name="quantity" value="{{ item.quantity|add:'1' }}"` pattern so each button submits the pre-computed new quantity directly
- Ebook items in cart show static "1" with no +/- controls per decision D-06
- Checkout confirmation is a static placeholder awaiting Phase 5 payment integration

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test for checkout empty cart redirect**
- **Found during:** Task 1
- **Issue:** Existing test expected 200 from GET /zamowienie/ but new implementation redirects empty cart to /koszyk/
- **Fix:** Updated TestCheckout to test empty cart redirect (302), added test with cart items (200), and test for POST order creation
- **Files modified:** shop/tests/test_views.py
- **Verification:** All 31 shop tests pass
- **Committed in:** 8362e6f (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Test update necessary to match new view behavior. No scope creep.

## Known Stubs
- `templates/shop/checkout_confirm.html` - Confirmation page is a static placeholder; will be wired to payment status in Phase 5 (intentional per plan)

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Full shopping flow complete: browse -> detail -> add to cart -> manage cart -> checkout -> confirmation
- Ready for Phase 5 payment integration (Przelewy24)
- Confirmation page placeholder awaits payment status wiring

## Self-Check: PASSED

All created files verified present. All commit hashes (8362e6f, 84aeea2) verified in git log. 98 tests pass (full suite).

---
*Phase: 04-shop*
*Completed: 2026-04-02*
