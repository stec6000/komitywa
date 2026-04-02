# Phase 5: Payments & Orders — Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 5 wires the existing checkout form (Phase 4) to Przelewy24, processes payment webhooks with CRC validation, sends order confirmation emails, and delivers ebook PDFs by email. The Order model (Phase 4) already exists with status=pending after checkout form submission — Phase 5 upgrades the payment flow and adds email delivery.

Phase 5 does NOT add: user accounts, order history pages, refund flows, or physical product shipping notifications.

</domain>

<decisions>
## Implementation Decisions

### Przelewy24 Integration
- **D-01 (Claude's Discretion):** Library/approach choice left to researcher and planner. Either python-przelewy24 package or direct REST calls via requests (already in requirements.txt) are acceptable. Researcher should evaluate the current state of python-przelewy24 and recommend.
- **D-02:** Design for sandbox first. P24_MERCHANT_ID, P24_POS_ID, P24_CRC_KEY, P24_API_KEY in .env with separate sandbox/production values. Switching to production = config change only.

### Payment Flow & Order Lifecycle
- **D-03:** Order created BEFORE payment (Phase 4 approach retained). Checkout form POST creates Order with status="pending". Phase 5 adds a p24_session_id field to Order and registers the transaction with P24, then redirects to P24 payment page.
- **D-04:** Add `p24_session_id` field to Order model (CharField, blank=True) via migration. This is the identifier used to match P24 webhook notifications to the correct Order.
- **D-05:** Return URL (user returns from P24 after payment) shows a pending confirmation page: "Dziękujemy za zamówienie! Potwierdzenie zostanie wysłane na Twój email." Webhook processes asynchronously and updates Order status to "paid" + triggers emails.
- **D-06:** Failed/cancelled payments — set Order status to "cancelled", restore cart from Order.cart_snapshot into the session, redirect user back to /zamowienie/ so they can retry. Cart was cleared at checkout form submission (Phase 4) — restoring from snapshot gives the user their items back.

### Ebook Delivery
- **D-07:** Ebook PDF files stored in Django media/ directory at `media/ebooks/`. Uploaded via Django admin. Existing MEDIA_ROOT setup from Phase 1 handles this.
- **D-08:** PDF delivered as email attachment directly in the ebook delivery email. No download links, no expiry concerns. Aligns with REQUIREMENTS.md: "ebooki dostarczane wyłącznie na email."
- **D-09:** Add `ebook_file = models.FileField(upload_to="ebooks/", blank=True, null=True)` to the Product model. Only populated for type="ebook" products. Migration needed.
- **D-10:** Delivery failure handling — catch exception, log with Django logging (order ID, product ID, error), continue. Admin checks Django admin for orders needing manual resend. No automatic retry in v1. Payment is already confirmed — do not reverse it.

### Email & Notifications
- **D-11:** Django SMTP backend via django-environ .env config (EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_USE_TLS). Development: EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend". Production: SMTP (admin configures).
- **D-12:** Two separate emails sent after webhook confirms payment:
  1. **Order confirmation** (all orders) — sent to customer email with order summary (items, total, pickup date)
  2. **Ebook delivery** (only for orders containing ebook products) — sent to customer email with PDF attachment(s)
- **D-13:** Plain text emails. Warm personal Polish tone matching site brand (Phase 2 D-12). Subject lines in Polish.
- **D-14:** No admin notification email. Admin monitors new paid orders via Django admin panel (PAY-06 covered by admin registration).

### Claude's Discretion
- Exact P24 library chosen by researcher (python-przelewy24 vs. direct REST)
- P24 transaction registration endpoint structure and CRC signing implementation details
- Webhook signature verification implementation details
- Email subject line and body copy (warm Polish tone, per D-13)
- Admin fieldset layout for updated Order model
- Error page copy for payment failure

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — PAY-01 through PAY-06 and LEGAL-04
- `.planning/ROADMAP.md` — Phase 5 goal, success criteria, dependency on Phase 4

### Prior Phase Outputs
- `.planning/phases/04-shop/04-CONTEXT.md` — Cart architecture, Order model decisions, checkout form (LEGAL-04 checkboxes already implemented)
- `.planning/phases/01-foundation/01-CONTEXT.md` — django-environ setup, MEDIA_ROOT configuration

### Codebase
- `shop/models.py` — Existing Order model (status choices, cart_snapshot, email, name, phone, pickup_date, total)
- `shop/views.py` — checkout() view that creates Order stub and cart_clear logic
- `shop/forms.py` — CheckoutForm with LEGAL-04 consent fields
- `backend/settings.py` — Installed apps, MEDIA_ROOT, email backend config location
- `.env.example` — Environment variable pattern to follow when adding P24 + email config

</canonical_refs>

<specifics>
## Specific Ideas

- Phase 4 checkout view already creates the Order and clears the cart. Phase 5 should modify checkout to: (1) create Order, (2) register P24 transaction using the Order ID as session identifier, (3) redirect to P24 payment URL. Do NOT rewrite the entire checkout view — extend it.
- The p24_session_id is typically derived from the Order PK or a UUID — researcher should clarify P24's requirements for session ID format.
- Webhook URL pattern: `/zamowienie/webhook/p24/` — needs CSRF exemption (@csrf_exempt).
- Return URL pattern: `/zamowienie/powrot/` — shown to user after returning from P24.
- Cart restoration on payment failure: deserialize Order.cart_snapshot and repopulate request.session['cart'].
- For mixed orders (physical + ebook), send both the confirmation email AND the ebook delivery email.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-payments*
*Context gathered: 2026-04-02*
