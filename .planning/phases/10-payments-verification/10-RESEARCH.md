# Phase 10: Payments & Verification — Research

**Researched:** 2026-04-11
**Domain:** Przelewy24 sandbox integration, Django security deployment, ebook email delivery
**Confidence:** HIGH (code read directly; P24 panel behavior from multiple Polish sources)

---

## Summary

Phase 10 has no greenfield code to write. The P24 integration, order flow, email sending, and ebook attachment logic are **fully coded and correct**. The work is entirely operational: configure P24 sandbox credentials in the production `.env`, fix six `manage.py check --deploy` warnings, upload a test ebook PDF via Django admin, and run the end-to-end purchase flow to verify everything works.

Two warnings from `check --deploy` require code changes in `settings.py` (silencing `security.W008` since Apache handles SSL redirect, and removing two deprecated allauth settings). Four warnings are fixed by setting environment variables on production. No new Python packages are needed.

**Primary recommendation:** Fix `settings.py` first (two edits), then configure production `.env`, then verify E2E flow.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| P24-01 | P24 sandbox payments work on production with correct webhook URL pointing to production HTTPS domain | Webhook URL is auto-built from `request.build_absolute_uri()` — works correctly once prod credentials are in `.env`. P24 panel needs IP set to `%` wildcard. |
| P24-02 | Ebook PDFs uploaded through Django admin on production and accessible for delivery | `Product.ebook_file` FileField uploads to `public/media/ebooks/`. Admin already exposes the field. MyDevil serves `public/` as static — files are accessible. |
| VER-01 | Full end-to-end flow verified: browse → cart → checkout → P24 sandbox → confirmation email with ebook PDF | All code exists. Requires prod credentials + test ebook uploaded. |
| VER-02 | `python manage.py check --deploy` reports no security warnings | 8 warnings found. 2 require code changes. 4 require `.env` env vars. 2 are deprecated allauth settings requiring code removal. |
</phase_requirements>

---

## Standard Stack

No new dependencies needed. Existing stack handles everything:

| Component | Status | Notes |
|-----------|--------|-------|
| `shop/payment.py` | Complete | Registers, verifies, builds payment URL |
| `shop/views.py` — `p24_webhook` | Complete | Verifies sign, finds order, calls verify, sends emails |
| `shop/emails.py` — `send_ebook_delivery` | Complete | Attaches `product.ebook_file.path` to EmailMessage |
| `shop/emails.py` — `send_order_confirmation` | Complete | Sends order summary |
| `shop/admin.py` — `ProductAdmin` | Complete | Exposes `ebook_file` field for upload |

**No `pip install` needed for Phase 10.**

---

## Architecture Patterns

### How the P24 Flow Works (verified from code)

```
checkout POST
  → Order.create() + p24_session_id = "order-{id}-{uuid}"
  → register_transaction() → POST sandbox.przelewy24.pl/api/v1/transaction/register
      payload: merchantId, posId, sessionId, amount, currency, email,
               urlReturn = https://kuchennakomitywa.pl/zamowienie/powrot/?order_id=X
               urlStatus = https://kuchennakomitywa.pl/zamowienie/webhook/p24/
  → redirect to sandbox.przelewy24.pl/trnRequest/{token}

[user pays in P24 sandbox UI]

P24 sends POST to urlStatus (webhook)
  → p24_webhook() verifies sign (SHA-384 of JSON fields + CRC key)
  → verify_transaction() → PUT sandbox.przelewy24.pl/api/v1/transaction/verify
  → order.status = "paid"
  → send_order_confirmation(order)  ← plain text email
  → send_ebook_delivery(order)      ← attaches PDF from product.ebook_file.path
```

### Webhook URL auto-build (confirmed in views.py line 154)

```python
url_status = request.build_absolute_uri("/zamowienie/webhook/p24/")
```

With `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` already set in `settings.py`, this correctly returns `https://kuchennakomitywa.pl/zamowienie/webhook/p24/` on production. **No code change needed for the webhook URL.**

### Media File Serving on MyDevil

`MEDIA_ROOT = BASE_DIR / "public" / "media"` — MyDevil serves all files under `public/` as static files via Apache without Django processing. Uploaded ebooks land at:

```
/usr/home/LOGIN/domains/kuchennakomitywa.pl/public_python/public/media/ebooks/filename.pdf
```

Apache serves `/media/ebooks/filename.pdf` directly. `product.ebook_file.path` returns the absolute filesystem path, which `email.attach_file()` reads correctly. **This works as-is on production.**

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Webhook sign verification | Custom HMAC | Existing `calculate_sign()` in `payment.py` | Already implements SHA-384 JSON signing correctly |
| PDF email attachment | Manual file read + base64 | `email.attach_file(path, "application/pdf")` | Django EmailMessage handles MIME encoding |
| P24 transaction verify | Re-implement HTTP client | Existing `verify_transaction()` | Already correct |

---

## `manage.py check --deploy` — Full Warning Analysis

Running `python3 manage.py check --deploy` from the repo root (with dev `.env`) produced **8 warnings**. Analysis of each:

### Warnings requiring CODE changes in `settings.py`

#### 1. security.W008 — SECURE_SSL_REDIRECT not True
```
Your SECURE_SSL_REDIRECT setting is not set to True.
```
**Root cause:** Apache on MyDevil handles HTTP→HTTPS redirect. Setting `SECURE_SSL_REDIRECT=True` would cause Django to double-redirect. The existing comment in `settings.py` explicitly says "False — Apache handles it".

**Fix:** Silence this check. Add to `settings.py`:
```python
SILENCED_SYSTEM_CHECKS = ["security.W008"]
```
**Confidence:** HIGH — Django docs explicitly state: "If your Django app is behind a reverse proxy that already redirects HTTP to HTTPS, you can silence this check." (See: https://docs.djangoproject.com/en/5.2/ref/checks/)

#### 2. Deprecated allauth settings (2 warnings)
```
settings.ACCOUNT_EMAIL_REQUIRED is deprecated, use: ACCOUNT_SIGNUP_FIELDS
settings.ACCOUNT_USERNAME_REQUIRED is deprecated, use: ACCOUNT_SIGNUP_FIELDS
```
**Root cause:** `settings.py` has both `ACCOUNT_SIGNUP_FIELDS` (lines 153–157, correct) AND the deprecated `ACCOUNT_USERNAME_REQUIRED = False` (line 160) and `ACCOUNT_EMAIL_REQUIRED = True` (line 161).

**Fix:** Remove the two deprecated lines from `settings.py`:
```python
# DELETE these two lines:
ACCOUNT_USERNAME_REQUIRED = False   # line 160 — covered by ACCOUNT_SIGNUP_FIELDS
ACCOUNT_EMAIL_REQUIRED = True       # line 161 — covered by ACCOUNT_SIGNUP_FIELDS
```

### Warnings fixed by production `.env` (no code change)

| Warning | Code | Fix via `.env` |
|---------|------|----------------|
| SECRET_KEY too short / insecure prefix | security.W009 | `SECRET_KEY=<50+ char random string>` |
| SESSION_COOKIE_SECURE not True | security.W012 | `SESSION_COOKIE_SECURE=True` |
| CSRF_COOKIE_SECURE not True | security.W016 | `CSRF_COOKIE_SECURE=True` |
| DEBUG is True | security.W018 | `DEBUG=False` |

**Note:** `SECURE_HSTS_SECONDS` (security.W004) does NOT appear in the `check --deploy` output as a blocking warning when `SILENCED_SYSTEM_CHECKS` silences W008. However, if HSTS is already configured in production `.env` from Phase 8 (`SECURE_HSTS_SECONDS=31536000`), W004 resolves automatically.

### Summary: what the plan must include

| Action | Type | Where |
|--------|------|-------|
| Add `SILENCED_SYSTEM_CHECKS = ["security.W008"]` | Code change | `settings.py` |
| Remove `ACCOUNT_USERNAME_REQUIRED` and `ACCOUNT_EMAIL_REQUIRED` lines | Code change | `settings.py` |
| Verify production `.env` has `DEBUG=False`, secure cookies, strong SECRET_KEY | Ops check | SSH to production |
| Run `check --deploy` on production and confirm 0 warnings | Verification | SSH to production |

---

## P24 Sandbox Configuration

### What the user needs from the P24 panel

**Source:** Multiple Polish integration guides (jdm.pl, comarchesklep.pl, nakiedy.pl, official P24 help center)

#### Getting credentials (MEDIUM confidence — P24 docs not directly accessible)

The user must have a Przelewy24 merchant account. Sandbox credentials are separate from production:

1. Log in to the sandbox panel: `https://sandbox.przelewy24.pl/panel/`
   - Or create sandbox account from production panel: "Moje dane" → "Konto w SANDBOX"
   - Sandbox login credentials arrive by email after sandbox account activation

2. In the sandbox panel, navigate to: **Moje konto → Moje dane → Dane API i konfiguracja**

3. Collect these four values:
   - `P24_MERCHANT_ID` — the numeric seller ID (same as login number, e.g. 12345)
   - `P24_POS_ID` — Point of Sale ID (often same as MERCHANT_ID for simple accounts)
   - `P24_CRC_KEY` — the CRC key (used for signing, different from API key)
   - `P24_API_KEY` — the report/API key ("klucz do raportów")

#### IP address configuration (HIGH confidence — multiple sources confirm)

In the "Dane API i konfiguracja" section, there is an "Adres IP" field next to the API key. MyDevil shared hosting uses dynamic or shared IPs — the user should:

**Set the IP field value to `%` (percent sign)**

This disables IP restriction and allows webhook delivery from any IP. Steps:
1. Find the "Klucz API" / "Klucz do raportów" section
2. Change the IP value in the field next to the key to `%`
3. Click `+` button then save

Without this, P24 may reject API calls from the production server's IP.

#### No separate webhook URL registration in P24 panel

The webhook URL (`urlStatus`) is sent dynamically in each `register_transaction()` call payload — P24 does not require you to pre-register a webhook URL in the panel. The URL is passed per-transaction. **No panel configuration needed for the webhook URL itself.**

### What to put in production `.env`

```bash
P24_MERCHANT_ID=<your sandbox merchant ID>
P24_POS_ID=<your sandbox POS ID>
P24_CRC_KEY=<your sandbox CRC key>
P24_API_KEY=<your sandbox API key>
P24_SANDBOX=True
```

### P24 Sandbox test flow

In the P24 sandbox payment page, the user can complete payment using test cards or the "approve" button — no real money changes hands.

---

## Common Pitfalls

### Pitfall 1: Wrong credentials environment (production vs sandbox)
**What goes wrong:** Using production P24 credentials with `P24_SANDBOX=True` — registration call goes to sandbox URL but authenticates with production credentials → 401 error.
**Why it happens:** P24 sandbox has separate credentials from production.
**How to avoid:** Always get credentials from `sandbox.przelewy24.pl/panel/`, not the production panel.
**Warning signs:** `register_transaction()` raises HTTP 401.

### Pitfall 2: IP restriction blocking API calls
**What goes wrong:** `register_transaction()` returns 401 or connection refused from MyDevil server.
**Why it happens:** P24 panel has IP whitelist on the API key — only allows calls from registered IP.
**How to avoid:** Set IP field to `%` in P24 panel (see above).
**Warning signs:** Local dev works, production returns 401 on checkout.

### Pitfall 3: Webhook unreachable (P24 can't POST to production)
**What goes wrong:** Payment completes in P24 UI, but order stays `pending` — webhook never arrives.
**Why it happens:** CSRF exemption missing (already handled with `@csrf_exempt`), or SSL cert issue, or URL wrong.
**How to avoid:** Confirm `https://kuchennakomitywa.pl/zamowienie/webhook/p24/` returns 200 from external request. Check `logs/django.log` after test payment.
**Warning signs:** Order stays `pending` after P24 payment success page.

### Pitfall 4: Ebook file not uploaded — silent failure
**What goes wrong:** `send_ebook_delivery()` returns early without sending email (line 59: `if not ebook_products: return`).
**Why it happens:** Admin uploaded product without attaching the PDF file.
**How to avoid:** Verify `product.ebook_file` is set in admin before E2E test.
**Warning signs:** No ebook email received, no error in logs.

### Pitfall 5: `check --deploy` run with dev `.env`
**What goes wrong:** Running `check --deploy` locally still shows `DEBUG=True` warnings.
**Why it happens:** Local `.env` has `DEBUG=True`.
**How to avoid:** Run `check --deploy` on the production server via SSH.
**Warning signs:** Sees W018 (DEBUG=True) even after claiming to fix it.

### Pitfall 6: `attach_file()` using `.path` — fails if media file missing
**What goes wrong:** `email.attach_file(product.ebook_file.path, ...)` raises `FileNotFoundError`.
**Why it happens:** File path stored in DB but file deleted from disk, or upload path changed.
**How to avoid:** Upload ebook PDF on production before E2E test. The existing try/except in `send_ebook_delivery()` logs the error and continues — won't crash the webhook.
**Warning signs:** Ebook email not received; log shows `Failed to attach ebook for order X`.

---

## Code Examples

### settings.py changes needed (verified against current file)

**Add** (after the existing security settings block, around line 257):
```python
# silence W008: Apache handles HTTP→HTTPS redirect, not Django
SILENCED_SYSTEM_CHECKS = ["security.W008"]
```

**Remove** lines 160-161:
```python
ACCOUNT_USERNAME_REQUIRED = False   # DELETE — redundant, covered by ACCOUNT_SIGNUP_FIELDS
ACCOUNT_EMAIL_REQUIRED = True       # DELETE — redundant, covered by ACCOUNT_SIGNUP_FIELDS
```

### Verifying webhook URL on production (SSH command)

```bash
curl -I https://kuchennakomitywa.pl/zamowienie/webhook/p24/
# Expected: HTTP/2 405 (Method Not Allowed — GET not allowed on require_POST)
# This confirms URL resolves and Django is responding
```

### Manual webhook test (simulate P24 notification)

The sign verification makes manual POST testing complex. Instead, verify by completing a full sandbox payment. Check logs:

```bash
tail -50 /path/to/logs/django.log
```

---

## Environment Availability

| Dependency | Required By | Available | Notes |
|------------|-------------|-----------|-------|
| P24 sandbox credentials | P24-01 | Must obtain from user | User must log into sandbox.przelewy24.pl |
| Brevo SMTP | Email delivery | Configured (Phase 9 complete) | EMAIL-01 marked complete in REQUIREMENTS.md |
| PostgreSQL on production | Order persistence | Configured (Phase 8 complete) | DB-01 marked complete |
| HTTPS on production | P24 webhook URL, secure cookies | Configured (Phase 8 complete) | SSL-01 through SSL-04 marked complete |
| Ebook PDF file | VER-01 | Must be uploaded by operator | Via Django admin on production |

**Blocking items requiring human action before E2E test:**
- User must obtain P24 sandbox credentials from sandbox panel
- User must upload a test ebook PDF via production Django admin

---

## Validation Architecture

Phase 10 is operational verification, not new code. The "test" is the E2E flow itself.

### Manual Test Protocol (VER-01)

1. SSH to production; run `python3 manage.py check --deploy` — expect 0 warnings
2. Open `https://kuchennakomitywa.pl/sklep/` in browser
3. Add ebook product to cart
4. Proceed to checkout, fill form, submit
5. P24 sandbox payment page loads (confirms `register_transaction()` worked)
6. Complete payment in sandbox UI
7. Check order in Django admin — status should be `paid`
8. Check test email inbox — two emails expected:
   - Order confirmation (plain text)
   - Ebook delivery with PDF attachment
9. Confirm PDF opens correctly

### Automated check command

```bash
python3 manage.py check --deploy
# Must return: System check identified no issues (0 silenced).
```

---

## Plan Structure Recommendation

**Two plans are appropriate:**

### Plan 1 — Code Fixes + Production Configuration
1. Edit `settings.py`: add `SILENCED_SYSTEM_CHECKS`, remove deprecated allauth lines
2. Verify/update production `.env` with P24 sandbox credentials + all security env vars
3. Deploy (git push + SSH deploy.sh or equivalent restart)
4. Run `python3 manage.py check --deploy` on production → 0 warnings

### Plan 2 — E2E Verification
1. Upload test ebook PDF in Django admin on production
2. Run full E2E purchase flow (browser test)
3. Confirm order status in admin
4. Confirm emails received (confirmation + ebook)
5. Mark requirements P24-01, P24-02, VER-01, VER-02 complete in REQUIREMENTS.md

---

## Open Questions

1. **Does the user already have a P24 sandbox account?**
   - What we know: The `.env.example` has empty `P24_MERCHANT_ID`, `P24_POS_ID`, etc.
   - What's unclear: Whether the user has registered at `sandbox.przelewy24.pl` or has credentials
   - Recommendation: Plan 1 should include a pre-condition check: "Confirm P24 sandbox credentials available before proceeding"

2. **Are SSL security env vars (`SESSION_COOKIE_SECURE`, etc.) already set on production?**
   - What we know: Phase 8 is marked complete in REQUIREMENTS.md (SSL-01 through SSL-04)
   - What's unclear: Whether the `.env` on production actually has these vars set
   - Recommendation: Plan 1 should include a step to verify all required `.env` vars are present

3. **P24 sandbox IP list for `p24_webhook` validation**
   - What we know: The code validates `sign` (SHA-384), not source IP
   - What's unclear: Whether P24 sandbox sends from a known IP range that MyDevil might block
   - Recommendation: If webhook doesn't arrive after payment, check MyDevil firewall. The `sign` check in the code is the correct security mechanism — IP-based filtering is not implemented and not needed.

---

## Sources

### Primary (HIGH confidence)
- Code read directly: `shop/payment.py`, `shop/views.py`, `shop/emails.py`, `shop/models.py`, `shop/admin.py`, `backend/settings.py`, `backend/urls.py`
- `python3 manage.py check --deploy` — output captured directly from this repo
- Django docs on `SILENCED_SYSTEM_CHECKS`: https://docs.djangoproject.com/en/5.2/ref/checks/

### Secondary (MEDIUM confidence)
- jdm.pl — IP `%` wildcard in P24 panel: https://jdm.pl/pomoc/baza-wiedzy/jak-ustawic-ip-dla-przelewy24-pl/
- Comarch e-Sklep P24 docs — IP whitelist requirement: https://pomoc.comarchesklep.pl/artykul/przelewy24-konfiguracja/
- MyDevil Django docs — `public/` served statically: https://pomoc.mydevil.net/Django/
- Przelewy24 help center — sandbox setup: https://www.przelewy24.pl/en/help-center/api-technical-support/how-do-i-set-up-the-sandbox-environment

### Tertiary (LOW confidence)
- WebSearch consensus on P24 credentials location ("Moje dane" → "Dane API i konfiguracja") — could not directly access official P24 panel docs due to 403 on developers.przelewy24.pl

---

## Metadata

**Confidence breakdown:**
- Code analysis (existing P24 flow): HIGH — read source directly
- `check --deploy` warnings: HIGH — ran command, read output
- P24 sandbox panel configuration: MEDIUM — official docs inaccessible (403), corroborated by 3+ Polish integration guides
- MyDevil media file serving: HIGH — documented at pomoc.mydevil.net

**Research date:** 2026-04-11
**Valid until:** 2026-07-11 (P24 API stable; Django 5.2 security settings stable)
