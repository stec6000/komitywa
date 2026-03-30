# Project Research Summary

**Project:** Kuchenna Komitywa
**Domain:** Vegan food business website (e-commerce + recipe blog + newsletter)
**Researched:** 2026-03-30
**Confidence:** HIGH

## Executive Summary

Kuchenna Komitywa is a vegan/plant-based food business website combining a recipe blog, ebook sales, physical product sales (jarred meals, cakes with local pickup), and newsletter. The existing Django 5.2 backend with email-based authentication provides a solid foundation, but needs a significant shift from API-only to Django templates with server-rendered HTML.

The recommended approach is to build on the existing Django stack using Django templates + Bootstrap 5 + htmx for interactivity, custom e-commerce models (not a heavy framework like Oscar — the product catalog is simple enough), Przelewy24 for payments, and Celery for async email delivery. The frontend should be mobile-first given that 70%+ of food blog traffic comes from mobile devices.

Key risks include: Przelewy24 webhook security (fake payment confirmations), ebook PDF exposure without payment verification, RODO/GDPR compliance requirements (mandatory for Polish e-commerce), and email deliverability for ebook delivery. All are preventable with proper implementation in the right phase.

## Key Findings

### Recommended Stack

The existing Django 5.2 + allauth + DRF stack is kept. New additions: Bootstrap 5 for responsive CSS, htmx for dynamic interactions (cart, search), Pillow for image handling, easy-thumbnails for auto-resizing, Celery + Redis for async tasks (email, order processing), and django-crispy-forms for form rendering.

**Core technologies:**
- Django 5.2 + templates: Server-rendered HTML, great for SEO, simpler than SPA
- Bootstrap 5 + htmx: Responsive design + dynamic interactions without JS framework
- Custom e-commerce models: Lighter than django-oscar for 2 product types
- Przelewy24 REST API: Polish payment gateway with BLIK, bank transfers, cards
- Celery + Redis: Async email sending (ebook delivery, newsletter, confirmations)

### Expected Features

**Must have (table stakes):**
- Hero section with brand story and value proposition
- Recipe blog with categories, search, high-quality photos, Schema.org markup
- Product catalog with clear categories (ebooks, dania w sloiku, ciasta)
- Shopping cart with checkout flow
- Przelewy24 payments
- Ebook delivery via email after payment
- Newsletter signup with double opt-in
- Mobile-responsive design
- Legal pages (regulamin, polityka prywatnosci, RODO)
- Contact info with pickup location

**Should have (competitive):**
- Recipe print view
- Recipe sharing (social media)
- Related recipes suggestions
- Product reviews/ratings
- Order history for logged-in users

**Defer (v2+):**
- Ingredient quantity scaling by servings
- Meal planning / weekly menu
- Loyalty program
- Multiple pickup locations
- Recipe video integration

### Architecture Approach

Django MTV pattern with 5 apps: pages (landing/static), recipes (blog), shop (products/cart/checkout/orders/payments), newsletter (subscribers), and existing accounts (auth). Template inheritance from base.html with Bootstrap 5. htmx for dynamic interactions (cart add/remove, search, newsletter signup). Products use model inheritance: base Product → Ebook and PhysicalProduct subtypes.

**Major components:**
1. pages app — Landing page, about, contact, legal pages
2. recipes app — Recipe CRUD, categories, search, Schema.org SEO
3. shop app — Product catalog, cart, checkout, orders, Przelewy24 integration, ebook delivery
4. newsletter app — Subscriber management, double opt-in, confirmation
5. accounts app (existing) — Auth, now with template-based views alongside API

### Critical Pitfalls

1. **Hardcoded secrets** — SECRET_KEY in settings.py (already present). Fix: move to .env with python-dotenv (already installed).
2. **Przelewy24 webhook fraud** — Unverified webhooks allow fake payments. Fix: CRC signature verification + amount matching.
3. **Ebook URL exposure** — PDFs in public media dir downloadable without payment. Fix: serve through authenticated Django view.
4. **RODO non-compliance** — Polish law requires privacy policy, double opt-in, cookie consent, regulamin. Fix: legal pages in Phase 1, consent in checkout/newsletter.
5. **Image performance** — Food sites are image-heavy, unoptimized images kill load time. Fix: auto-thumbnails, WebP, lazy loading.

## Implications for Roadmap

### Phase 1: Foundation & Infrastructure
**Rationale:** Fix existing security issues, set up template infrastructure, configure environment properly.
**Delivers:** base.html, Bootstrap 5 theme, .env configuration, static/media setup, legal page stubs
**Addresses:** Landing page foundation, security hardening
**Avoids:** Hardcoded secrets pitfall, production deployment issues

### Phase 2: Landing Page & Brand Identity
**Rationale:** Public-facing entry point needed before content. Brand identity informs all subsequent visual work.
**Delivers:** Landing page, about page, contact page, brand CSS theme
**Addresses:** Hero section, brand presence, contact info, mobile responsiveness

### Phase 3: Recipe Blog
**Rationale:** Core content that drives organic traffic (SEO). Independent of shop, can launch early for marketing.
**Delivers:** Recipe model, list/detail views, categories, search, Schema.org markup, admin
**Uses:** Pillow, easy-thumbnails, django-meta
**Implements:** recipes app architecture

### Phase 4: Shop & Products
**Rationale:** Depends on brand identity (Phase 2) for product presentation. Independent of payments (can show catalog first).
**Delivers:** Product models, catalog views, cart, product admin
**Implements:** shop app (catalog + cart portion)

### Phase 5: Payments & Orders
**Rationale:** Depends on shop (Phase 4) for cart/products. Critical path for revenue.
**Delivers:** Przelewy24 integration, checkout flow, order management, ebook email delivery
**Addresses:** Payment processing, ebook delivery, order confirmation
**Avoids:** P24 webhook security pitfall, ebook exposure pitfall

### Phase 6: Newsletter
**Rationale:** Can be built after main site structure exists. Needs double opt-in for RODO compliance.
**Delivers:** Subscriber model, signup widget, double opt-in flow, confirmation emails
**Avoids:** RODO compliance pitfall

### Phase 7: Polish & Production
**Rationale:** Final optimization after all features work. SEO, performance, security, deployment.
**Delivers:** Image optimization, caching, SEO audit, production config, deployment
**Avoids:** Performance pitfalls, email deliverability issues

### Phase Ordering Rationale

- Foundation first — security and infrastructure must be solid before building features
- Landing page before content — brand identity informs visual design of recipes and shop
- Recipes before shop — drives organic traffic, can launch independently for marketing
- Shop before payments — catalog can be shown before payments work (builds anticipation)
- Newsletter last of features — simple, independent, but needs all pages to exist for footer widget
- Polish last — optimization makes sense only after all features are complete

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 5 (Payments):** Przelewy24 REST API specifics, sandbox setup, webhook format
- **Phase 3 (Recipes):** Schema.org Recipe markup specifics, Google Rich Results requirements

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** Standard Django template setup, well-documented
- **Phase 2 (Landing):** Standard Bootstrap landing page patterns
- **Phase 6 (Newsletter):** Simple CRUD + email confirmation flow

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Django ecosystem is mature, all recommended packages well-maintained |
| Features | HIGH | Food business website is a well-understood domain |
| Architecture | HIGH | Standard Django patterns, no exotic requirements |
| Pitfalls | HIGH | Common e-commerce and Django pitfalls, well-documented |

**Overall confidence:** HIGH

### Gaps to Address

- Przelewy24 API version and exact integration flow — verify during Phase 5 planning with current P24 docs
- Email service provider choice (SES vs Mailgun vs other) — decide during Phase 5 planning based on volume needs
- Hosting platform (VPS, PaaS, etc.) — decide during Phase 7 planning

## Sources

### Primary (HIGH confidence)
- Django documentation (djangoproject.com)
- Przelewy24 developer docs (developers.przelewy24.pl)
- Bootstrap 5 documentation
- htmx documentation (htmx.org)

### Secondary (MEDIUM confidence)
- Django e-commerce community patterns
- Polish RODO/GDPR compliance guidelines
- Food blog SEO best practices

---
*Research completed: 2026-03-30*
*Ready for roadmap: yes*
