---
phase: 11
slug: https-bezpiecze-stwo
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-16
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual verification + curl |
| **Config file** | brak |
| **Quick run command** | `curl -I https://kuchennakomitywa.pl` |
| **Full suite command** | Checklist 5 punktów z success criteria |
| **Estimated runtime** | ~2 minuty (manual) |

---

## Sampling Rate

- **After every task commit:** Run `curl -I https://kuchennakomitywa.pl`
- **After every plan wave:** Run full checklist (5 punktów)
- **Before `/gsd-verify-work`:** Wszystkie 5 punktów musi przejść
- **Max feedback latency:** ~120 sekund

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | HTTPS-01 | T-11-06 | Let's Encrypt issuer w certyfikacie | smoke | `curl -vI https://kuchennakomitywa.pl 2>&1 \| grep -i "issuer"` | ✅ | ⬜ pending |
| 11-01-02 | 01 | 1 | HTTPS-02 | T-11-01 | HTTP→HTTPS 301 redirect | smoke | `curl -I http://kuchennakomitywa.pl 2>&1 \| grep "301\|Location"` | ✅ | ⬜ pending |
| 11-01-03 | 01 | 1 | HTTPS-03 | T-11-02 | Brak błędu CSRF pod HTTPS | manual | Ręczny POST formularza logowania | N/A | ⬜ pending |
| 11-01-04 | 01 | 1 | HTTPS-04 | T-11-01 | Cookie Secure + HttpOnly flags | manual | DevTools → Application → Cookies | N/A | ⬜ pending |
| 11-01-05 | 01 | 1 | HTTPS-05 | T-11-03/04/05 | HSTS, X-Content-Type-Options, X-Frame-Options | smoke | `curl -I https://kuchennakomitywa.pl` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Brak — faza weryfikacyjna, nie wymaga pisania kodu testowego. Istniejąca infrastruktura (curl, przeglądarka, DevTools) pokrywa wszystkie wymagania.

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| POST formularze bez błędu CSRF | HTTPS-03 | Wymaga aktywnej sesji i przeglądarki | Otwórz stronę logowania pod https://, wypełnij i wyślij formularz, sprawdź czy nie pojawia się błąd 403 CSRF |
| Cookie flags Secure + HttpOnly | HTTPS-04 | Wymaga przeglądarki | Zaloguj się, otwórz DevTools → Application → Cookies → kuchennakomitywa.pl, sprawdź kolumny Secure i HttpOnly |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
