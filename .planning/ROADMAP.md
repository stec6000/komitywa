# Roadmap: Kuchenna Komitywa

## Milestones

- ✅ **v1.0 MVP** — Phases 1-6 (shipped 2026-04-04) → [archive](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1 Wdrożenie Produkcyjne** — Phases 7-10 (shipped 2026-04-16)
- 🚧 **v1.2 Infrastruktura & Bezpieczeństwo** — Phases 11-12 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-6) — SHIPPED 2026-04-04</summary>

- [x] Phase 1: Foundation (3/3 plans) — completed 2026-03-31
- [x] Phase 2: Landing & Brand (3/3 plans) — completed 2026-03-31
- [x] Phase 3: Recipes (3/3 plans) — completed 2026-04-01
- [x] Phase 4: Shop (3/3 plans) — completed 2026-04-02
- [x] Phase 5: Payments & Orders (2/2 plans) — completed 2026-04-03
- [x] Phase 6: Newsletter (2/2 plans) — completed 2026-04-03

</details>

<details>
<summary>✅ v1.1 Wdrożenie Produkcyjne (Phases 7-10) — SHIPPED 2026-04-16</summary>

- [x] **Phase 7: Server Foundation** - Passenger WSGI, virtualenv, production settings, static/media, deploy script, logging
- [x] **Phase 8: Database & SSL** - PostgreSQL migration, superuser, Let's Encrypt HTTPS, security headers, keep-alive cron
- [x] **Phase 9: Email** - Brevo SMTP configuration, SPF/DKIM DNS verification, all email flows tested on production
- [x] **Phase 10: Payments & Verification** - P24 sandbox webhook on production domain, ebook upload, end-to-end purchase test, deploy check

</details>

### 🚧 v1.2 Infrastruktura & Bezpieczeństwo (In Progress)

**Milestone Goal:** Domknąć pozostałą infrastrukturę produkcyjną — HTTPS, weryfikacja emaila i stabilność serwera.

- [ ] **Phase 11: HTTPS & Bezpieczeństwo** - Let's Encrypt cert, HTTP→HTTPS redirect, CSRF trusted origins, secure cookies, security headers
- [ ] **Phase 12: Email & Stabilność** - SPF/DKIM DNS verification in Brevo, cron keep-alive for MyDevil auto-shutdown prevention

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
**Plans:** 1/2 plans executed
Plans:
- [x] 08-01-PLAN.md — PostgreSQL adapter and database setup (psycopg, migrations, superuser)
- [ ] 08-02-PLAN.md — Let's Encrypt HTTPS, security settings, keep-alive cron

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
**Plans**: 2 plans
Plans:
- [x] 09-01-PLAN.md — Email templates, Site migration, Brevo SMTP config
- [ ] 09-02-PLAN.md — SPF/DKIM DNS verification and production email testing

### Phase 10: Payments & Verification
**Goal**: Full purchase flow works end-to-end on production with P24 sandbox payments and ebook delivery
**Depends on**: Phase 9
**Requirements**: P24-01, P24-02, VER-01, VER-02
**Success Criteria** (what must be TRUE):
  1. P24 sandbox payment completes successfully with the webhook URL pointing to the production HTTPS domain
  2. Ebook PDFs are uploaded through Django admin on production and are accessible for delivery
  3. Full end-to-end flow works: browse products, add to cart, checkout, pay via P24 sandbox, receive confirmation email with ebook PDF attachment
  4. `python manage.py check --deploy` reports no security warnings
**Plans**: 2 plans
Plans:
- [x] 10-01-PLAN.md — settings.py fixes, deploy, P24 sandbox config, check --deploy
- [x] 10-02-PLAN.md — E2E purchase flow verification, requirements sign-off

### Phase 11: HTTPS & Bezpieczeństwo
**Goal**: Strona działa wyłącznie przez HTTPS z poprawną konfiguracją bezpieczeństwa Django
**Depends on**: Phase 10
**Requirements**: HTTPS-01, HTTPS-02, HTTPS-03, HTTPS-04, HTTPS-05
**Success Criteria** (what must be TRUE):
  1. Certyfikat Let's Encrypt jest aktywny — przeglądarka pokazuje kłódkę, adres zaczyna się od `https://`
  2. Wpisanie adresu `http://` automatycznie przekierowuje na `https://` (301/302) — żadna strona nie jest dostępna przez HTTP
  3. Formularze POST (logowanie, checkout, newsletter) działają pod HTTPS bez błędów CSRF — `CSRF_TRUSTED_ORIGINS` zawiera domenę produkcyjną
  4. Cookies sesji i CSRF mają flagi `Secure` i `HttpOnly` — potwierdzone przez DevTools → Application → Cookies
  5. Nagłówki bezpieczeństwa (HSTS, X-Content-Type-Options, X-Frame-Options) zwracane przez serwer — potwierdzone przez `curl -I https://domena`
**Plans**: 1 plan
Plans:
- [ ] 11-01-PLAN.md — Weryfikacja produkcyjna HTTPS + aktualizacja .env.example

### Phase 12: Email & Stabilność
**Goal**: Emaile trafiają do skrzynki odbiorczej (nie spam) a serwer nie wyłącza się automatycznie na MyDevil
**Depends on**: Phase 11
**Requirements**: EMAIL-01, OPS-01
**Success Criteria** (what must be TRUE):
  1. Rekordy SPF i DKIM są dodane do DNS domeny — status weryfikacji w panelu Brevo pokazuje "Verified"
  2. Email testowy wysłany z aplikacji trafia do skrzynki odbiorczej (nie do folderu spam) — nagłówki emaila zawierają DKIM-Signature
  3. Cron job na MyDevil jest skonfigurowany — widoczny w cPanel → Cron Jobs z harmonogramem co 12h
  4. Serwer pozostaje aktywny przez minimum 24h bez ręcznego restartowania — brak auto-shutdown
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
| 7. Server Foundation | v1.1 | 2/2 | Complete | 2026-04-10 |
| 8. Database & SSL | v1.1 | 1/2 | In Progress|  |
| 9. Email | v1.1 | 1/2 | In Progress | - |
| 10. Payments & Verification | v1.1 | 2/2 | Complete | 2026-04-16 |
| 11. HTTPS & Bezpieczeństwo | v1.2 | 0/1 | Not started | - |
| 12. Email & Stabilność | v1.2 | 0/? | Not started | - |


## Backlog

### Phase 999.1: Panel klienta z historią zamówień (BACKLOG)

**Goal:** Logowanie i rejestracja przez HTML (allauth widoki), powiązanie zamówień z kontami użytkowników, strona "Moje zamówienia", podstawowe dane konta
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)
