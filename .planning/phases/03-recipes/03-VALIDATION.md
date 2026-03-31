---
phase: 3
slug: recipes
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Django TestCase (built-in, no extra package) |
| **Config file** | `backend/settings.py` (`DATABASES`, `INSTALLED_APPS`) |
| **Quick run command** | `python3 manage.py test recipes --verbosity=0` |
| **Full suite command** | `python3 manage.py test --verbosity=0` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 manage.py test recipes --verbosity=0`
- **After every plan wave:** Run `python3 manage.py test --verbosity=0`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 0 | PRZE-01–06 | unit stubs | `python3 manage.py test recipes --verbosity=0` | ❌ W0 | ⬜ pending |
| 3-01-02 | 01 | 1 | PRZE-01 | unit (HTTP) | `python3 manage.py test recipes.tests.TestRecipeList -x` | ❌ W0 | ⬜ pending |
| 3-01-03 | 01 | 1 | PRZE-02 | unit (HTTP) | `python3 manage.py test recipes.tests.TestRecipeDetail -x` | ❌ W0 | ⬜ pending |
| 3-02-01 | 02 | 2 | PRZE-03 | unit (HTTP) | `python3 manage.py test recipes.tests.TestCategoryFilter -x` | ❌ W0 | ⬜ pending |
| 3-02-02 | 02 | 2 | PRZE-04 | unit (HTTP) | `python3 manage.py test recipes.tests.TestRecipeSearch -x` | ❌ W0 | ⬜ pending |
| 3-03-01 | 03 | 3 | PRZE-05 | unit (HTTP) | `python3 manage.py test recipes.tests.TestSchemaOrgMarkup -x` | ❌ W0 | ⬜ pending |
| 3-03-02 | 03 | 3 | PRZE-06 | unit (admin) | `python3 manage.py test recipes.tests.TestRecipeAdmin -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `recipes/tests.py` — stubs for all 6 test classes (TestRecipeList, TestRecipeDetail, TestCategoryFilter, TestRecipeSearch, TestSchemaOrgMarkup, TestRecipeAdmin)
- [ ] `recipes/migrations/0001_initial.py` — auto-generated after model definition
- [ ] `recipes/__init__.py`, `recipes/apps.py`, `recipes/models.py`, `recipes/views.py`, `recipes/urls.py`, `recipes/admin.py`
- [ ] `templates/recipes/list.html` and `templates/recipes/detail.html`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Recipe images display correctly in browser | PRZE-01, PRZE-02 | Visual check — automated test verifies URL presence only | Open `/przepisy/` in browser, confirm images render without broken icons |
| Category pill active state styling | PRZE-03 | CSS visual state | Filter by a category, confirm active pill shows brand olive/sage color |
| Schema.org rich snippet preview | PRZE-05 | Google tool required | Paste recipe URL into Google Rich Results Test, confirm Recipe card preview |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
