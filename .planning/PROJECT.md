# Kuchenna Komitywa

## What This Is

Strona informacyjna i sklep online dla firmy Kuchenna Komitywa — wegańskiej/roślinnej kuchni. Serwis łączy blog z przepisami, sprzedaż ebooków (PDF), sprzedaż gotowych produktów (dania w słoiku, ciasta z odbiorem osobistym) oraz newsletter. Całość po polsku, na Django z klasycznymi szablonami HTML.

v1.0 MVP dostarczył kompletny serwis: od fundacji szablonów przez sklep, płatności Przelewy24 po newsletter z double opt-in.

## Current Milestone: v1.1 Wdrożenie Produkcyjne

**Goal:** Przenieść aplikację z dev na MyDevil.net z pełną konfiguracją produkcyjną (PostgreSQL, Brevo SMTP, HTTPS, P24 sandbox).

**Target features:**
- Konfiguracja środowiska produkcyjnego na MyDevil.net (WSGI/Passenger, settings prod, static/media files)
- Migracja bazy danych z SQLite na PostgreSQL
- Konfiguracja emaila przez Brevo SMTP
- HTTPS + domena (certyfikat SSL na MyDevil)
- P24 skonfigurowane w trybie sandbox na produkcji

## Core Value

Klienci mogą przeglądać przepisy, kupować ebooki i zamawiać gotowe wegańskie produkty z odbiorem osobistym — w jednym miejscu.

## Current State

**Shipped: v1.0 MVP (2026-04-04)**

- 6 phases, 16 plans, 30 tasks delivered
- ~3,600 Python LOC + Django templates
- Stack: Django 5.2, Bootstrap 5, SQLite (dev), django-environ, Przelewy24

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ Rejestracja użytkownika z email i hasłem — existing (accounts app)
- ✓ Weryfikacja email po rejestracji — existing (allauth email confirmation)
- ✓ Logowanie z email i hasłem — existing (dj-rest-auth login)
- ✓ Reset hasła przez email — existing (allauth password reset)
- ✓ Panel administracyjny Django — existing (accounts/admin.py)
- ✓ API REST z dokumentacją OpenAPI — existing (drf-spectacular)
- ✓ Szablony Django (frontend na Django templates) — v1.0 Phase 1
- ✓ Bootstrap 5 responsywny layout z brand CSS — v1.0 Phase 1
- ✓ RODO cookie consent banner — v1.0 Phase 1
- ✓ Landing page z informacjami o firmie (hero, O nas, Kontakt) — v1.0 Phase 2
- ✓ Polityka prywatności i regulamin sklepu — v1.0 Phase 2
- ✓ Blog z przepisami (lista, filtry kategorii, wyszukiwanie, JSON-LD SEO) — v1.0 Phase 3
- ✓ Sklep z produktami (katalog, karta produktu, koszyk, zamówienie) — v1.0 Phase 4
- ✓ Płatności przez Przelewy24 z webhookiem CRC — v1.0 Phase 5
- ✓ Dostarczenie ebooków PDF na email po zakupie — v1.0 Phase 5
- ✓ Email z potwierdzeniem zamówienia — v1.0 Phase 5
- ✓ Newsletter z double opt-in i wypisaniem — v1.0 Phase 6

### Active

<!-- Next milestone scope. -->

- [ ] Konfiguracja środowiska MyDevil.net (Passenger WSGI, settings prod, static/media) — v1.1
- [ ] Migracja bazy z SQLite na PostgreSQL — v1.1
- [ ] Konfiguracja Brevo SMTP na produkcji — v1.1
- [ ] HTTPS + domena z certyfikatem SSL (MyDevil) — v1.1
- [ ] P24 sandbox na środowisku produkcyjnym — v1.1
- [ ] Panel do wysyłania newsletterów (kampanie, baza subskrybentów) — odłożone (v1.2)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Wysyłka kurierska — tylko odbiór osobisty
- Wersja angielska — strona tylko po polsku
- React/Vue SPA — frontend na Django templates
- OAuth/social login — email/hasło wystarczające
- Aplikacja mobilna — web-first
- Real-time chat — nie potrzebny dla tego typu strony
- Pobieranie ebooków ze strony — ebooki dostarczane wyłącznie na email
- System komentarzy do przepisów — za dużo moderacji
- Blog (nie-przepisowy) — skupienie na przepisach

## Context

- Django 5.2 z pełną warstwą szablonów HTML (Bootstrap 5, brand CSS)
- SQLite w dev — wymaga migracji do PostgreSQL przed produkcją
- django-environ skonfigurowany dla .env
- Przelewy24 sandbox skonfigurowany — wymaga produkcyjnych danych sprzedawcy
- Email przez console backend w dev — wymaga SMTP/SendGrid w prod
- Brak CI/CD, Dockera, lintingu — tech debt v2
- Logowanie użytkowników nie jest wymagane do zakupów (flow gościa)

## Constraints

- **Stack**: Django 5.2 + Django templates (bez SPA)
- **Płatności**: Przelewy24
- **Język**: Tylko polski
- **Dostawa ebooków**: Wyłącznie na email (PDF)
- **Dostawa produktów**: Tylko odbiór osobisty
- **Identyfikacja wizualna**: Sage-olive-cream, Lora + Nunito — ustalone w Phase 1

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Django templates zamiast SPA | Prostsza budowa, lepsze SEO dla landing page i bloga | ✓ Good — SEO markup (JSON-LD) działa out of the box |
| Przelewy24 jako bramka płatności | Popularny w Polsce, obsługuje BLIK i przelewy | ✓ Good — SHA-384 webhook działa, sandbox zweryfikowany |
| Odbiór osobisty only | Uproszczenie logistyki w v1 | ✓ Good — brak potrzeby integracji z kurierami |
| Email-only dostawa ebooków | Prostszy flow, brak potrzeby systemu pobierania | ✓ Good — attachment na email działa |
| django-environ zamiast python-dotenv | Typowane zmienne env, lepsza integracja z Django | ✓ Good — uproszcza settings.py |
| Bootstrap 5 + custom CSS | Szybka budowa UI, responsywność out of the box | ✓ Good — spójny wygląd bez JS framework |
| Session-based cart (nie DB) | Prostsza implementacja, brak wymogu logowania | ✓ Good — działa dla gości |
| Double opt-in newsletter | RODO compliance, 24h token expiry | ✓ Good — zgodność prawna bez zewnętrznego ESP |
| Ebook quantity lock w koszyku | Ebook to plik cyfrowy — bez sensu zamawiać 3 kopie | ✓ Good — UX edge case obsłużony |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-10 — v1.1 milestone started (production deployment: MyDevil.net, PostgreSQL, Brevo, HTTPS)*
