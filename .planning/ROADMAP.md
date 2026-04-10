# Roadmap: Kuchenna Komitywa

## Milestones

- ✅ **v1.0 MVP** — Phases 1-6 (shipped 2026-04-04) → [archive](milestones/v1.0-ROADMAP.md)
- 🚧 **v1.1 Wdrożenie Produkcyjne** — Phases 7-10 (in progress)

## Phases

### v1.1 Wdrozenie Produkcyjne (Phases 7-10)

- [ ] Phase 7: Server Foundation (2/2 plans) — in progress
- [ ] Phase 8: Database & Security
- [ ] Phase 9: Email Configuration
- [ ] Phase 10: Payments Production

<details>
<summary>✅ v1.0 MVP (Phases 1-6) — SHIPPED 2026-04-04</summary>

- [x] Phase 1: Foundation (3/3 plans) — completed 2026-03-31
- [x] Phase 2: Landing & Brand (3/3 plans) — completed 2026-03-31
- [x] Phase 3: Recipes (3/3 plans) — completed 2026-04-01
- [x] Phase 4: Shop (3/3 plans) — completed 2026-04-02
- [x] Phase 5: Payments & Orders (2/2 plans) — completed 2026-04-03
- [x] Phase 6: Newsletter (2/2 plans) — completed 2026-04-03

</details>

### 🚧 v1.1 Wdrożenie Produkcyjne (In Progress)

**Milestone Goal:** Przenieść aplikację z dev na MyDevil.net z pełną konfiguracją produkcyjną (PostgreSQL, Brevo SMTP, HTTPS, P24 sandbox).

- [ ] **Phase 7: Server Foundation** - Passenger WSGI, virtualenv, production settings, static/media, deploy script, logging
- [ ] **Phase 8: Database & SSL** - PostgreSQL migration, superuser, Let's Encrypt HTTPS, security headers, keep-alive cron
- [ ] **Phase 9: Email** - Brevo SMTP configuration, SPF/DKIM DNS verification, all email flows tested on production
- [ ] **Phase 10: Payments & Verification** - P24 sandbox webhook on production domain, ebook upload, end-to-end purchase test, deploy check

## Phase Details

### Phase 7: Server Foundation
**Goal**: Operator can deploy and run the Django application on MyDevil.net with correct static/media serving and production configuration
**Depends on**: Phase 6 (v1.0 complete)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05, INFRA-06
**Success Criteria** (what must be TRUE):
  1. Django responds to HTTP requests on MyDevil.net through Passenger WSGI with a dedicated virtualenv
  2. All production configuration (SECRET_KEY, DEBUG, ALLOWED_HOSTS) is managed through a `.env` file — no secrets in code
  3. Static files (CSS, JS, icons) and media files (ebook PDFs) load correctly in the browser at their public URLs
  4. Operator can deploy a new version by running `deploy.sh` which pulls code, installs deps, runs migrations, collects static, and restarts the app
  5. Application errors are written to `logs/django.log` on the server
**Plans:** 2 plans
Plans:
- [x] 07-01-PLAN.md — Production configuration (passenger_wsgi.py, settings.py, requirements.txt)
- [x] 07-02-PLAN.md — Deploy script and environment template (deploy.sh, .env.example, .gitignore)

### Phase 8: Database & SSL
**Goal**: Application runs on PostgreSQL with HTTPS-only access and production-grade security settings
**Depends on**: Phase 7
**Requirements**: DB-01, DB-02, DB-03, SSL-01, SSL-02, SSL-03, SSL-04, SSL-05
**Success Criteria** (what must be TRUE):
  1. Application uses PostgreSQL as its database — all Django migrations applied successfully on PostgreSQL
  2. Operator can log into Django admin at the production URL and manage content
  3. Site is accessible only via HTTPS with a valid Let's Encrypt certificate — HTTP requests redirect to HTTPS
  4. POST forms (login, checkout, newsletter signup) work correctly under HTTPS without CSRF errors
  5. Session and CSRF cookies have Secure and HttpOnly flags set — a cron job pings the site every 12h to prevent auto-shutdown
**Plans**: TBD

### Phase 9: Email
**Goal**: All application email flows work on production through Brevo SMTP with proper sender domain authentication
**Depends on**: Phase 8
**Requirements**: EMAIL-01, EMAIL-02, EMAIL-03, EMAIL-04, EMAIL-05, EMAIL-06
**Success Criteria** (what must be TRUE):
  1. Application sends emails through Brevo SMTP — emails arrive in inbox (not spam) with the correct sender domain
  2. SPF and DKIM DNS records are configured and verified in Brevo — sender domain is authenticated
  3. Registration email with verification link arrives and the link works on production
  4. Password reset email arrives and the reset flow completes successfully on production
  5. Newsletter double opt-in confirmation email arrives and the confirm link works on production
**Plans**: TBD

### Phase 10: Payments & Verification
**Goal**: Full purchase flow works end-to-end on production with P24 sandbox payments and ebook delivery
**Depends on**: Phase 9
**Requirements**: P24-01, P24-02, VER-01, VER-02
**Success Criteria** (what must be TRUE):
  1. P24 sandbox payment completes successfully with the webhook URL pointing to the production HTTPS domain
  2. Ebook PDFs are uploaded through Django admin on production and are accessible for delivery
  3. Full end-to-end flow works: browse products, add to cart, checkout, pay via P24 sandbox, receive confirmation email with ebook PDF attachment
  4. `python manage.py check --deploy` reports no security warnings
**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 3/3 | Complete | 2026-03-31 |
| 2. Landing & Brand | v1.0 | 3/3 | Complete | 2026-03-31 |
| 3. Recipes | v1.0 | 3/3 | Complete | 2026-04-01 |
| 4. Shop | v1.0 | 3/3 | Complete | 2026-04-02 |
| 5. Payments & Orders | v1.0 | 2/2 | Complete | 2026-04-03 |
| 6. Newsletter | v1.0 | 2/2 | Complete | 2026-04-03 |
| 7. Server Foundation | v1.1 | 0/2 | In Progress | - |
| 8. Database & SSL | v1.1 | 0/? | Not started | - |
| 9. Email | v1.1 | 0/? | Not started | - |
| 10. Payments & Verification | v1.1 | 0/? | Not started | - |
