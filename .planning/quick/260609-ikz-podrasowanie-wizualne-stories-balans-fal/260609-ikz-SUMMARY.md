---
phase: quick-260609-ikz
plan: 01
subsystem: content
tags: [instagram-stories, story-renderer, pillow, visual-polish]
status: complete

provides:
  - "Fallback (bez zdjecia): tekst wysrodkowany w pionie zamiast bottom-anchor"
  - "Wordmark KUCHENNA KOMITYWA (dol-srodek) na wszystkich slajdach"
  - "Progress dots (gora-srodek): biezacy slajd jasny, reszta przyciemniona"
  - "render/render_to_file: opcjonalne index/total (dots tylko gdy podane)"

key-files:
  modified:
    - content/services/story_renderer.py
    - content/admin.py
    - content/management/commands/generate_story_images.py

key-decisions:
  - "Layout A bottom-anchor podniesiony (margines na wordmark); fallback vertical-center"
  - "Dots rysowane tylko gdy index+total podane — stare wywolania bez zmian"
  - "Legacy dict-based generate_story_images_action niezmieniona (poza zakresem)"

requirements-completed: []

duration: ~10min
completed: 2026-06-09
---

# Quick 260609-ikz: Podrasowanie wizualne IG stories (pakiet 1+2+3)

**Stories dostaly profesjonalny szlif: zbalansowany fallback (tekst wysrodkowany), znak marki na dole i progress dots u gory.**

## Co zrobiono (content/services/story_renderer.py + 2 wywolania)

1. **Balans fallbacku** — gdy brak background_image, blok eyebrow+headline+subtext wysrodkowany w pionie (1080x1920); layout A (ze zdjeciem) zostaje bottom-anchor (dol=scrim), ale podniesiony o margines na wordmark.
2. **Wordmark** — tekstowy "KUCHENNA KOMITYWA" (letter-spaced, blended/przyciemniony) na dole-srodku; bialy przy zdjeciu / text_color_for_bg w fallbacku.
3. **Progress dots** — rzad kropek u gory-srodku, kropka biezacego slajdu jasna, reszta przyciemniona.
- Sygnatura: `render(slide, index=None, total=None)` + `render_to_file(..., index, total)`. Dots TYLKO gdy index+total podane (stare wywolania dzialaja bez dots).
- Wywolania przekazujace index+total: `StorySlideAdmin` akcja "Generuj PNG" + CLI `generate_story_images` (enumerate start=1, total=count).

## Weryfikacja

- `manage.py check` 0 issues.
- Render smoke: zdjecie+1/7, fallback+3/7, bez index/total (bez dots) — wszystkie PNG 1080x1920, brak wyjatku.
- **Potwierdzone wizualnie** (realne PNG): layout A (dots 1/7 + wordmark + tekst podniesiony) i fallback (tekst wysrodkowany + dots 3/7 + wordmark) — czysto, polskie znaki OK.

## Commity

- `22dc6fc` renderer — vertical-center fallback, wordmark, progress dots, index/total
- `6681fd5` przekaz index/total do render_to_file z admin akcji i CLI

## Deployment

Renderer-only (zero zmian w modelu/migracjach/danych). Wymaga push na main → auto-deploy. Po wdrozeniu nowe PNG generowane akcja "Generuj PNG" / CLI dostana dots+wordmark; istniejace PNG trzeba przegenerowac.
