---
phase: 8
slug: database-ssl
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-10
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing Django test runner) |
| **Config file** | `manage.py test` / `pytest.ini` if present |
| **Quick run command** | `python manage.py check --deploy` |
| **Full suite command** | `python manage.py test accounts` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python manage.py check --deploy`
- **After every plan wave:** Run `python manage.py test accounts`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | DB-01 | integration | `python manage.py dbshell --command "SELECT 1;"` | ✅ | ⬜ pending |
| 08-01-02 | 01 | 1 | DB-02 | integration | `python manage.py showmigrations --list` | ✅ | ⬜ pending |
| 08-01-03 | 01 | 1 | DB-03 | manual | Django admin login at production URL | ❌ W0 | ⬜ pending |
| 08-02-01 | 02 | 2 | SSL-01 | manual | `curl -I https://DOMAIN` | ❌ W0 | ⬜ pending |
| 08-02-02 | 02 | 2 | SSL-02 | manual | `curl -I http://DOMAIN` (expect 301) | ❌ W0 | ⬜ pending |
| 08-02-03 | 02 | 2 | SSL-03 | integration | `python manage.py check --deploy` (no warnings) | ✅ | ⬜ pending |
| 08-02-04 | 02 | 2 | SSL-04 | manual | POST login form under HTTPS, no CSRF error | ❌ W0 | ⬜ pending |
| 08-02-05 | 02 | 2 | SSL-05 | manual | Browser DevTools: cookie Secure+HttpOnly flags | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- `python manage.py check --deploy` — baseline Django deployment check (psycopg must be installed)

*Most verification is manual due to server-side SSL/network configuration nature of this phase.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| HTTPS certificate valid | SSL-01 | Requires live server + Let's Encrypt issuance | `curl -vI https://DOMAIN 2>&1 \| grep "SSL certificate"` |
| HTTP → HTTPS redirect | SSL-02 | Requires MyDevil sslonly option active | `curl -I http://DOMAIN` → expect 301 Location: https:// |
| Forms work under HTTPS | SSL-04 | Requires live HTTPS + login form interaction | POST to /admin/login/ under https://, no CSRF 403 |
| Cookie security flags | SSL-05 | Requires live browser session | DevTools → Application → Cookies → SESSION_ID: Secure✓ HttpOnly✓ |
| Cron ping active | SSL-05 | Requires MyDevil cron job | `devil cron list` shows ping entry every 12h |
| Admin access | DB-03 | Requires live server with superuser | Login at https://DOMAIN/admin/ with superuser credentials |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
