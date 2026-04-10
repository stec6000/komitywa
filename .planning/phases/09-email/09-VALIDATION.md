---
phase: 9
slug: email
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-10
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing Django test runner) |
| **Config file** | `manage.py test` |
| **Quick run command** | `python manage.py check` |
| **Full suite command** | `python manage.py test accounts newsletter shop` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python manage.py check`
- **After every plan wave:** Run `python manage.py test accounts newsletter shop`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | EMAIL-01 | unit | `grep -r "email_confirmation" templates/account/email/` | ✅ | ⬜ pending |
| 09-01-02 | 01 | 1 | EMAIL-03 | unit | `python manage.py test accounts` | ✅ | ⬜ pending |
| 09-01-03 | 01 | 1 | EMAIL-04 | unit | `python manage.py test accounts` | ✅ | ⬜ pending |
| 09-02-01 | 02 | 2 | EMAIL-01 | manual | Send test email via Brevo SMTP, check inbox | ❌ W0 | ⬜ pending |
| 09-02-02 | 02 | 2 | EMAIL-02 | manual | Brevo dashboard shows domain verified | ❌ W0 | ⬜ pending |
| 09-02-03 | 02 | 2 | EMAIL-03 | manual | Register on production, receive Polish verification email | ❌ W0 | ⬜ pending |
| 09-02-04 | 02 | 2 | EMAIL-04 | manual | Request password reset, receive Polish email, complete reset | ❌ W0 | ⬜ pending |
| 09-02-05 | 02 | 2 | EMAIL-05 | manual | Place test order, receive order confirmation with PDF | ❌ W0 | ⬜ pending |
| 09-02-06 | 02 | 2 | EMAIL-06 | manual | Subscribe to newsletter, receive Polish double opt-in email | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- `templates/account/email/` directory with Polish .txt templates (created in Wave 1)

*Most end-to-end email verification is manual (requires live SMTP and production server).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Emails arrive in inbox (not spam) | EMAIL-01 | Requires live SMTP + real mailbox | Send test email from Django shell: `python manage.py shell -c "from django.core.mail import send_mail; send_mail('Test', 'body', None, ['your@email.com'])"` |
| SPF/DKIM verified in Brevo | EMAIL-02 | Requires Brevo dashboard + DNS propagation | Brevo → Senders → Domains → kuchennakomitywa.pl → Status: Authenticated |
| Registration verification email | EMAIL-03 | Requires production registration flow | Register new account on https://kuchennakomitywa.pl, check email |
| Password reset email | EMAIL-04 | Requires production reset flow | Request password reset, check email, complete reset |
| Order confirmation with PDF | EMAIL-05 | Requires live order + payment sandbox | Place test order, verify email received with PDF attachment |
| Newsletter double opt-in | EMAIL-06 | Requires live newsletter signup | Subscribe to newsletter, verify Polish confirmation email |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
