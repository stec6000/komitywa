---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Infrastruktura & Bezpieczeństwo
current_phase: 11
current_plan: 0
status: planning
stopped_at: ~
last_updated: "2026-04-16T00:00:00.000Z"
last_activity: 2026-06-03 -- Completed quick task 260603-aou: IG Stories PNG generator + AI image prompty z brand suffix
progress:
  total_phases: 2
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-16)

**Core value:** Klienci mogą przeglądać przepisy, kupować ebooki i zamawiać gotowe wegańskie produkty z odbiorem osobistym — w jednym miejscu.
**Current focus:** Phase 11 — HTTPS & Bezpieczeństwo

## Current Position

Phase: 11 — HTTPS & Bezpieczeństwo
Plan: —
Status: Not started (roadmap defined, awaiting plan)
Last activity: 2026-06-08 — Completed quick task 260608-e71: napraw promote_to_blogpost (skladaj body z intro+sections, excerpt z meta_description)

## Milestone Status

**v1.2 Infrastruktura & Bezpieczeństwo** — In Progress

Previous:

- v1.0 MVP shipped — 2026-04-04 (archive: `.planning/milestones/v1.0-ROADMAP.md`)
- v1.1 Wdrożenie Produkcyjne shipped — 2026-04-16

## Current Phase

**Phase 11: HTTPS & Bezpieczeństwo**
**Status:** Not started

Requirements: HTTPS-01, HTTPS-02, HTTPS-03, HTTPS-04, HTTPS-05

Success criteria:
1. Certyfikat Let's Encrypt aktywny — przeglądarka pokazuje kłódkę, adres `https://`
2. HTTP → HTTPS redirect działa — żadna strona niedostępna przez HTTP
3. Formularze POST działają pod HTTPS bez błędów CSRF
4. Cookies sesji i CSRF mają flagi `Secure` i `HttpOnly`
5. Nagłówki bezpieczeństwa (HSTS, X-Content-Type-Options, X-Frame-Options) aktywne

## Accumulated Context

### Decisions

- Direct os.environ assignment for DJANGO_SETTINGS_MODULE in passenger_wsgi.py (not setdefault)
- WhiteNoise CompressedManifestStaticFilesStorage for cache-busting static files
- Pre-HTTPS security settings always-on; HTTPS-dependent settings env-driven with safe defaults
- LOGGING at WARNING level for initial launch visibility
- deploy.sh uses set -e for fail-fast on errors
- Security env vars commented out in .env.example (Phase 8 activates after HTTPS)
- DATABASE_URL commented out in .env.example (SQLite default until Phase 8)

v1.1 key decisions:

- MyDevil.net as hosting (shared hosting with Passenger WSGI)
- Brevo as email provider (SMTP key, not API key)
- PostgreSQL as production database (fresh DB, no SQLite migration needed)
- psycopg[binary] >=3.3 (not psycopg2) — Django 5.2 preference, binary needed on shared hosting
- whitenoise for static file serving behind Passenger
- P24 sandbox on production for now (prod credentials pending seller verification)
- [Phase 08-database-ssl]: psycopg[binary] initially chosen, then replaced with psycopg2-binary -- no binary wheel for MyDevil platform
- [Phase 08-database-ssl]: SECURE_SSL_REDIRECT=False (Apache sslonly handles redirect), HSTS starts at 3600s

### Pending Todos

- Phase 11: activate HTTPS env vars in .env on server after Let's Encrypt cert is installed
- Phase 12: add SPF/DKIM DNS records early — propagation can take up to 48h

### Blockers/Concerns

- P24 production credentials not yet obtained (seller verification pending)
- Brevo SPF/DKIM DNS propagation can take up to 48h — set up DNS records early
- MyDevil PostgreSQL host address only known after SSH login (pgsqlX.mydevil.net)

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 260412-g5k | Zaktualizuj stronę kontakt: adres ul. Bukowa 14 15-796 Białystok, telefon 511562100, usuń godziny otwarcia | 2026-04-12 | ffff1d3 | — | [260412-g5k-zaktualizuj-stron-kontakt-adres-ul-bukow](.planning/quick/260412-g5k-zaktualizuj-stron-kontakt-adres-ul-bukow/) |
| 260412-gkc | Przepisz sekcję Nasza historia na stronie O nas — luźny ton, bez Warszawy, prosta historia prostego chłopaka | 2026-04-12 | b4964a0 | — | [260412-gkc-przepisz-sekcj-nasza-historia-na-stronie](.planning/quick/260412-gkc-przepisz-sekcj-nasza-historia-na-stronie/) |
| 260508-hne | Dodaj przepis: krem z białej fasoli ze szparagami i pomidorkami | 2026-05-08 | b1bb24e | — | [260508-hne-dodaj-przepis-krem-z-bia-ej-fasoli-ze-sz](.planning/quick/260508-hne-dodaj-przepis-krem-z-bia-ej-fasoli-ze-sz/) |
| 260508-ibb | Recipe: tagi (M2M Tag), servings, difficulty, notes + filtr tagów + frontend | 2026-05-08 | ffa99b0 | Verified | [260508-ibb-recipe-dodaj-tagi-m2m-tag-servings-diffi](.planning/quick/260508-ibb-recipe-dodaj-tagi-m2m-tag-servings-diffi/) |
| 260602-i1r | Nowy app content/ + weekly research pipeline (model WeeklyResearch, management command, Anthropic SDK) | 2026-06-02 | 2d547a5 | — | [260602-i1r-nowy-app-content-z-weekly-research-pipel](.planning/quick/260602-i1r-nowy-app-content-z-weekly-research-pipel/) |
| 260602-p98 | Hardening run_weekly_research: sleep 60s, JSON strictness addendum, auto-retry call 2, --retry-format flag | 2026-06-02 | 8e9a6df | — | [260602-p98-hardening-run-weekly-research-sleep-60s-](.planning/quick/260602-p98-hardening-run-weekly-research-sleep-60s-/) |
| 260602-prf | Admin preview WeeklyResearch — tabbed UI (Blog/IG Posty/Stories) z Copy to clipboard, brand palette | 2026-06-02 | b6bed65 | — | [260602-prf-admin-preview-weeklyresearch-tabbed-ui-b](.planning/quick/260602-prf-admin-preview-weeklyresearch-tabbed-ui-b/) |
| 260602-qcl | Pełny blog na stronie: BlogPost model + admin draft/publish + akcja Promuj z WeeklyResearch + frontend /blog/ + /blog/<slug>/ | 2026-06-02 | 14e8054 | — | [260602-qcl-pe-ny-blog-na-stronie-model-blogpost-adm](.planning/quick/260602-qcl-pe-ny-blog-na-stronie-model-blogpost-adm/) |
| 260603-aou | IG Stories PNG generator (1080x1920 przez Pillow) + AI image prompty z brand suffix do postow (services layer + admin action + CLI + ZIP download) | 2026-06-03 | f88706e | — | [260603-aou-grafiki-ig-stories-png-1080x1920-przez-p](.planning/quick/260603-aou-grafiki-ig-stories-png-1080x1920-przez-p/) |
| 260603-bzf | Newsletter anti-bot: Cloudflare Turnstile (graceful skip bez kluczy) + honeypot pole `website` + cleanup_junk_subscribers command | 2026-06-03 | e23c02e | — | [260603-bzf-newsletter-anti-bot-cloudflare-turnstile](.planning/quick/260603-bzf-newsletter-anti-bot-cloudflare-turnstile/) |
| 260608-dau | Fix rate-limit 429 w run_weekly_research: max_uses na web_search + obsluga RateLimitError z retry-after w call 1 i call 2 | 2026-06-08 | 9177dfc | — | [260608-dau-fix-rate-limit-429-w-run-weekly-research](.planning/quick/260608-dau-fix-rate-limit-429-w-run-weekly-research/) |
| 260608-e71 | Napraw promote_to_blogpost: skladaj body z intro+sections, excerpt z meta_description (akcja zawsze failowala — czytala nieistniejace klucze) | 2026-06-08 | de51a9b | — | [260608-e71-napraw-promote-to-blogpost-skladaj-body-](.planning/quick/260608-e71-napraw-promote-to-blogpost-skladaj-body-/) |

## Session Continuity

Last session: 2026-06-03T08:05:00.000Z
Stopped at: Completed quick task 260603-aou (IG Stories PNG generator + AI prompty)
Resume file: None
