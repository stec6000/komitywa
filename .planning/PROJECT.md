# Kuchenna Komitywa

## What This Is

Strona informacyjna i sklep online dla firmy Kuchenna Komitywa — wegańskiej/roślinnej kuchni. Serwis łączy blog z przepisami, sprzedaż ebooków (PDF), sprzedaż gotowych produktów (dania w słoiku, ciasta z odbiorem osobistym) oraz newsletter. Całość po polsku, na Django z klasycznymi szablonami HTML.

## Core Value

Klienci mogą przeglądać przepisy, kupować ebooki i zamawiać gotowe wegańskie produkty z odbiorem osobistym — w jednym miejscu.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ Rejestracja użytkownika z email i hasłem — existing (accounts app)
- ✓ Weryfikacja email po rejestracji — existing (allauth email confirmation)
- ✓ Logowanie z email i hasłem — existing (dj-rest-auth login)
- ✓ Reset hasła przez email — existing (allauth password reset)
- ✓ Panel administracyjny Django — existing (accounts/admin.py)
- ✓ API REST z dokumentacją OpenAPI — existing (drf-spectacular)

### Active

<!-- Current scope. Building toward these. -->

- [x] Landing page z informacjami o firmie — Validated in Phase 2: Landing & Brand
- [ ] Blog z przepisami (pełne przepisy, zdjęcia, kategorie, wyszukiwanie)
- [ ] Sklep z ebookami (lista, szczegóły, zakup, dostawa PDF na email)
- [ ] Sklep z produktami fizycznymi (dania w słoiku, ciasta, odbiór osobisty)
- [ ] Koszyk zakupowy i proces zamówienia
- [ ] Płatności online przez Przelewy24
- [ ] Newsletter (zbieranie subskrypcji, zarządzanie)
- [ ] Identyfikacja wizualna (logo, kolory, typografia, od zera) — brand CSS established in Phase 1
- [x] Szablony Django (frontend na Django templates) — Validated in Phase 1: Foundation

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Wysyłka kurierska — tylko odbiór osobisty w v1
- Wersja angielska — strona tylko po polsku
- React/Vue SPA — frontend na Django templates
- OAuth/social login — email/hasło wystarczające w v1
- Aplikacja mobilna — web-first
- Real-time chat — nie potrzebny dla tego typu strony
- Pobieranie ebooków ze strony — ebooki dostarczane wyłącznie na email

## Context

- Istniejący backend Django 5.2 z systemem użytkowników (email-only, allauth + dj-rest-auth)
- Obecna architektura to API-only (REST) — wymaga przebudowy na Django templates z widokami HTML
- SQLite w dev, brak konfiguracji produkcyjnej
- django-environ configured for .env loading (replaced python-dotenv in Phase 1)
- Brak CI/CD, Dockera, lintingu
- Email templates już po polsku
- CORS skonfigurowany dla localhost:3000 (frontend dev)

## Constraints

- **Stack**: Django 5.2 + Django templates (bez SPA)
- **Płatności**: Przelewy24
- **Język**: Tylko polski
- **Dostawa ebooków**: Wyłącznie na email (PDF)
- **Dostawa produktów**: Tylko odbiór osobisty
- **Identyfikacja wizualna**: Do stworzenia od zera

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Django templates zamiast SPA | Prostsza budowa, lepsze SEO dla landing page i bloga | — Pending |
| Przelewy24 jako bramka płatności | Popularny w Polsce, obsługuje BLIK i przelewy | — Pending |
| Odbiór osobisty only | Uproszczenie logistyki w v1 | — Pending |
| Email-only dostawa ebooków | Prostszy flow, brak potrzeby systemu pobierania | — Pending |
| Przebudowa z API-only na templates | Istniejący backend API → dodanie warstwy HTML | — Pending |

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
*Last updated: 2026-03-31 after Phase 2 completion — Landing & Brand live*
