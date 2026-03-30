---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Django TestCase (built-in, no extra dependency) |
| **Config file** | None needed (Django's default test runner) |
| **Quick run command** | `python manage.py test --verbosity=2` |
| **Full suite command** | `python manage.py test --verbosity=2` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python manage.py test --verbosity=2`
- **After every plan wave:** Run `python manage.py test --verbosity=2`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | FOUND-01 | unit | `python manage.py test core.tests.TestEnvironmentConfig -v2` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | FOUND-02 | integration | `python manage.py test core.tests.TestBaseTemplate -v2` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | FOUND-03 | integration | `python manage.py test core.tests.TestResponsiveLayout -v2` | ❌ W0 | ⬜ pending |
| 01-02-03 | 02 | 1 | FOUND-04 | integration | `python manage.py test core.tests.TestStaticFiles -v2` | ❌ W0 | ⬜ pending |
| 01-02-04 | 02 | 1 | FOUND-05 | unit | `python manage.py test core.tests.TestMediaConfig -v2` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | LEGAL-03 | integration | `python manage.py test core.tests.TestCookieBanner -v2` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `core/tests.py` — test stubs for FOUND-01 through FOUND-05, LEGAL-03
- [ ] Django app `core` created (or test module at project level)
- [ ] No framework install needed (Django TestCase already available)

*Existing infrastructure covers test framework — only test files need creation.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Mobile responsive layout | FOUND-03 | Visual check on different breakpoints | Open pages at 375px, 768px, 1024px widths — verify nav collapses, content reflows |
| Cookie banner positioning | LEGAL-03 | Visual placement verification | Load page with cleared localStorage — verify bottom bar appears, buttons visible |
| Brand visual feel | D-08/D-09 | Subjective design assessment | Verify warm/natural palette (greens, beiges), cozy kitchen feel |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
