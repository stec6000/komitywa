---
phase: quick-260715-exh
plan: 01
subsystem: frontend
tags: [home, featured-recipe, css, templates, ux]
requires: []
provides:
  - "Zbalansowana sekcja 'przepis tygodnia' na home (mini-meta + niższe zdjęcie 4/3 + wyśrodkowanie)"
affects:
  - templates/pages/home.html
  - static/css/main.css
tech-stack:
  added: []
  patterns:
    - "Ramki meta w stylu .kk-meta ze strony przepisu (featured-meta jako lżejsza wariacja)"
key-files:
  created: []
  modified:
    - templates/pages/home.html
    - static/css/main.css
decisions:
  - "Kategoria owinięta w {% if featured_recipe.category %} — pole bywa null, cała ramka pomijana gdy brak"
  - "Mobile (<=900px) resetuje .featured align-items do stretch, aby po zestackowaniu kolumny renderowały się naturalnie od góry"
metrics:
  duration: "~15 min"
  completed: "2026-07-15"
  tasks: 2
  files: 2
---

# Quick 260715-exh: Balans sekcji „przepis tygodnia" Summary

Sekcja „przepis tygodnia" na home została zbalansowana: usunięto wielką pustkę pod tekstem w lewej kolumnie przez (1) obniżenie zdjęcia z portretu 4/5 do 4/3 z `max-height: 480px`, (2) wzbogacenie lewej kolumny o mini-meta (porcje / trudność / kategoria) w ramkach spójnych ze stroną przepisu, (3) wyśrodkowanie zawartości lewej kolumny w pionie względem zdjęcia.

## Co zrobiono

### Task 1 — Mini-meta w lewej kolumnie (markup)
`templates/pages/home.html`: po `<p class="featured-blurb">` a przed inline flex-row z CTA dodano `<div class="featured-meta">` z trzema `featured-meta-item`:
- **porcje** — `{{ servings }} porcj{a|e|i}` (wzorzec liczebnika jak w recipes/detail.html)
- **trudność** — `{{ difficulty }}`
- **kategoria** — `{{ category.name|lower }}`, owinięte w `{% if featured_recipe.category %}` (null-safe)

Bez hashtagów. Prawa kolumna, CTA i `prep_time` nietknięte.

### Task 2 — Niższe zdjęcie + wyśrodkowanie + style meta (CSS)
`static/css/main.css` (blok Featured recipe):
- `.featured` → dodano `align-items: center`
- `.featured-img` → `aspect-ratio: 4/5` → `4/3` + `max-height: 480px` (`object-fit: cover` już był)
- Nowe reguły `.featured-meta`, `.featured-meta-item` (+`:nth-child(even)` obrót/paper-2), `.featured-meta-label`, `.featured-meta-value` — lżejsza wariacja ramek `.kk-meta`
- `@media (max-width:900px)` → `.featured { align-items: stretch; }` (reset centrowania po zestackowaniu)

## Weryfikacja (checkpoint human-verify — screenshoty zamiast oczekiwania)

Środowisko: `.env`, `db.sqlite3`, `public/media/recipes/weganskie-ragu-z-tofu.jpg` skopiowane z głównego repo; `.venv` głównego repo. Featured recipe = najnowszy przepis „Wegańskie ragù z tofu" (servings 4, difficulty latwy, kategoria Obiady, ze zdjęciem) — sekcja widoczna.

Screenshoty (headless google-chrome-stable, pełna strona, NIE commitowane):
- `.planning/quick/260715-exh-balans-sekcji-przepis-tygodnia-wype-nij-/featured-desktop-1440.png` (1440×6800)
- `.planning/quick/260715-exh-balans-sekcji-przepis-tygodnia-wype-nij-/featured-mobile-390.png` (390×9000)

**Desktop 1440px:** sekcja zbalansowana — mini-meta (porcje/trudność/kategoria) widoczne pod opisem, zdjęcie niższe (4/3, penne w misce wypełnia ramkę cover), tekst wycentrowany w pionie względem zdjęcia, brak wielkiej pustej przestrzeni pod CTA.

**Mobile 390px:** kolumny stackują się pionowo (data → tytuł → opis → mini-meta → CTA + 45 min → zdjęcie), meta renderują się naturalnie od góry (stretch), wszystko czytelne, nic nie wystaje.

`python manage.py check` — brak problemów.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

- templates/pages/home.html — FOUND (zawiera `featured-meta-item`)
- static/css/main.css — FOUND (zawiera `.featured-meta-item`, `aspect-ratio: 4/3`, `align-items: center`)
- Commit 3bb58a4 (Task 1) — FOUND
- Commit 251e680 (Task 2) — FOUND
