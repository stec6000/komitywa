---
phase: 05-payments
plan: 02
subsystem: payments
tags: [przelewy24, p24, webhook, csrf, payment-flow, django-views]

# Dependency graph
requires:
  - phase: 05-01
    provides: P24 payment client (register_transaction, verify_transaction, calculate_sign), email module (send_order_confirmation, send_ebook_delivery), Order.p24_session_id field
provides:
  - Checkout POST creates Order, registers P24 transaction, redirects to P24 payment page
  - P24 webhook receives confirmation, verifies sign, calls verify_transaction, updates Order to paid, sends emails
  - Return page shows pending confirmation with order number
  - Cancel page restores cart from order snapshot and marks order cancelled
  - URL patterns for webhook, return, and cancel endpoints
affects: [06-newsletter, production-deployment]

# Tech tracking
tech-stack:
  added: []
  patterns: [csrf_exempt webhook, P24 sign verification, cart snapshot restore on cancel]

key-files:
  created:
    - templates/shop/p24_return.html
    - templates/shop/p24_cancel.html
  modified:
    - shop/views.py
    - shop/urls.py
    - shop/tests/test_views.py
    - templates/shop/checkout_confirm.html

key-decisions:
  - "Checkout redirects to shop:p24_cancel on P24 registration failure (restores cart, cancels order)"
  - "Return page does NOT check order.status - shows pending message per D-05 design decision"
  - "checkout_confirm view now redirects to home (replaced by p24_return)"

patterns-established:
  - "Webhook sign verification: calculate expected sign from received data + CRC key, compare with received sign"
  - "Cart restore pattern: store cart_snapshot in Order, restore to session on cancel/failure"
  - "Email error isolation: each email send wrapped in try/except, logged but never crashes webhook"

requirements-completed: [PAY-01, PAY-02, PAY-03]

# Metrics
duration: 3min
completed: 2026-04-03
---

# Phase 05 Plan 02: Payment Flow Views Summary

**End-to-end P24 payment flow: checkout creates order + redirects to P24, webhook confirms payment + sends emails, return/cancel pages with cart restore**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-03T10:18:12Z
- **Completed:** 2026-04-03T10:21:56Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Checkout POST creates Order with unique p24_session_id, registers P24 transaction, and redirects to P24 payment page
- P24 webhook verifies sign with CRC, calls verify_transaction, updates Order to paid, sends confirmation + ebook emails
- Return page shows pending confirmation with hourglass icon and order number
- Cancel page restores cart from order.cart_snapshot and shows failure with retry CTA
- All 23 view tests pass with mocked P24 API calls (57 total shop tests pass)

## Task Commits

Each task was committed atomically:

1. **Task 1: Checkout + Webhook + Return/Cancel views (RED)** - `61be90e` (test)
2. **Task 1: Checkout + Webhook + Return/Cancel views (GREEN)** - `20bf43f` (feat)
3. **Task 2: Payment status page templates** - `ab6b978` (feat)

## Files Created/Modified
- `shop/views.py` - Added checkout P24 flow, p24_webhook, p24_return, p24_cancel views
- `shop/urls.py` - Added webhook/p24/, powrot/, anulowano/ URL patterns
- `shop/tests/test_views.py` - Added TestP24Webhook, TestP24Return, TestP24Cancel test classes
- `templates/shop/p24_return.html` - Payment return page with hourglass icon and order number
- `templates/shop/p24_cancel.html` - Payment failure page with exclamation icon and retry CTA
- `templates/shop/checkout_confirm.html` - Simplified to redirect notice (view redirects to home)

## Decisions Made
- Checkout redirects to shop:p24_cancel on P24 registration failure (restores cart, cancels order)
- Return page does NOT check order.status -- shows pending message per D-05 design decision
- checkout_confirm view now redirects to home (replaced by p24_return)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

**External services require manual configuration.** P24 sandbox credentials needed:
- `P24_MERCHANT_ID` - from Przelewy24 panel
- `P24_POS_ID` - from Przelewy24 panel
- `P24_CRC_KEY` - from Przelewy24 panel
- `P24_API_KEY` - from Przelewy24 panel
- Webhook URL must be configured in P24 panel: `{domain}/zamowienie/webhook/p24/`

## Known Stubs

None - all views are fully wired to payment.py and emails.py modules from Plan 01.

## Next Phase Readiness
- Complete payment flow ready for production testing with real P24 sandbox credentials
- Phase 05 (payments) complete -- ready for Phase 06 (newsletter)

## Self-Check: PASSED

All 7 files verified present. All 3 commits verified in git log.

---
*Phase: 05-payments*
*Completed: 2026-04-03*
