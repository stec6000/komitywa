# Phase 4: Shop — Discussion Log

**Date:** 2026-04-01
**Areas discussed:** Cart persistence, Ebook vs physical products

---

## Cart Persistence

**Q: How should the cart be stored?**
Options: Django sessions / Database CartItem model
**Selected:** Django sessions
> Cart stored in `request.session['cart']` as `{product_id: quantity}` dict. No extra model needed. Works for anonymous users.

**Q: Can anonymous users add to cart and reach checkout?**
Options: Yes — guest checkout / No — must be logged in
**Selected:** Yes — guest checkout
> No login required. Checkout form collects email directly.

---

## Ebook vs Physical Products

**Q: How should ebooks and physical products be differentiated in the UI?**
Options: Same template with badge + delivery note / Separate layouts per type
**Selected:** Same template, badge + delivery note
> One Product model with `type` field. Ebooks get "Cyfrowy" badge and "dostawa na email" note. Physical products get "odbiór osobisty" note.

**Q: What does the ebook product detail page show beyond title, photo, description, price?**
Options: Delivery note only / Sample/excerpt section / You decide
**Selected:** Delivery note only
> Clear line: "Po zakupie ebook zostanie wysłany na Twój email." No preview or chapters needed.

**Q: Can an ebook be purchased at quantity > 1?**
Options: Always quantity 1 / Allow any quantity
**Selected:** Always quantity 1 for ebooks
> Ebook cart items have no quantity controls. Fixed at 1.
