---
phase: quick-260603-aou
plan: 01
subsystem: content
tags: [ig-stories, png-generator, pillow, admin, ai-prompts, deploy]
dependency_graph:
  requires:
    - content.WeeklyResearch (model with formatted_json["instagram_stories"])
    - Pillow (already in requirements.txt)
  provides:
    - content.services.colors.text_color_for_bg (single source of truth)
    - content.services.story_renderer.StoryRenderer (PIL renderer 1080x1920)
    - content.services.ai_prompts.AI_IMAGE_BRAND_SUFFIX
    - content.management.commands.generate_story_images (CLI)
    - content.admin.generate_story_images_action (admin action)
    - content.views.WeeklyResearchStoriesZipView (staff-only ZIP download)
  affects:
    - content.templatetags.content_extras (delegate to services.colors)
    - content/templates/admin/content/weeklyresearch/_preview.html
    - content/templates/admin/content/weeklyresearch/change_form.html
tech_stack:
  added: [Noto Sans fonts (bundled), NotoColorEmoji (bundled)]
  patterns: [services layer, single-source-of-truth helpers, staff-only views]
key_files:
  created:
    - content/services/__init__.py
    - content/services/colors.py
    - content/services/story_renderer.py
    - content/services/ai_prompts.py
    - content/fonts/NotoSans-Regular.ttf
    - content/fonts/NotoSans-Bold.ttf
    - content/fonts/NotoColorEmoji.ttf
    - content/management/commands/generate_story_images.py
  modified:
    - content/admin.py
    - content/views.py
    - content/urls.py
    - content/templatetags/content_extras.py
    - content/templates/admin/content/weeklyresearch/_preview.html
    - content/templates/admin/content/weeklyresearch/change_form.html
    - content/static/content/admin/weekly_research_preview.css
    - content/README.md
decisions:
  - Brand palette mapping (text_color_for_bg) hardcoded — algorytm luminancji nieprzydatny dla zamknietej palety 5 kolorow
  - NotoColorEmoji (10.1 MiB) bundled — pod 12 MiB budget, emoji widoczne na story PNG
  - ZIP build in-memory (BytesIO) — ~50KB/PNG x 6-7 sztuk = ~400KB, pomijalne dla shared hosting
  - URL pattern weeklyresearch_stories_zip umieszczony PRZED <slug:slug>/ w content/urls.py (kolejnosc match)
  - generate_story_images NIE odpalany na prod (per constraints — user uruchomi sam pierwszy raz)
metrics:
  duration_minutes: 25
  completed_date: 2026-06-03
---

# Phase quick-260603-aou: IG Stories PNG generator + AI prompty Summary

Pillow renderuje IG Stories PNG (1080x1920) z brand palette z formatted_json["instagram_stories"], admin pokazuje miniatury + ZIP download; pod kazdym IG postem prompt AI z brand suffix (Bialystok, rzemieslnicza fotografia).

## What Was Built

### Services layer (new)
- `content/services/colors.py` — `text_color_for_bg(bg_hex)` single source of truth (przeniesione z templatetags); brand palette mapping {paper, ink, olive, terracotta, mustard} -> readable text color; tolerancja hex bez `#`.
- `content/services/story_renderer.py` — `StoryRenderer` class z `render(slide) -> bytes` i `render_to_file(slide, path) -> Path`. Buduje PNG 1080x1920 (PIL): bg color + emoji (top center) + main text (auto-wrap, centered) + slide_type label (bottom, letter-spaced, blended 70% opacity). Emoji optional — NotoColorEmoji jesli istnieje, fallback do NotoSans Bold.
- `content/services/ai_prompts.py` — `AI_IMAGE_BRAND_SUFFIX` const (Bialystok, rzemieslnicza fotografia, square 1:1, no text overlay) + `build_ai_image_prompt(visual_hint)` helper.

### Fonts (bundled w repo)
- `content/fonts/NotoSans-Regular.ttf` — 562 KB (Google Fonts CDN via github.com/googlefonts/noto-fonts)
- `content/fonts/NotoSans-Bold.ttf` — 575 KB
- `content/fonts/NotoColorEmoji.ttf` — 10.1 MiB (pod 12 MiB budget); github.com/googlefonts/noto-emoji
- Total: 11.3 MiB (pod 15 MiB limit)
- NIE w `.gitignore`, fonty trafiaja do repo i deployowane gita

### CLI command
- `content/management/commands/generate_story_images.py` — `python manage.py generate_story_images --week LABEL | --latest [--force]`
- Walidacja: dokladnie jeden z `--week`/`--latest`, error gdy WR nie istnieje lub brak `instagram_stories`
- Output: `MEDIA_ROOT/weekly_research/<week_label>/stories/01_<slide_type>.png` itd.
- `--force` nadpisuje istniejace; bez `--force` pomija

### Admin (content/admin.py)
- `generate_story_images_action` — admin akcja (list view checkbox) renderuje PNG-i dla zaznaczonych WR; messages.success/warning dla licznikow
- `WeeklyResearchAdmin.get_stories_files(obj)` — skanuje `MEDIA_ROOT/weekly_research/<label>/stories/*.png`, zwraca posortowana liste dict-ow `{index, slide_type, url, filename}`
- `WeeklyResearchAdmin.change_view` override — dodaje extra_context: `ai_image_brand_suffix` (zawsze) + `stories_files`/`stories_zip_url` (gdy sa pliki)

### Views + URLs
- `content/views.py::WeeklyResearchStoriesZipView` — staff-only (`request.user.is_authenticated and is_staff` w dispatch, 403 dla anon), buduje ZIP-deflated archiwum z PNG-ow per WR, zwraca `application/zip` z attachment Content-Disposition
- `content/urls.py` — pattern `weeklyresearch_stories_zip` PRZED `<slug:slug>/` (slug capture problem); URL: `/blog/admin/content/weeklyresearch/<int:pk>/stories.zip`

### Templates + CSS
- `_preview.html` (kk-panel-stories) — `{% if stories_files %}` rzeczywiste `<img>` miniatury PNG-ow + ZIP link; `{% else %}` info + CSS placeholder fallback; CSS placeholder zachowany jako `<details>` toggle gdy sa pliki
- `_preview.html` (kk-panel-posts) — pod kazdym postem `{% if ai_image_brand_suffix %}` sekcja `.kk-post-ai-prompt` z `<pre>` preview promptu (visual_hint + brand suffix) + Copy button
- `change_form.html` — `{% include %}` jawnie przekazuje `stories_files`, `stories_zip_url`, `ai_image_brand_suffix`
- `weekly_research_preview.css` — dodane klasy: `kk-stories-{generated,actions,zip-link,placeholder-toggle,info}`, `kk-story-actual{,-img,-meta,-label,-download}`, `kk-post-ai-prompt{,-header,-actions}`, `kk-ai-prompt-preview`

### Documentation
- `content/README.md` — odznaczony punkt 3 roadmapy (DONE 260603-aou); nowa sekcja "Generowanie grafik IG" (Stories workflow + admin action + CLI + Posts AI prompts + Architektura); zaktualizowana tabela "Pliki w tym appie"

## Commit History

| # | Commit | Message |
|---|--------|---------|
| 1 | `b4a166d` | feat(content): services layer (colors, story_renderer, ai_prompts) + bundled Noto fonty |
| 2 | `2bdd49a` | feat(content): IG stories PNG generator — admin action, CLI command, ZIP download |
| 3 | `f88706e` | feat(content): admin preview — rzeczywiste PNG miniatury + AI image prompt z brand suffix |

Pushed: `git push origin main` → `19d1195..f88706e main -> main` OK.

## Deploy

| Step | Result |
|------|--------|
| paramiko SSH connect (panel84.mydevil.net) | OK |
| `bash ./deploy.sh` | OK (git fetch, pip install no-op, migrate no-op, collectstatic 0/424, app restart OK) |
| Server git HEAD | `f88706e` (matches local) |
| `manage.py check` on prod | 0 issues |
| Pillow + fonts loadable | OK (`ImageFont.truetype` Regular+Bold) |
| `StoryRenderer().render({...})` on prod | OK (19278 PNG bytes) |
| HTTP smoke `/admin/login/` | 200 |
| HTTP smoke `/` | 200 |
| HTTP smoke `/blog/` | 200 |
| `generate_story_images` na prod | NOT RUN (per constraints — user wykona sam) |

## NotoColorEmoji.ttf Status

Bundled, 10.1 MiB (pod 12 MiB limit) → emoji w story PNG renderuja sie kolorowe (bitmap font fixed size 109). W razie problemow z PIL/embedded_color fallback do `NotoSans-Bold` (czarny tekst — moze byc widoczne kolko/puste dla niektorych glifow).

## Verification Results

| Check | Result |
|-------|--------|
| `python manage.py check` (lokalnie) | 0 issues |
| `content.services.colors.text_color_for_bg` 5 kolorow brand palette + default + no-hash tolerance | OK |
| `content.templatetags.content_extras.text_color_for_bg` (delegate) | OK |
| `StoryRenderer().render(slide)` dla 4 brand kolorow | PNG bytes 30k-31k kazdy |
| `render_to_file` mkdir parents=True | OK |
| `manage.py help generate_story_images` | OK (registered) |
| Command CLI: no args / both args / nonexistent week | CommandError OK |
| `admin.WeeklyResearchAdmin.actions` zawiera `generate_story_images_action` | OK |
| `admin.WeeklyResearchAdmin.get_stories_files(None)` / nonexistent dir | `[]` |
| `reverse('content:weeklyresearch_stories_zip', kwargs={'pk':1})` | `/blog/admin/content/weeklyresearch/1/stories.zip` |
| Anon GET ZIP endpoint | 403 (Forbidden) |
| Staff GET ZIP (2 PNG-i) | 200, application/zip, attachment, 27454 bytes |
| Template parse `_preview.html` ma `stories_files`, `kk-stories-zip-link`, `kk-story-actual-img`, `kk-post-ai-prompt`, `ai_image_brand_suffix` | OK |
| Template `change_form.html` przekazuje stories_files | OK |
| CSS balanced braces | OK |
| E2E sanity (test WR 9999-W99): 2 PNG-i `01_hook.png` + `02_tip.png`, valid PNG header, >10KB | OK; cleanup OK |

## Deviations from Plan

None — plan executed exactly as written. Wszystkie 11 taskow ukonczone bez Rule 1/2/3 fixow.

## Known Limitations

- Brak auto-regenerate przy save WR (admin action ma byc wywolany swiadomie)
- Brak per-slide manual edit w adminie (caly slajd renderowany z formatted_json)
- Brak watermarku / brandingu logo na PNG (dyskutowac z userem)
- Auto-wrap w `textwrap.wrap(width=14)` jest character-based — moze dac suboptymalne lamy dla dlugich polskich slow
- Emoji renderowane jako bitmap (fixed 109px) — moze nie skalowac sie idealnie pod target 240px slot
- ZIP buduje w pamieci — przy 100+ PNG-ow zalecane StreamingHttpResponse (nie nasz scenariusz, 6-7 PNG-ow)

## Quick Win — Test CLI on prod

User moze odpalic na prod gdy bedzie gotow weekly research:
```bash
ssh jem3pizze@panel84.mydevil.net
cd ~/domains/kuchennakomitywa.pl/public_python
~/.virtualenvs/komitywa/bin/python manage.py generate_story_images --latest
```
PNG-i ladawia w `MEDIA_ROOT/weekly_research/<label>/stories/`, miniatury + ZIP download w adminie pod change view tego WR (tab IG Stories).

## Self-Check: PASSED

- File content/services/colors.py — FOUND
- File content/services/story_renderer.py — FOUND
- File content/services/ai_prompts.py — FOUND
- File content/services/__init__.py — FOUND
- File content/fonts/NotoSans-Regular.ttf — FOUND
- File content/fonts/NotoSans-Bold.ttf — FOUND
- File content/fonts/NotoColorEmoji.ttf — FOUND
- File content/management/commands/generate_story_images.py — FOUND
- Commit b4a166d — FOUND
- Commit 2bdd49a — FOUND
- Commit f88706e — FOUND
- Server HEAD = f88706e — VERIFIED
- HTTP 200 /admin/login/ — VERIFIED
- HTTP 200 / — VERIFIED
- HTTP 200 /blog/ — VERIFIED
