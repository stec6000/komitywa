---
phase: quick-260608-kke
plan: 01
subsystem: content
tags: [instagram-stories, storyslide, pillow, renderer, admin, ai-prompt]
status: complete

provides:
  - "Model StorySlide (wiersze per slajd) + migracja 0003 + upload background_image"
  - "StoryRenderer layout A (zdjecie + gradient scrim + headline/subtext) + fallback kolor marki, bez emoji"
  - "Akcja promote_to_story_slides + StorySlideAdmin (upload, AI-prompt, Generuj PNG) + readonly inline"
  - "build_story_image_prompt (pionowy 9:16 sufiks) — gotowy prompt do zewnetrznego generatora"
  - "FORMAT_PROMPT: stories ze {slide_type, headline, subtext, bg_color, visual_hint}"

key-files:
  created:
    - content/migrations/0003_storyslide.py
  modified:
    - content/models.py
    - content/admin.py
    - content/services/story_renderer.py
    - content/services/ai_prompts.py
    - content/management/commands/run_weekly_research.py
    - content/management/commands/generate_story_images.py
    - content/templates/admin/content/weeklyresearch/_preview.html

key-decisions:
  - "Slajdy jako model StorySlide (jak BlogPost) — natywny upload ImageField, inline w adminie"
  - "Zrodlo zdjec: reczny upload + gotowy AI-prompt do skopiowania (BEZ integracji z API obrazow)"
  - "Layout A: zdjecie na calosc + gradient scrim u dolu (czytelnosc bialego tekstu niezalezna od jasnosci zdjecia)"
  - "Emoji usuniete; tekst = headline (<=55) + subtext (<=150)"
  - "FORMAT_PROMPT swiadomie zmieniony (nie-verbatim) — PROMPTS-VERBATIM.md zsynchronizowany"

requirements-completed: []

duration: ~18min
completed: 2026-06-08
---

# Quick 260608-kke: Ulepszone IG Stories (kierunek A)

**Stories z jednego zdania na plaskim kolorze → zdjecie na calosc + bogatszy tekst (nagłowek + rozwiniecie) + reczny upload zdjecia + gotowy AI-prompt.**

## Zakres (5 zadan, wg speca docs/superpowers/specs/2026-06-08-ig-stories-enhancement-design.md)

1. **FORMAT_PROMPT** — schemat `instagram_stories` z `{slide_type, text, bg_color, emoji}` na `{slide_type, headline, subtext, bg_color, visual_hint}`; PROMPTS-VERBATIM.md zaktualizowany.
2. **Model StorySlide** (+ migracja 0003) — FK research, order, slide_type, headline(90), subtext, bg_color, visual_hint, background_image (ImageField upload). + `build_story_image_prompt`.
3. **StoryRenderer** — layout A (cover-crop 1080x1920 + gradient scrim + eyebrow PL + headline bold + subtext), fallback kolor marki; usuniety stary tryb emoji. `render()` przyjmuje dict ORAZ obiekt StorySlide.
4. **Admin** — `promote_to_story_slides` (idempotentna, fallback text->headline), `StorySlideAdmin` (upload, AI-prompt readonly + Kopiuj, Generuj PNG), readonly inline na WeeklyResearchAdmin.
5. **Preview + CLI** — zakladka Stories (headline+subtext, AI-prompt, miniatura); `generate_story_images` renderuje z `wr.story_slides`, sciezka PNG bez zmian.

## Weryfikacja

- `manage.py check` 0 issues; `makemigrations --check` clean.
- gsd-verifier: **7/7 must-haves** potwierdzone wzgledem realnego kodu (status human_needed tylko dla rzeczy przegladarkowych).
- **Wizualnie potwierdzone PNG** (renderowane realnie i ogladniete):
  - Layout A na ciemnym zdjeciu — OK.
  - Layout A na niemal bialym zdjeciu (stress scrim) — biały tekst nadal czytelny dzieki gradientowi.
  - Fallback (kolor marki) — czysty, polskie znaki (ą,ó,ł,ń) renderuja sie poprawnie.
- Pozostaje do klikniecia: przyciski „Kopiuj" (navigator.clipboard) w adminie/preview — standardowy JS, do potwierdzenia w przegladarce.

## Commity (kod)

- `c8d44c9` FORMAT_PROMPT stories schemat
- `d978366` model StorySlide + build_story_image_prompt
- `666cf35` StoryRenderer layout A + fallback
- `19a0134` admin promote_to_story_slides + StorySlideAdmin
- `d98a9f2` preview Stories + CLI na StorySlide

## Deployment / uzycie

- Wymaga **wdrozenia na mydevil** (push → auto-deploy; `deploy.sh` robi `migrate --noinput`, wiec migracja 0003 zaaplikuje sie sama).
- Nowy schemat stories obowiazuje dla **nowych** researchy. Dla istniejacych: `run_weekly_research --retry-format --force` regeneruje JSON nowym promptem; potem akcja *Promuj stories do StorySlide*.
- Workflow operatora: research → *Promuj stories* → (edytuj tekst / wgraj zdjecie / skopiuj AI-prompt) → *Generuj PNG* → pobierz.
