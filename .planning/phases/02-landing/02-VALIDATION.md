---
phase: 2
slug: landing
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Django TestCase (built-in) |
| **Config file** | None needed (Django default test runner) |
| **Quick run command** | `python manage.py test core -v2` |
| **Full suite command** | `python manage.py test -v2` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python manage.py test core -v2`
- **After every plan wave:** Run `python manage.py test -v2`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | LAND-01 | unit | `python manage.py test core.tests.TestHeroSection -v2` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | LAND-02 | unit | `python manage.py test core.tests.TestAboutPage -v2` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | LAND-03 | unit | `python manage.py test core.tests.TestContactPage -v2` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | LEGAL-01 | unit | `python manage.py test core.tests.TestPrivacyPage -v2` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | LEGAL-02 | unit | `python manage.py test core.tests.TestRegulationsPage -v2` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 1 | LAND-01 | unit | `python manage.py test core.tests.TestNavbarLinks -v2` | ❌ W0 | ⬜ pending |
| 02-03-02 | 03 | 1 | LAND-01 | unit | `python manage.py test core.tests.TestFooterLinks -v2` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `core/tests.py` — Add TestHeroSection: assert hero section content, CTA button, split layout classes
- [ ] `core/tests.py` — Add TestAboutPage: assert `/o-nas/` returns 200, has company story content
- [ ] `core/tests.py` — Add TestContactPage: assert `/kontakt/` returns 200, has address and hours
- [ ] `core/tests.py` — Add TestPrivacyPage: assert `/polityka-prywatnosci/` returns 200, has RODO content
- [ ] `core/tests.py` — Add TestRegulationsPage: assert `/regulamin/` returns 200, has regulations content
- [ ] `core/tests.py` — Add TestNavbarLinks: assert O nas and Kontakt links use `{% url %}` not `#`
- [ ] `core/tests.py` — Add TestFooterLinks: assert footer contains privacy and regulations links

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Hero layout splits on desktop, stacks on mobile | LAND-01 (D-01) | Requires visual viewport check | Resize browser to <768px, verify hero stacks vertically |
| Stock photos display correctly | D-11 | Requires visual check | Verify hero and section images load, are not distorted |
| Brand tone matches warm/personal style | D-12 | Subjective content quality | Read page copy, verify tone matches "Gotujemy z sercem" style |
| Legal pages have placeholder banner | D-08/D-09 | Requires visual check | Verify "UWAGA: Tekst wzorcowy" banner visible on legal pages |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
