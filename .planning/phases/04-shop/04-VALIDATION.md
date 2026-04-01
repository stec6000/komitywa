---
phase: 4
slug: shop
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-01
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pytest.ini` or `setup.cfg` (none yet — Wave 0 installs) |
| **Quick run command** | `python manage.py test shop --verbosity=0` |
| **Full suite command** | `python manage.py test` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python manage.py test shop --verbosity=0`
- **After every plan wave:** Run `python manage.py test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 01 | 1 | SHOP-01 | unit | `python manage.py test shop.tests.test_models` | ❌ W0 | ⬜ pending |
| 4-01-02 | 01 | 1 | SHOP-01 | unit | `python manage.py test shop.tests.test_models` | ❌ W0 | ⬜ pending |
| 4-01-03 | 01 | 1 | SHOP-02 | unit | `python manage.py test shop.tests.test_models` | ❌ W0 | ⬜ pending |
| 4-02-01 | 02 | 1 | SHOP-03 | integration | `python manage.py test shop.tests.test_views` | ❌ W0 | ⬜ pending |
| 4-02-02 | 02 | 1 | SHOP-03 | integration | `python manage.py test shop.tests.test_views` | ❌ W0 | ⬜ pending |
| 4-03-01 | 03 | 2 | SHOP-04 | integration | `python manage.py test shop.tests.test_cart` | ❌ W0 | ⬜ pending |
| 4-03-02 | 03 | 2 | SHOP-04 | integration | `python manage.py test shop.tests.test_cart` | ❌ W0 | ⬜ pending |
| 4-03-03 | 03 | 2 | SHOP-05 | integration | `python manage.py test shop.tests.test_cart` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `shop/tests/__init__.py` — test package
- [ ] `shop/tests/test_models.py` — stubs for SHOP-01, SHOP-02, SHOP-03
- [ ] `shop/tests/test_views.py` — stubs for SHOP-03 catalog/product views
- [ ] `shop/tests/test_cart.py` — stubs for SHOP-04, SHOP-05 cart operations
- [ ] `shop/tests/conftest.py` — shared fixtures (test products, categories)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Cart badge count updates in navbar without page reload | SHOP-04 | Requires browser JS interaction | Add item to cart, verify navbar badge increments |
| Admin product image upload and display | SHOP-06 | Requires file upload UI interaction | Upload image in admin, verify it appears on product page |
| Ebook quantity locked to 1 in cart | SHOP-02 | UX enforcement requires browser test | Add ebook to cart, attempt to change quantity, verify it stays at 1 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
