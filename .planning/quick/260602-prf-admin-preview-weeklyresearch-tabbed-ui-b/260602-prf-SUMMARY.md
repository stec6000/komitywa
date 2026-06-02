---
phase: 260602-prf
plan: 01
subsystem: content
tags:
  - admin
  - ui
  - templates
  - clipboard
  - brand-styling
status: complete
key-files:
  created:
    - content/templatetags/__init__.py
    - content/templatetags/content_extras.py
    - content/templates/admin/content/weeklyresearch/change_form.html
    - content/templates/admin/content/weeklyresearch/_preview.html
    - content/static/content/admin/weekly_research_preview.css
    - content/static/content/admin/weekly_research_preview.js
  modified:
    - content/admin.py
commit: b6bed65
duration_minutes: 8
---

# Admin Preview WeeklyResearch — SUMMARY

## What was built

Pełny brand-styled preview `formatted_json` w adminie Django na `/admin/content/weeklyresearch/<id>/change/`:

1. **3 zakładki CSS-only** (Blog | IG Posty | IG Stories) — przełączanie przez ukryte `<input type="radio">` + general sibling selector. Zero JS dla tab switching.

2. **Tab Blog** — tytuł, intro, sekcje, tagi-chipy, meta_description. Per-element przyciski "Skopiuj" + jeden master "Skopiuj całość bloga (Markdown)" generujący gotowy markdown.

3. **Tab IG Posty** — 5 kart z caption + hashtagami + visual_hint w stonowanej ramce. Per-post: "Skopiuj post" (caption+tags), "Skopiuj wizualkę". Master: "Skopiuj wszystkie posty".

4. **Tab IG Stories** — grid kart w realistycznej proporcji `aspect-ratio: 9/16` (140px szerokie), każda z prawdziwym `bg_color`, emoji u góry (32px), tekst na środku, label `slide_type` u dołu (caps, opacity 0.7). Hex pod kartą. Per-card "Tekst" + master "Skopiuj wszystkie teksty stories".

5. **Custom template filter `text_color_for_bg`** — case-insensitive mapping 5 brand colors:
   - `#2a2420` (ink) → `#f3ead7` (jasny tekst)
   - `#6b7a3a` (oliwka) → `#f3ead7`
   - `#b6562e` (terakota) → `#f3ead7`
   - `#c89a3a` (musztarda) → `#2a2420` (ciemny — żółty wymaga ciemnego tekstu)
   - `#f3ead7` (papier) → `#2a2420`
   - Default: `#2a2420`

6. **Toast "Skopiowano!"** — fixed bottom-right, fade in/out po 1.5s. Vanilla CSS animation.

7. **Vanilla JS (53 linie, IIFE)** — single delegated click listener na `[data-copy-text]`, używa `navigator.clipboard.writeText()` + pokazuje toast.

## Brand consistency

CSS używa zmiennych z `:root`:
- `--paper: #f3ead7` (tło preview)
- `--paper-2: #ebe0c5` (alt)
- `--paper-shadow: #d9c9a3` (border)
- `--ink: #2a2420` (tekst główny)
- `--ink-soft: #5a4a3a` (sekundarny)
- `--accent: #6b7a3a` (oliwka — active tab, primary button)
- `--accent-2: #b6562e` (terakota — copy buttons)
- `--accent-3: #c89a3a` (musztarda — focus/hover accent)

Spójne z `static/css/main.css` (front-end strony).

## Edge cases

- `formatted_json is None` (status=failed bez JSON) → preview nie renderuje, admin nadal działa
- Buttons mają `type="button"` (admin change_form jest `<form>` — uniknęliśmy przypadkowego submit)
- Newlines w `data-copy-text` przez `&#10;` (HTML entity numeryczne, przepuszczane przez Django auto-escape)

## Validation (local)

- `manage.py check` → 0 issues
- `collectstatic --noinput --dry-run` → wylistował 2 nowe pliki (CSS + JS)
- Filter assert: `text_color_for_bg('#2a2420') == '#f3ead7'`, `text_color_for_bg('#c89a3a') == '#2a2420'`, default for unknown OK
- Template load: `get_template('admin/content/weeklyresearch/change_form.html')` OK

## Deploy

- Commit: `b6bed65` — `feat(content): admin preview WeeklyResearch — tabbed UI z Copy to clipboard`
- Push: `b620aa9..b6bed65` → `origin/main`
- Deploy (paramiko + bash deploy.sh): exit 0, app restarted, 2 static files copied
- Server HEAD: `b6bed65` (matches push)
- Server `manage.py check`: 0 issues
- `https://kuchennakomitywa.pl/admin/login/`: HTTP 200

## What this means for the user

Teraz po wejściu na admin → `WeeklyResearch` → 2026-W22:
- W górnej części widzisz brand-styled preview z 3 zakładkami
- Klikasz "Skopiuj sekcję" / "Skopiuj post" / "Tekst" — content ląduje w schowku
- "Skopiuj całość bloga (Markdown)" daje gotowy tekst do wklejenia np. w edytorze blogu
- Stories pokazują się jako realistyczne 9:16 kafelki z prawdziwymi kolorami — wizualnie wiesz jak będą wyglądały na IG

Surowy JSON `formatted_json` nadal jest widoczny poniżej preview (jako readonly field) — dla debugowania, gdyby coś się rozjechało.

## Files

- **Created:** 6 plików (~400 LOC łącznie: 28 Python + 315 CSS + 53 JS + 2 templates)
- **Modified:** `content/admin.py` (1 linia: `change_form_template`)
- **Commit:** `b6bed65`
