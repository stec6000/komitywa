---
phase: 10-payments-verification
plan: 02
status: complete
completed: 2026-04-16
---

# Summary: E2E Purchase Flow Verification

## What was done

Full end-to-end purchase flow verified on production with P24 sandbox payments and ebook PDF delivery.

## Results

- **E2E flow**: browse → cart → checkout → P24 sandbox payment → return page ✓
- **Webhook**: P24 posted to `https://kuchennakomitywa.pl/zamowienie/webhook/p24/` — order status set to "paid" ✓
- **Email 1**: Order confirmation email received ✓
- **Email 2**: Ebook delivery email with PDF attachment received ✓
- **Django admin**: Order status shows "paid" ✓

## Issues encountered

1. **P24 401 Unauthorized** — `P24_API_KEY` was set to "Klucz do zamówień" but the REST API v1 requires "Klucz do raportów". Fixed by updating `.env` on production.
2. **Ebook not sent** — Test product had `type = Physical` instead of `type = Ebook`. Fixed in Django admin. The `send_ebook_delivery` function silently returns when no ebook products found.

## Requirements signed off

- [x] P24-01: P24 sandbox payments work on production with correct webhook URL
- [x] P24-02: Ebook PDFs uploaded via Django admin and delivered by email
- [x] VER-01: Full purchase flow works end-to-end
- [x] VER-02: `python manage.py check --deploy` reports no warnings

## Milestone

**v1.1 Wdrożenie Produkcyjne — COMPLETE** (shipped 2026-04-16)
