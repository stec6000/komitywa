---
phase: quick-260715-hqv
plan: 01
subsystem: frontend-theme
tags: [css, background, texture, svg, scroll-driven-animations]
requires: []
provides:
  - "Globalna warstwa dekoracji tła .page-sketches w base.html"
  - "Tekstura kraft (ziarno + kierunkowe włókna) na body::after"
  - "6 ołówkowych szkiców składników jako data-URI SVG w main.css"
affects: [templates/base.html, static/css/main.css]
tech-stack:
  added: []
  patterns:
    - "CSS scroll-driven animations (animation-timeline: view()) z fallbackiem @supports"
    - "Inline data-URI SVG dla dekoracji bez nowych plików graficznych"
key-files:
  created: []
  modified:
    - templates/base.html
    - static/css/main.css
decisions:
  - "Szkice ukryte całkowicie na <=900px (priorytet: zero kolizji z treścią na mobile)"
  - "Efektywna opacity ziarna+włókien zredukowana z ~0.36 do ~0.07 (kraft ma być namacalny, nie brudny)"
  - "Scroll-drift przez zmienną --sk-rot per szkic w jednym @keyframes (mniej duplikacji)"
metrics:
  duration: "~35 min (z przerwą na reset limitu sesji)"
  completed: "2026-07-15"
---

# Quick Task 260715-hqv: Ożywienie tła strony (tekstura kraft + szkice) Summary

Tekstura kraft z kierunkowymi włóknami + 6 bladych ołówkowych szkiców składników (data-URI SVG) w marginesach całej witryny, z CSS-only scroll-driftem i pełnym fallbackiem — zero JS, zero nowych plików graficznych.

## Tasks

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Globalna warstwa dekoracji w base.html | 8ece8bb | templates/base.html |
| 2 | Tekstura kraft + styl szkiców + scroll-drift | ea45a16 | static/css/main.css |
| 3 | Checkpoint human-verify (screenshoty zebrane automatycznie) | — | PNG w katalogu zadania (niecommitowane) |

## What Was Done

**Task 1 — base.html:**
- Kontener `<div class="page-sketches" aria-hidden="true">` wpięty raz, tuż po skip-linku, przed navbar.
- 6 pustych elementów `<i class="sk sk-*">`: thyme, onion, carrot, bowl, fork, sprig.
- Bez inline stylów, bez zmian w skryptach.

**Task 2 — main.css:**
- **Kraft (edycja istniejącego `body::after`):** dodany drugi data-URI SVG feTurbulence z `baseFrequency='0.012 0.9'` (kierunkowe włókna papieru w tonie --ink); efektywna opacity ziarna+włókien obniżona do `calc(var(--texture-grain) * 0.06)` ≈ 0.072 (w widełkach 0.05–0.09 z planu). Warstwy fixed z-index 0/1 pod treścią (z-index 2) zachowane.
- **`.page-sketches`:** `position: absolute; inset: 0; z-index: 0; pointer-events: none; overflow: hidden;` + `body { position: relative; }` (absolute, nie fixed — szkice w przepływie dokumentu, mają zakres scrolla dla `view()`).
- **6 szkiców `.sk-*`:** inline data-URI SVG rysowane nieregularnymi ścieżkami (odręczny charakter, `fill='none'`, `stroke='%232a2420'`, `stroke-linecap='round'`, grubość 1.8–2), opacity 0.075–0.09, rotacje od -9deg do 7deg, rozmiary 100–135px, pozycje przy krawędziach viewportu (left/right 10–16px) rozłożone na 8% / 24% / 45% / 62% / 80% / 92% wysokości dokumentu.
- **Scroll-drift:** owinięty w `@media (prefers-reduced-motion: no-preference)` + `@supports (animation-timeline: view())`; `@keyframes sk-drift` prostuje szkic z `--sk-rot` + translateY(14px) do neutralnej pozycji przy wejściu w viewport (`animation-range: entry 0% cover 60%`). Firefox/starsze Safari: statyczne rotacje. Reduced motion: brak ruchu.
- **Mobile:** `@media (max-width: 900px) { .page-sketches { display: none; } }` — zero kolizji na wąskich ekranach.

## Checkpoint: Screenshoty (do oceny przez użytkownika)

Zebrane headless Chrome (serwer runserver 127.0.0.1:8010, zatrzymany po zrzutach). PNG NIE są commitowane:

- `.planning/quick/260715-hqv-o-yw-t-o-strony-tekstura-papieru-kraft-o/260715-hqv-home-1440.png` — home desktop 1440, full-page (4720px)
- `.planning/quick/260715-hqv-o-yw-t-o-strony-tekstura-papieru-kraft-o/260715-hqv-home-390.png` — home mobile 390, full-page
- `.planning/quick/260715-hqv-o-yw-t-o-strony-tekstura-papieru-kraft-o/260715-hqv-recipe-1440.png` — /przepisy/weganskie-ragu-z-tofu/ desktop 1440, full-page

Ocena własna wykonawcy (na powiększonych cropach 1:1):
1. Tekstura namacalna, prawie niewidoczna — nie wygląda jak szum, kontrast tekstu bez zmian.
2. Szkice blade (opacity 0.075–0.09), wyłącznie w marginesach; na 1440px kolumna treści (1280px + padding) zostawia ~116px marginesu — szkice mieszczą się przy krawędzi, nie zachodzą na tekst ani zdjęcia.
3. Mobile 390: szkice ukryte, treść czysta.
4. Strona przepisu: tło spójne, składniki/przygotowanie czytelne, tła sekcji/kart/polaroidów nietknięte.
5. Scroll-drift: mała amplituda (kilka stopni + 14px), headless screenshot pokazuje stan statyczny — do oceny na żywo.

## Deviations from Plan

None - plan executed exactly as written. (Checkpoint human-verify zautomatyzowany zgodnie z instrukcją orkiestratora: screenshoty zebrane, decyzja "approved/poprawki" należy do użytkownika.)

## Known Stubs

None.

## Threat Flags

None — zmiany czysto prezentacyjne (CSS + statyczny HTML dekoracyjny, aria-hidden, pointer-events: none).

## Verification

- Task 1 grep gate: PASSED (`page-sketches` + dokładnie 6 `.sk`)
- Task 2 grep gate: PASSED (page-sketches, sk-thyme, pointer-events:none, @supports animation-timeline, prefers-reduced-motion, max-width:900px)
- Brak nowych plików .js/graficznych; zmiany tylko w base.html i main.css
- Istniejące tła sekcji/kart/polaroidów niezmienione (poza subtelną korektą body::after)

## Self-Check: PASSED

- Wszystkie zmodyfikowane pliki, screenshoty i SUMMARY istnieją na dysku
- Commity 8ece8bb i ea45a16 obecne w historii gałęzi
- Brak usunięć plików w zakresie ce16d41..HEAD
- Jedyne niezacommitowane pliki: SUMMARY.md (commit po stronie orkiestratora) i 3 PNG (celowo niecommitowane)
