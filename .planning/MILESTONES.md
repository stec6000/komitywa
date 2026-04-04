# Milestones

## v1.0 MVP (Shipped: 2026-04-04)

**Phases completed:** 6 phases, 16 plans, 30 tasks

**Key accomplishments:**

- 1. [Rule 3 - Blocking] Fixed .gitignore blocking .env.example and media/.gitkeep
- Bootstrap 5 responsive layout with Lora/Nunito typography, sage-olive-cream brand palette, and template inheritance chain
- RODO-compliant cookie banner with localStorage persistence, accept/reject buttons, and accessible markup
- Full landing page at / with hero split-layout, 3 feature cards (Bootstrap icons), about teaser, and secondary CTA — plus all 5 Phase 2 URLs, 7 test classes, and Phase 2 CSS components
- O nas and Kontakt full content pages in Polish with navbar URL wiring and active state detection
- RODO privacy policy and Polish e-commerce regulations pages with two-column footer linking both via Django {% url %} template tags
- Category and Recipe models with admin, URL namespace at /przepisy/, stub views, and 6 test classes (12 passing)
- Recipe list page with 3-column card grid, category filter pills, search by title/ingredients, and paginated results at /przepisy/
- Full recipe detail page with two-column layout, Schema.org JSON-LD for SEO, and wired navbar link with active state
- Django shop app with ProductCategory/Product/Order models, session-based Cart with ebook quantity lock, CheckoutForm with LEGAL-04 consent fields, and 29 passing tests
- Product catalog with category filter pills, paginated card grid, and detail page with delivery notes and add-to-cart POST form
- Session cart page with quantity controls, checkout form with LEGAL-04 consent and Order persistence, confirmation page, and navbar wired to live shop URLs with dynamic badge
- P24 payment client with SHA-384 sign, email module with Polish copy and ebook PDF attachment, model migrations for p24_session_id and ebook_file
- End-to-end P24 payment flow: checkout creates order + redirects to P24, webhook confirms payment + sends emails, return/cancel pages with cart restore
- Double opt-in newsletter with Subscriber model, confirmation emails, token-based confirm/unsubscribe views, and global signup form on every page
- Branded newsletter flow pages with Polish copy, Bootstrap icons, and already-unsubscribed conditional UX

---
