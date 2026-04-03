# Phase 6: Newsletter - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 6 adds newsletter subscription to the site: a signup form above the footer with RODO-compliant double opt-in email confirmation, and a one-click unsubscribe flow via tokenized links.

Phase 6 does NOT add: bulk newsletter sending, campaign management, subscriber segmentation, or admin send UI (those are v2 — NEWS-V2-01, NEWS-V2-02).

</domain>

<decisions>
## Implementation Decisions

### Form Placement & Visual Design
- **D-01:** Newsletter signup form is a **distinct section above the footer**, not inside `.kk-footer`. It sits between page content and the existing footer bar — visually separated, more prominent.
- **D-02:** Form fields: email input + **RODO consent checkbox** ("Wyrażam zgodę na otrzymywanie newslettera" with link to polityka prywatności). Checkbox is required before submission.
- **D-03:** Form submission: standard Django full-page POST (no AJAX/JS). On success, redirect to `/newsletter/sprawdz-email/` — a page saying "Wysłaliśmy link potwierdzający na [email]. Kliknij go, żeby dokończyć zapis."

### Double Opt-In Flow
- **D-04:** After form submission, send confirmation email with a tokenized link. User must click to activate subscription (RODO compliance). Claude's discretion on token implementation and expiry (24h is standard).
- **D-05:** If user submits the form with an already-subscribed email (confirmed), silently redirect to the "sprawdź email" page — do not reveal subscription status (privacy). If pending (unconfirmed), resend the confirmation email.

### Unsubscribe Flow
- **D-06:** **One-click immediate unsubscribe** — `GET /newsletter/wypisz/<token>/` immediately marks subscriber as unsubscribed, then renders "Zostałeś wypisany z newslettera" page. No confirmation step.
- **D-07:** Unsubscribe is idempotent — clicking the same token a second time renders "Zostałeś już wypisany" without errors.
- **D-08:** Unsubscribe token included in: the double opt-in confirmation email. Future newsletter emails (sent manually by admin) should also include the same unsubscribe URL pattern.

### Claude's Discretion
- App structure: new `newsletter` Django app (separate from `core` for clean separation)
- Subscriber model fields: email, confirmed (bool), confirmation_token, unsubscribe_token, created_at
- Token generation: `secrets.token_urlsafe()` or UUID4 — researcher's choice
- Confirmation token expiry: 24h is standard; expired token shows "link wygasł" with option to re-enter email
- Admin interface: standard Django admin with subscriber list (email, confirmed status, date) — no export needed in v1
- Email copy: warm Polish tone per Phase 5 D-13; subject lines in Polish

### Email Style (from Phase 5)
- Plain text emails (Phase 5 D-13)
- Warm, personal Polish tone: "Dziękujemy za zapis do newslettera Kuchennej Komitywy!"
- Django SMTP backend via django-environ (Phase 5 D-11) — same config, no new setup needed

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Core Requirements
- `.planning/REQUIREMENTS.md` — NEWS-01, NEWS-02, NEWS-03 (newsletter requirements)

### Existing Code to Extend/Integrate
- `templates/includes/_footer.html` — Footer to render newsletter section ABOVE (not inside)
- `templates/base.html` — Base template with `{% include "includes/_footer.html" %}` — newsletter section goes between `</main>` and the footer include
- `backend/settings.py` — Installed apps, email backend config location
- `.env.example` — Email config pattern (EMAIL_HOST, EMAIL_PORT, etc. already defined)

### Established Patterns
- `shop/` app — Reference for Django app structure (models, views, urls, admin, templates/shop/)
- `templates/pages/` — Reference for standalone page templates ("sprawdź email", "wypisano")
- `shop/views.py` — POST form handling pattern (redirect after POST)

### Brand & Styling
- `static/css/main.css` — `--kk-*` CSS custom properties, Bootstrap 5 utility classes

</canonical_refs>

<specifics>
## Specific Ideas

None captured.
</specifics>

<deferred>
## Deferred Ideas

None raised during discussion.
</deferred>
