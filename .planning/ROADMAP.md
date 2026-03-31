# Roadmap: Kuchenna Komitywa

## Overview

Kuchenna Komitywa transforms from an API-only Django backend into a full server-rendered website for a vegan food business. The journey starts with infrastructure and template foundation, then builds the public-facing landing page with brand identity, adds the recipe blog for organic traffic, builds the product catalog and cart, integrates Przelewy24 payments with ebook delivery, and finishes with newsletter functionality. Legal/RODO requirements are distributed across phases where they naturally belong (cookie consent in foundation, legal pages with landing, checkout consent with payments).

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation** - Django template infrastructure, environment config, static/media setup, cookie consent
- [ ] **Phase 2: Landing & Brand** - Landing page with brand identity, about/contact pages, legal pages
- [ ] **Phase 3: Recipes** - Recipe blog with categories, search, SEO markup, and admin management
- [ ] **Phase 4: Shop** - Product catalog, product pages, shopping cart, and admin management
- [ ] **Phase 5: Payments & Orders** - Przelewy24 integration, checkout flow, order confirmation, ebook delivery
- [ ] **Phase 6: Newsletter** - Newsletter signup, double opt-in, unsubscribe

## Phase Details

### Phase 1: Foundation
**Goal**: The Django application renders server-side HTML pages with a consistent layout, proper environment configuration, and working static/media file handling
**Depends on**: Nothing (first phase)
**Requirements**: FOUND-01, FOUND-02, FOUND-03, FOUND-04, FOUND-05, LEGAL-03
**Success Criteria** (what must be TRUE):
  1. Application loads configuration from .env file and no secrets are hardcoded in settings
  2. Every page renders with a shared base template including header, footer, and navigation
  3. Pages display correctly on mobile devices (responsive layout with Bootstrap 5)
  4. Static files (CSS, JS, images) load without errors on every page
  5. Cookie consent banner appears on first visit and respects user choice
**Plans**: 3 plans

Plans:
- [x] 01-01-PLAN.md — Environment config, static/media setup, core app with home route
- [x] 01-02-PLAN.md — Template hierarchy (base.html, navbar, footer) with Bootstrap 5 and brand CSS
- [x] 01-03-PLAN.md — RODO cookie consent banner with localStorage persistence

### Phase 2: Landing & Brand
**Goal**: Visitors see a professional landing page that communicates the brand identity, tells the company story, and provides contact/pickup information alongside required legal pages
**Depends on**: Phase 1
**Requirements**: LAND-01, LAND-02, LAND-03, LEGAL-01, LEGAL-02
**Success Criteria** (what must be TRUE):
  1. Visitor sees a hero section with the company mission and value proposition
  2. Visitor can read the company story on an "O nas" section or page
  3. Visitor can find the pickup address, opening hours, and location map on the contact page
  4. Visitor can access privacy policy and shop regulations from the footer
**Plans**: 3 plans
**UI hint**: yes

Plans:
- [x] 02-01-PLAN.md — Views/URLs/tests scaffold + full landing page (hero, features, about teaser, CTA) + CSS
- [x] 02-02-PLAN.md — O nas and Kontakt content pages + navbar link wiring
- [x] 02-03-PLAN.md — Privacy policy and regulations pages + footer link wiring

### Phase 3: Recipes
**Goal**: Visitors can browse, search, and read vegan recipes with rich content, and the site generates structured data for Google rich snippets
**Depends on**: Phase 2
**Requirements**: PRZE-01, PRZE-02, PRZE-03, PRZE-04, PRZE-05, PRZE-06
**Success Criteria** (what must be TRUE):
  1. Visitor sees a list of recipes with thumbnail images and can click through to full recipe details
  2. Visitor can filter recipes by category (sniadania, obiady, desery, etc.)
  3. Visitor can search recipes by title or ingredients and see matching results
  4. Recipe detail page includes structured Schema.org JSON-LD markup visible in page source
  5. Admin can create, edit, and delete recipes from the Django admin panel
**Plans**: 3 plans
**UI hint**: yes

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD
- [ ] 03-03: TBD

### Phase 4: Shop
**Goal**: Visitors can browse a product catalog with categories, view product details, and manage a shopping cart
**Depends on**: Phase 2
**Requirements**: SHOP-01, SHOP-02, SHOP-03, SHOP-04, SHOP-05, SHOP-06
**Success Criteria** (what must be TRUE):
  1. Visitor sees product catalog organized by categories (ebooks, dania w sloiku, ciasta)
  2. Visitor can open a product page with photos, description, and price
  3. Visitor can add products to cart and see cart item count update
  4. Visitor can view cart contents, change quantities, and remove items
  5. Admin can add, edit, and hide products from the Django admin panel
**Plans**: 3 plans
**UI hint**: yes

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD
- [ ] 04-03: TBD

### Phase 5: Payments & Orders
**Goal**: Customers can complete purchases through Przelewy24, receive order confirmations, and get ebooks delivered to their email
**Depends on**: Phase 4
**Requirements**: PAY-01, PAY-02, PAY-03, PAY-04, PAY-05, PAY-06, LEGAL-04
**Success Criteria** (what must be TRUE):
  1. Customer can fill in checkout form with required data and consent checkboxes, then pay via Przelewy24
  2. System correctly processes Przelewy24 payment webhook with CRC validation
  3. Customer sees an order confirmation page after successful payment
  4. Customer receives order confirmation email after payment
  5. Customer who purchased an ebook receives the PDF file via email
**Plans**: 3 plans

Plans:
- [ ] 05-01: TBD
- [ ] 05-02: TBD
- [ ] 05-03: TBD

### Phase 6: Newsletter
**Goal**: Visitors can subscribe to the newsletter with RODO-compliant double opt-in and manage their subscription
**Depends on**: Phase 1
**Requirements**: NEWS-01, NEWS-02, NEWS-03
**Success Criteria** (what must be TRUE):
  1. Visitor can enter email in a footer signup form to subscribe to the newsletter
  2. Subscriber receives a confirmation email and must click to confirm (double opt-in)
  3. Subscriber can unsubscribe via a link in any newsletter email
**Plans**: 3 plans

Plans:
- [ ] 06-01: TBD
- [ ] 06-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6
Note: Phase 3 (Recipes) and Phase 4 (Shop) both depend on Phase 2 but are independent of each other. Phase 6 (Newsletter) depends only on Phase 1 and can run after any phase from 2 onward.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 3/3 | Complete | 2026-03-31 |
| 2. Landing & Brand | 3/3 | Complete | 2026-03-31 |
| 3. Recipes | 0/3 | Not started | - |
| 4. Shop | 0/3 | Not started | - |
| 5. Payments & Orders | 0/3 | Not started | - |
| 6. Newsletter | 0/2 | Not started | - |
