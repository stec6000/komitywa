# Phase 4: Shop — Context

**Gathered:** 2026-04-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 delivers a product catalog (ebooks, dania w słoiku, ciasta), product detail pages, shopping cart management (add/view/change quantities/remove), a checkout form collecting pickup data, and Django admin for product management.

Payment processing (Przelewy24) and order confirmation are Phase 5. Phase 4 ends at the checkout form with a placeholder "Przejdź do płatności" button.

</domain>

<decisions>
## Implementation Decisions

### Cart Architecture
- **D-01:** Cart stored in Django sessions (`request.session['cart']` as `{product_id: quantity}` dict). No CartItem database model needed. Sessions persist page refreshes; clear on expiry or browser close.
- **D-02:** Guest checkout — no login required to add to cart, view cart, or fill the checkout form. The checkout form collects email directly. Login remains optional throughout.

### Product Model & Types
- **D-03:** Single `Product` model with a `type` field (`ebook` / `physical`). Same card and detail templates for both types — no separate layouts.
- **D-04:** Ebooks show a "Cyfrowy" badge on the product card. Product detail page shows a clear delivery note: "Po zakupie ebook zostanie wysłany na Twój email." No preview, sample, or table of contents needed.
- **D-05:** Physical products show "Odbiór osobisty" delivery note on the detail page.
- **D-06:** Ebook quantity in cart is fixed at 1. No quantity controls rendered for ebook cart items. Physical products have normal quantity controls (+ / –).

### Product Catalog Layout
- **D-07:** Unified product grid with category filter pills — consistent with the Phase 3 recipe pattern (`kk-filter-pill`, `kk-recipe-card` adapted to `kk-product-card`). Categories: "Wszystkie | Ebooki | Dania w słoiku | Ciasta". No separate pages per category.

### Cart UI
- **D-08:** Claude's Discretion — dedicated `/koszyk/` page. Navbar cart icon (already present with badge count) links to this page.

### Checkout Form (SHOP-05)
- **D-09:** Claude's Discretion — form on `/zamowienie/`. Collects: email, imię i nazwisko, telefon (optional), and odbiór data (date picker or free text). Ends with a "Przejdź do płatności" placeholder button (Phase 5 wires this).
- **D-10:** LEGAL-04 compliance: form includes two checkboxes — (1) zgoda na przetwarzanie danych osobowych, (2) akceptacja regulaminu. Both required to proceed.

### Brand & Visual Consistency
- **D-11:** Carries forward Phase 3 3-column card grid pattern. Product cards show: photo (4:3 ratio, `object-fit: cover`), category badge, product name, short description excerpt, price. Ebooks additionally show "Cyfrowy" badge.
- **D-12:** Warm personal Polish copy tone (Phase 2 D-12). Empty cart state: "Twój koszyk jest pusty — zapraszamy do sklepu!"

### Claude's Discretion
- Exact `Product` model field names and admin fieldset layout
- Cart badge update mechanism (Django redirect vs. JS fetch — keep it simple: redirect with GET param)
- Checkout form field validation details (phone format, date format)
- Specific stock photo selection for product placeholders

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — SHOP-01 through SHOP-06 and LEGAL-04 (checkout form consents)
- `.planning/ROADMAP.md` — Phase 4 goal, success criteria, and dependency on Phase 2

### Prior Phase Outputs
- `.planning/phases/01-foundation/01-CONTEXT.md` — Brand decisions (colors, fonts, feel)
- `.planning/phases/03-recipes/03-CONTEXT.md` — Card grid and filter pill pattern decisions (D-01, D-02, D-03) to reuse for product catalog
- `.planning/phases/03-recipes/03-UI-SPEC.md` — UI component patterns established for cards and filter pills

### Codebase
- `static/css/main.css` — All brand CSS variables and existing component classes (`kk-filter-pill`, `kk-recipe-card`, `kk-badge`, etc.)
- `templates/base.html` — Base template with navbar (cart icon with badge already present)
- `templates/includes/_navbar.html` — Cart icon location and badge markup

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `kk-filter-pill` CSS class (static/css/main.css): already styled for active/inactive category pills — reuse directly for product category filter
- `kk-recipe-card` pattern: adapt to `kk-product-card` keeping same 4:3 image ratio, badge, and card structure
- `kk-badge` class: already used for category badges on recipe cards — use for "Cyfrowy" and "Nowy" badges on products
- Navbar cart icon (`bi-cart3`) with badge count in `_navbar.html`: already rendered, just needs dynamic count from session context processor

### Established Patterns
- Category filter: GET param `?kategoria=slug` pattern from Phase 3 `recipe_list` view — same approach for product catalog
- Search: GET param `?q=` pattern from Phase 3 — reuse for product search if needed
- Pagination: Django `Paginator` with query param preservation — same approach
- Admin: `@admin.register(Model)` + `prepopulated_fields` for slug — same as `RecipeAdmin`

### Integration Points
- `backend/urls.py`: add `path("sklep/", include("shop.urls", namespace="shop"))`
- `backend/urls.py`: add `path("koszyk/", ...)` and `path("zamowienie/", ...)`
- `templates/includes/_navbar.html`: wire cart badge count to `{{ cart_count }}` from context processor
- `templates/base.html`: may need a cart context processor registered in `TEMPLATES[0]['OPTIONS']['context_processors']`

</code_context>

<specifics>
## Specific Ideas

- Navbar cart badge is already rendered (Phase 1 stub) — just needs a context processor to inject live session count
- Phase 3 recipe filter pattern is a direct blueprint for product category filter — planner can reference 03-02-PLAN.md for exact implementation approach
- Checkout form (SHOP-05) is in Phase 4 scope but payment wiring is Phase 5 — form should POST to a view that saves an Order stub and renders a "Czekamy na płatność" placeholder or redirects to Phase 5's payment initiation URL

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-shop*
*Context gathered: 2026-04-01*
