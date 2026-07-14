---
phase: quick-260714-li1
plan: 01
subsystem: recipes (frontend)
tags: [ux, redesign, templates, css, templatetags]
requires: []
provides: [redesigned-recipe-detail, format_ingredients-filter]
affects: [templates/recipes/detail.html, static/css/main.css]
tech-stack:
  added: []
  patterns: [django-custom-templatetag, css-grid-mobile-first-order-swap, sticky-column]
key-files:
  created:
    - recipes/templatetags/__init__.py
    - recipes/templatetags/recipe_extras.py
  modified:
    - templates/recipes/detail.html
    - static/css/main.css
decisions:
  - "Zachowano definicję CSS .kk-detail-sidebar (używa jej templates/shop/detail.html) — usunięto tylko z widoku przepisu"
  - "Mobile-first grid single-column ze składnikami przed krokami w DOM; order swap dopiero w @media min-width:992px"
metrics:
  duration: ~15 min
  completed: 2026-07-14
requirements: [LI1-UX-DETAIL]
---

# Phase quick-260714-li1 Plan 01: Redesign strony szczegółów przepisu Summary

Przebudowa `/przepisy/<slug>/` pod UX: składniki przeniesione do prawej sticky kolumny, meta dane (czas/porcje/trudność/data) w jednym notatnikowym meta-barze pod tytułem, usunięty redundantny sidebar „notatnik", nagłówki grup składników wyróżnione przez nowy filtr `format_ingredients`.

## What Was Built

- **Task 1 — filtr `format_ingredients`** (`recipes/templatetags/recipe_extras.py`, commit `15c95ba`): nowy pakiet templatetags dla app `recipes`. Filtr renderuje `ingredients_text` jako `<ul class="kk-ingredient-list">`; linie kończące się `:` dostają klasę `kk-ingredient-group` (nagłówek grupy), pozostałe `kk-ingredient-item`. Każda linia przechodzi przez `django.utils.html.escape` przed `mark_safe` (ochrona XSS — treść edytowalna w adminie, T-li1-01 mitigate).
- **Task 2 — redesign `detail.html` + CSS** (commit `c10f50d`):
  - `{% load recipe_extras %}` dodane; JSON-LD w `extra_js` nietknięty.
  - Nowa struktura: hero (bez zmian) → eyebrow z kategorią → `<h1>` → `.kk-meta-bar` (czas/porcje/trudność/dodano) → `.lead` → `.tag-row` (przeniesione z usuniętego sidebaru) → `.kk-recipe-body`.
  - `.kk-recipe-body`: w DOM NAJPIERW `<aside class="kk-recipe-ingredients-col">` (sticky składniki + link powrotny), POTEM `<div class="kk-recipe-steps-col">` (kroki + „Od autora").
  - Stary `<aside class="kk-detail-sidebar">` usunięty z widoku przepisu.
  - CSS: `.kk-meta-bar` (notatnikowe kafelki z lekkim rotate, `--font-hand` label + `--font-display` value), `.kk-recipe-body` (mobile-first single-column grid), `.kk-ingredients-sticky` (`position:sticky; top:100px; max-height:calc(100vh-130px); overflow-y:auto`), style list/group headers, oraz w `@media (min-width:992px)` dwukolumnowy grid `minmax(0,1fr) 340px` z order swap (kroki po lewej, składniki po prawej).

## Verification / Screenshots

Serwer uruchomiony z `.venv` głównego repo na skopiowanej lokalnej bazie (przepis `weganskie-ragu-z-tofu` obecny). Screenshoty headless Chrome zapisane w katalogu zadania (NIE commitowane):

- **`li1-recipe-desktop-1440.png`** (1440×2400): hero na pełną szerokość; meta-bar (czas 45 min / porcje 4 porcje / trudność latwy / dodano 14 lipca 2026) czytelny pod tytułem jako notatnikowe kafelki; po lewej „Sposób przygotowania", po prawej sticky „Składniki" z wyróżnionymi nagłówkami grup „Tofu mielone:" i „Sos:" (font ręczny, kolor terracotta) oraz itemami z myślnikiem; „← wróć do przepiśnika" pod składnikami; brak dublującego panelu meta danych.
- **`li1-recipe-mobile-390.png`** (390×2800): meta-bar zawija się czytelnie (3 kafelki + „dodano" w drugim rzędzie); **składniki pojawiają się PRZED krokami** (poprawny mobile DOM order); nic się nie rozjeżdża; sekcja „Od autora" bez zmian.

Uwaga: hero image wymagał skopiowania pliku media z głównego repo do worktree (`public/media/recipes/weganskie-ragu-z-tofu.jpg`, gitignored) — brak pliku w worktree to kwestia środowiska, nie zmian w kodzie.

Weryfikacje automatyczne przeszły:
- Task 1: filtr zwraca `kk-ingredient-group` + `kk-ingredient-item` i escapuje `<b>` → `&lt;b&gt;`.
- Task 2: `get_template('recipes/detail.html')` OK; obecne `kk-recipe-body`, `format_ingredients`; brak `kk-detail-sidebar` w detail.html; obecne `kk-meta-bar` w CSS.

## Deviations from Plan

None — plan wykonany zgodnie z zapisem. Jedyna decyzja dyskrecjonalna (przewidziana w planie): definicja CSS `.kk-detail-sidebar` oraz reguła `.kk-detail-sidebar { position: static; }` w media query pozostały, bo `templates/shop/detail.html` nadal ich używa — usunięto klasę tylko z widoku przepisu.

## Known Stubs

None.

## Self-Check: PASSED

- recipes/templatetags/__init__.py — FOUND
- recipes/templatetags/recipe_extras.py — FOUND
- templates/recipes/detail.html — FOUND (modified)
- static/css/main.css — FOUND (modified)
- Commit 15c95ba — FOUND
- Commit c10f50d — FOUND
- Screenshots li1-recipe-desktop-1440.png, li1-recipe-mobile-390.png — FOUND (not committed)
