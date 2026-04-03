---
phase: 5
slug: payments
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pytest.ini` or `pyproject.toml` (Wave 0 installs if missing) |
| **Quick run command** | `python manage.py test payments --verbosity=0` |
| **Full suite command** | `python manage.py test` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python manage.py test payments --verbosity=0`
- **After every plan wave:** Run `python manage.py test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 5-01-01 | 01 | 1 | PAY-01 | unit | `python manage.py test payments.tests.test_models` | ❌ W0 | ⬜ pending |
| 5-01-02 | 01 | 1 | PAY-01 | unit | `python manage.py test payments.tests.test_forms` | ❌ W0 | ⬜ pending |
| 5-02-01 | 02 | 2 | PAY-02 | unit | `python manage.py test payments.tests.test_views` | ❌ W0 | ⬜ pending |
| 5-02-02 | 02 | 2 | PAY-03 | unit | `python manage.py test payments.tests.test_webhook` | ❌ W0 | ⬜ pending |
| 5-03-01 | 03 | 3 | PAY-04 | unit | `python manage.py test payments.tests.test_email` | ❌ W0 | ⬜ pending |
| 5-03-02 | 03 | 3 | PAY-05 | unit | `python manage.py test payments.tests.test_ebook_delivery` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `payments/tests/__init__.py` — test package init
- [ ] `payments/tests/test_models.py` — stubs for Order, OrderItem models (PAY-01)
- [ ] `payments/tests/test_forms.py` — stubs for checkout form (PAY-01)
- [ ] `payments/tests/test_views.py` — stubs for checkout/confirmation views (PAY-02)
- [ ] `payments/tests/test_webhook.py` — stubs for Przelewy24 webhook handler (PAY-03)
- [ ] `payments/tests/test_email.py` — stubs for order confirmation email (PAY-04)
- [ ] `payments/tests/test_ebook_delivery.py` — stubs for PDF ebook delivery (PAY-05)

*Existing Django test infrastructure covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Przelewy24 sandbox payment flow end-to-end | PAY-02 | Requires live P24 sandbox credentials and network | Configure P24 sandbox, place test order, complete payment |
| Email delivery with PDF attachment | PAY-05 | Requires real SMTP or email delivery service | Place test ebook order, verify email arrives with PDF |
| CRC signature validation with real P24 secret | PAY-03 | Requires actual P24 CRC key | Configure P24 CRC key, trigger test notification |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
