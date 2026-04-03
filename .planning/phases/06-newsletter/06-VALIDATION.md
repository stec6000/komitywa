---
phase: 6
slug: newsletter
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Django TestCase (unittest-based) |
| **Config file** | None (Django default test runner) |
| **Quick run command** | `python3 manage.py test newsletter -v2` |
| **Full suite command** | `python3 manage.py test -v2` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 manage.py test newsletter -v2`
- **After every plan wave:** Run `python3 manage.py test -v2`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 0 | NEWS-01 | unit | `python3 manage.py test newsletter.tests.test_views -v2` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 0 | NEWS-02 | unit | `python3 manage.py test newsletter.tests.test_emails -v2` | ❌ W0 | ⬜ pending |
| 06-01-03 | 01 | 0 | NEWS-03 | unit | `python3 manage.py test newsletter.tests.test_views -v2` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `newsletter/tests/__init__.py` — package init
- [ ] `newsletter/tests/test_models.py` — model creation, token generation, expiry check
- [ ] `newsletter/tests/test_views.py` — all view tests (subscribe, confirm, unsubscribe flows)
- [ ] `newsletter/tests/test_emails.py` — confirmation email content and sending

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| RODO checkbox is required (form won't submit without it) | NEWS-01 | Browser-level HTML5 `required` attr | Load signup form, try submit without checkbox, confirm browser blocks |
| Confirmation email renders correctly in email client | NEWS-02 | Email rendering varies by client | Check console backend output in dev, verify token URL format |
| Unsubscribe link in confirmation email is clickable | NEWS-03 | Email link validation | Check console backend output, verify URL resolves |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
