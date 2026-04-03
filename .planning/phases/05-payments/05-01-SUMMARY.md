---
phase: 05-payments
plan: 01
subsystem: payments
tags: [przelewy24, p24, email, sha384, django-environ]

# Dependency graph
requires:
  - phase: 04-shop
    provides: Order model, Product model, checkout flow, admin registration
provides:
  - Order.p24_session_id field for P24 transaction matching
  - Product.ebook_file field for PDF delivery
  - shop/payment.py P24 API client (sign, register, verify, payment URL)
  - shop/emails.py email module (order confirmation, ebook delivery)
  - P24 and email settings via django-environ
affects: [05-payments-02, deployment]

# Tech tracking
tech-stack:
  added: [requests (P24 HTTP client), hashlib-sha384 (P24 sign)]
  patterns: [P24 compact-JSON sign calculation, email with PDF attachment, graceful attachment error logging]

key-files:
  created: [shop/payment.py, shop/emails.py, shop/tests/test_payment.py, shop/tests/test_emails.py, shop/migrations/0003_order_p24_session_id_product_ebook_file.py]
  modified: [shop/models.py, shop/admin.py, backend/settings.py, .env.example, shop/tests/test_views.py]

key-decisions:
  - "P24 sign uses SHA-384 on compact JSON (no spaces) per P24 REST API spec"
  - "Ebook delivery gracefully logs attachment errors without raising (D-10 resilience)"

patterns-established:
  - "P24 sign: json.dumps(params, separators=(',',':')) then SHA-384 hexdigest"
  - "Email attachment failure: log error, continue sending without attachment"

requirements-completed: [PAY-01, PAY-02, PAY-04, PAY-05, PAY-06, LEGAL-04]

# Metrics
duration: 4min
completed: 2026-04-03
---

# Phase 05 Plan 01: Payments Building Blocks Summary

**P24 payment client with SHA-384 sign, email module with Polish copy and ebook PDF attachment, model migrations for p24_session_id and ebook_file**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-03T10:10:24Z
- **Completed:** 2026-04-03T10:15:10Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 11

## Accomplishments
- P24 API client module with sign calculation, transaction register/verify, payment URL generation
- Email module sending order confirmation with Polish diacritics and ebook delivery with PDF attachments
- Model migrations adding p24_session_id to Order and ebook_file to Product
- P24 and email settings integrated via django-environ with .env.example documentation
- 15 new tests (7 payment, 8 email) all passing alongside 31 existing shop tests (46 total)

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing tests** - `96c2202` (test)
2. **Task 1 (GREEN): Implementation** - `7e8f107` (feat)

## Files Created/Modified
- `shop/payment.py` - P24 API client: calculate_sign, register_transaction, verify_transaction, get_payment_url
- `shop/emails.py` - Email sending: send_order_confirmation, send_ebook_delivery with PDF attachments
- `shop/models.py` - Added p24_session_id to Order, ebook_file to Product
- `shop/admin.py` - OrderAdmin updated with p24_session_id in readonly_fields and list_display
- `backend/settings.py` - P24_MERCHANT_ID/POS_ID/CRC_KEY/API_KEY/SANDBOX and EMAIL_* settings
- `.env.example` - Documented all P24 and email environment variables
- `shop/migrations/0003_order_p24_session_id_product_ebook_file.py` - Migration for new fields
- `shop/tests/test_payment.py` - 7 tests for P24 client functions
- `shop/tests/test_emails.py` - 8 tests for email functions
- `shop/tests/test_views.py` - Added TODO comment for Plan 02 checkout redirect update

## Decisions Made
- P24 sign calculation uses SHA-384 on compact JSON (no spaces) per Przelewy24 REST API specification
- Ebook delivery gracefully logs attachment errors without raising exceptions (D-10 resilience pattern)
- Email test for ebook attachment uses unittest.mock PropertyMock to patch ebook_file.path rather than manipulating MEDIA_ROOT

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed ebook attachment test using PropertyMock instead of temp MEDIA_ROOT**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** FileField.path resolves via Django storage backend which uses MEDIA_ROOT at initialization time; setting MEDIA_ROOT after field creation does not affect path resolution
- **Fix:** Used `unittest.mock.patch` with `PropertyMock` to mock `ebook_file.path` directly to the temp PDF file
- **Files modified:** shop/tests/test_emails.py
- **Verification:** Test passes, attachment is correctly included
- **Committed in:** 7e8f107

---

**Total deviations:** 1 auto-fixed (1 bug fix in test setup)
**Impact on plan:** Test fixture correction only. No scope creep.

## Issues Encountered
None beyond the test fixture issue documented above.

## User Setup Required
None - no external service configuration required at this stage. P24 credentials will be needed for live testing in Plan 02 integration.

## Next Phase Readiness
- All building blocks ready for Plan 02: payment views, webhook, checkout integration
- shop/payment.py exports: calculate_sign, register_transaction, verify_transaction, get_payment_url, get_base_url
- shop/emails.py exports: send_order_confirmation, send_ebook_delivery
- Order.p24_session_id available for session tracking
- Product.ebook_file available for PDF delivery

## Self-Check: PASSED

All 9 created/modified files verified present. Both commit hashes (96c2202, 7e8f107) verified in git log.

---
*Phase: 05-payments*
*Completed: 2026-04-03*
