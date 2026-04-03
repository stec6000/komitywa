# Phase 6: Newsletter - Discussion Log

**Date:** 2026-04-03
**Areas discussed:** Form placement & design, Unsubscribe UX

---

## Form Placement & Design

**Q: Where should the newsletter signup form appear?**
Options: Section above footer / New row inside footer
**Selected:** Section above footer — a distinct band between page content and .kk-footer

**Q: What does the signup form include?**
Options: Email + RODO checkbox / Email + inline disclaimer
**Selected:** Email + RODO checkbox ("Wyrażam zgodę na otrzymywanie newslettera" with link to polityka prywatności)

**Q: What happens after the user clicks 'Zapisz się'?**
Options: Full page redirect / Inline success message (AJAX)
**Selected:** Full page redirect → /newsletter/sprawdz-email/ ("Wysłaliśmy link potwierdzający...")

---

## Unsubscribe UX

**Q: What happens when the user clicks the unsubscribe link?**
Options: One-click immediate / Confirmation step first
**Selected:** One-click immediate — GET /newsletter/wypisz/<token>/ → unsubscribe → "Zostałeś wypisany" page
Note: Second click on same token → "Zostałeś już wypisany" (idempotent)

---

## Areas Not Discussed (Claude's Discretion)
- Double opt-in token implementation and expiry
- App structure (newsletter app)
- Admin interface design
- Subscriber model fields
