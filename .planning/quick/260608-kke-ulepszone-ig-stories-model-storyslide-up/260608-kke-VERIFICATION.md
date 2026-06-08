---
phase: quick-260608-kke
verified: 2026-06-08T00:00:00Z
status: human_needed
score: 7/7 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Otworz StorySlide w adminie, wgraj zdjecie tla, odpal akcje 'Generuj PNG (1080x1920)', obejrzyj wynikowy PNG layout A"
    expected: "Zdjecie cover-crop na cala wysokosc 1080x1920, ciemny gradient scrim u dolu, bialy eyebrow (PL) + headline + subtext czytelne na zdjeciu"
    why_human: "Jakosc wizualna (kontrast tekstu na zdjeciu, gradient, kadrowanie) nie da sie zweryfikowac programowo — PNG ma poprawny rozmiar, ale estetyka wymaga oka"
  - test: "W StorySlideAdmin kliknij przycisk 'Kopiuj prompt AI' przy readonly polu AI-prompt"
    expected: "Prompt (visual_hint + pionowy sufiks 9:16 1080x1920) trafia do schowka systemowego"
    why_human: "navigator.clipboard.writeText dziala tylko w przegladarce (secure context); nie testowalne bez DOM"
  - test: "W preview WeeklyResearch otworz zakladke Stories, kliknij 'Skopiuj prompt AI' przy slajdzie i 'Skopiuj wszystkie teksty stories'"
    expected: "Prompt stories (pionowy sufiks) oraz bulk teksty headline — subtext kopiuja sie poprawnie"
    why_human: "Zachowanie clipboard JS (kk-copy-btn) wymaga uruchomionej przegladarki"
---

# Quick 260608-kke: Ulepszone IG Stories (kierunek A) — Verification Report

**Task Goal:** Ulepszone IG Stories wg speca `docs/superpowers/specs/2026-06-08-ig-stories-enhancement-design.md` (kierunek A): model StorySlide + upload zdjecia + renderer layout A + AI-prompt + bogatszy tekst (headline+subtext) + admin promote/StorySlideAdmin + preview + CLI.
**Verified:** 2026-06-08
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | FORMAT_PROMPT schemat instagram_stories to {slide_type, headline, subtext, bg_color, visual_hint} — bez 'text'/'emoji' | VERIFIED | `run_weekly_research.py:68` schemat ma headline/subtext/visual_hint; izolowany blok stories nie zawiera quoted `"text"`/`"emoji"` ani slowa emoji (programowa asercja przeszla). Wytyczna STORIES (l.82-88) opisuje headline+subtext+visual_hint, paleta bg_color jako fallback. PROMPTS-VERBATIM.md zsynchronizowany + adnotacja swiadomej zmiany (l.46) |
| 2 | Operator moze zmaterializowac formatted_json['instagram_stories'] do StorySlide jedna akcja admina (idempotentnie) | VERIFIED | `admin.py:151` `promote_to_story_slides`; idempotencja przez `research.story_slides.exists()` (l.159); fallback `slide.get("headline") or slide.get("text")` (l.171-173); zarejestrowana w WeeklyResearchAdmin.actions (l.261-265, potwierdzone runtime) |
| 3 | Operator moze wgrac wlasne zdjecie tla per slajd przez ImageField w adminie | VERIFIED | `models.py:166` `background_image = ImageField(upload_to="weekly_research/story_uploads/%Y/%m/", blank, null)`; StorySlideAdmin.fields zawiera `background_image` (l.385) — edytowalne |
| 4 | StoryRenderer renderuje PNG 1080x1920 layout A (cover-crop + scrim + headline+subtext bialym tekstem) gdy jest background_image | VERIFIED | `story_renderer.py` `_cover_crop` (l.111) + `_build_scrim` (l.125) + alpha_composite (l.246-249) + bialy text (255,255,255) l.256-257. Smoke: render z testowym zdjeciem -> PNG (1080,1920) |
| 5 | StoryRenderer renderuje fallback PNG 1080x1920 (bg_color + headline + subtext) gdy brak zdjecia — bez wyjatku | VERIFIED | `story_renderer.py:259-280` galaz fallback: `Image.new(bg_rgb)` + `text_color_for_bg`. Smoke fallback (dict bez zdjecia + obiekt StorySlide bez zdjecia) -> PNG (1080,1920) bez wyjatku |
| 6 | Admin pokazuje gotowy AI-prompt z build_story_image_prompt(visual_hint) z przyciskiem Kopiuj | VERIFIED | `admin.py:397` `ai_prompt_display` wywoluje `build_story_image_prompt(obj.visual_hint)`, readonly (l.390), `<pre>`+button Kopiuj (l.405-408). Runtime: HTML zawiera visual_hint + "1080x1920" + "Kopiuj". Preview tez ma prompt stories z kk-copy-btn (l.132-137, 166-171) |
| 7 | CLI generate_story_images --week renderuje z wierszy StorySlide (nie z surowego JSON) | VERIFIED | `generate_story_images.py:60` `slides = list(wr.story_slides.all())`; CommandError gdy brak slajdow (l.61-65); iteracja po obiektach `slide.order`/`slide.slide_type` (l.77-82); sciezka PNG MEDIA/weekly_research/<week>/stories/<NN>_<slide_type>.png zachowana (l.82); `--force` zachowany (l.85). Brak `formatted_json.get("instagram_stories")` w komendzie |

**Score:** 7/7 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `content/models.py` | Model StorySlide z polami wg speca | VERIFIED | `class StorySlide` (l.138): research FK related_name=story_slides (CASCADE), order PositiveInteger, slide_type max_length=20, headline max_length=90, subtext TextField blank, bg_color max_length=9 default #f3ead7, visual_hint TextField blank, background_image ImageField, created/updated_at. Meta: ordering ["research","order"], unique_together ("research","order"), verbose_name. __str__ uzywa week_label/order/slide_type |
| `content/migrations/0003_storyslide.py` | Migracja tworzaca StorySlide | VERIFIED | CreateModel StorySlide z wszystkimi polami + options unique_together. `makemigrations --check` czysty (brak zmian niezaaplikowanych) |
| `content/services/ai_prompts.py` | build_story_image_prompt z pionowym 9:16 sufiksem | VERIFIED | `AI_STORY_BRAND_SUFFIX` (l.12) zawiera "Vertical 9:16, 1080x1920, photorealistic, no text overlay"; `build_story_image_prompt` (l.27) = hint+sufiks; pusty hint -> sam sufiks (nie crashuje). AI_IMAGE_BRAND_SUFFIX/build_ai_image_prompt nietkniete |
| `content/services/story_renderer.py` | render(dict\|StorySlide), layout A+fallback, bez emoji | VERIFIED | `_normalize` (l.76) obsluguje dict ORAZ obiekt; `def _load_background` z planu zrealizowany jako `_cover_crop`+inline open w render (funkcjonalny ekwiwalent); brak `_font_emoji`/`FONT_PATH_EMOJI`/odwolan do klucza emoji; SLIDE_TYPE_PL PL eyebrow |
| `content/admin.py` | promote + StorySlideAdmin + inline + Generuj PNG | VERIFIED | `class StorySlideAdmin` (l.372) zarejestrowany; promote_to_story_slides, generate_story_slide_pngs, StorySlideInline (readonly, has_add_permission=False) wszystkie obecne i podpiete |
| `content/templates/admin/content/weeklyresearch/_preview.html` | Zakladka Stories: headline+subtext, AI-prompt z Kopiuj, miniatura | VERIFIED | headline (`s.headline\|default:s.text`), subtext, slide_type chip, bg_color swatch; AI-prompt z ai_story_brand_suffix + kk-copy-btn; miniatury PNG (stories_files grid); link do StorySlideAdmin changelist |
| `content/management/commands/generate_story_images.py` | CLI renderujacy z StorySlide --week | VERIFIED | uzywa `wr.story_slides`; iteruje obiekty StorySlide; sciezka PNG zachowana; --help OK |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| admin.py::promote_to_story_slides | formatted_json['instagram_stories'] | iteracja + StorySlide.objects.create | WIRED | `(research.formatted_json or {}).get("instagram_stories")` (l.162) -> enumerate -> `StorySlide.objects.create` (l.181) |
| admin.py::StorySlideAdmin | ai_prompts::build_story_image_prompt | readonly pole z promptem | WIRED | `ai_prompt_display` (l.398-399) wywoluje `build_story_image_prompt`; pole w readonly_fields (l.390) i fields (l.386) |
| story_renderer.py::render | StorySlide.background_image | PIL Image.open cover-crop + scrim | WIRED | `_normalize` czyta `bg_field.path` (l.96); render: `Image.open(bg_path)` + `_cover_crop` + `_build_scrim` + alpha_composite |
| generate_story_images.py | WeeklyResearch.story_slides | wr.story_slides.all() zamiast formatted_json | WIRED | `list(wr.story_slides.all())` (l.60); brak odwolan do formatted_json w komendzie |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| StorySlideAdmin.ai_prompt_display | obj.visual_hint | StorySlide row (DB) -> build_story_image_prompt | Tak — prawdziwe pole modelu, smoke z visual_hint zwraca pelny prompt | FLOWING |
| StoryRenderer.render | headline/subtext/bg_path | _normalize z dict lub StorySlide instance | Tak — czyta realne pola/klucze, oba zrodla zweryfikowane smoke | FLOWING |
| generate_story_images | slides | wr.story_slides.all() (DB query) | Tak — realny queryset, nie statyczna lista | FLOWING |
| _preview.html stories | data.instagram_stories | WeeklyResearch.formatted_json (DB blob) | Tak — surowy JSON z modelu (z fallback s.text dla starego schematu) | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Django config czysty | `manage.py check` | System check identified no issues | PASS |
| Migracja kompletna | `makemigrations content --check --dry-run` | No changes detected | PASS |
| build_story_image_prompt(hint) | smoke | zawiera hint + '1080x1920' + '9:16'; pusty hint nie crashuje | PASS |
| Render layout A | smoke z testowym JPG | PNG (1080,1920) | PASS |
| Render fallback (dict) | smoke bez zdjecia | PNG (1080,1920) bez wyjatku | PASS |
| Render obiekt StorySlide | smoke z instancja | PNG (1080,1920) | PASS |
| Emoji usuniety | grep zrodla | brak _font_emoji/FONT_PATH_EMOJI/klucza emoji | PASS |
| Model unique_together | introspekcja | (('research','order'),) | PASS |
| StorySlideAdmin zarejestrowany | site._registry | obecny, ai_prompt_display dziala, akcja Generuj PNG, inline + promote na WR | PASS |
| CLI dziala | `generate_story_images --help` | help OK | PASS |
| FORMAT_PROMPT block | asercja izolacji | headline/subtext/visual_hint obecne, brak text/emoji | PASS |

### Requirements Coverage

| Requirement | Source Plan | Status | Evidence |
|-------------|-------------|--------|----------|
| IGS-FORMAT | Plan 01 | SATISFIED | FORMAT_PROMPT + PROMPTS-VERBATIM nowy schemat bez emoji |
| IGS-MODEL | Plan 01 | SATISFIED | StorySlide + migracja 0003 |
| IGS-PROMPT | Plan 01 | SATISFIED | build_story_image_prompt 9:16 sufiks |
| IGS-RENDER | Plan 01 | SATISFIED | StoryRenderer layout A + fallback, bez emoji |
| IGS-ADMIN | Plan 01 | SATISFIED | promote + StorySlideAdmin + inline + Generuj PNG |
| IGS-PREVIEW | Plan 01 | SATISFIED | preview Stories headline+subtext+AI-prompt+miniatura |
| IGS-CLI | Plan 01 | SATISFIED | generate_story_images z StorySlide |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| story_renderer.py | 241, 97 | `except Exception` bez logowania | Info | Swiadoma izolacja per-slajd (fallback przy uszkodzonym zdjeciu) — zgodne ze specem "blad renderu izolowany per slajd" |
| admin.py | 138, 228 | `except Exception` (noqa BLE001) | Info | Izolacja renderu w akcjach admina — celowe, komunikat messages.warning |

Brak blokujacych anti-patternow. Zadne `return null`/placeholder/TODO/stub w sciezce produktowej.

### Human Verification Required

Wszystkie automatyczne kontrole przeszly (7/7 truths, artefakty, key links, data-flow, spot-checks). Pozostaje weryfikacja wizualna/runtime, ktorej nie da sie sprawdzic programowo:

1. **Jakosc wizualna layout A** — wgraj zdjecie do StorySlide, odpal "Generuj PNG", obejrzyj PNG. Oczekiwane: cover-crop na pelny kadr, gradient scrim u dolu, czytelny bialy eyebrow PL + headline + subtext.
2. **Przycisk Kopiuj w StorySlideAdmin** — kliknij "Kopiuj prompt AI", sprawdz schowek. (navigator.clipboard dziala tylko w przegladarce.)
3. **Preview zakladka Stories** — "Skopiuj prompt AI" + "Skopiuj wszystkie teksty stories" w przegladarce.

### Gaps Summary

Brak luk. Implementacja realizuje spec kierunku A w calosci: model StorySlide z uploadem, renderer layout A (cover-crop + gradient scrim + bialy tekst) z bezpiecznym fallbackiem, pionowy AI-prompt 9:16, admin (promote idempotentny z fallback text->headline, StorySlideAdmin, readonly inline, akcja Generuj PNG), preview z headline/subtext/prompt/miniatura, CLI przestawione na wiersze StorySlide. Stary tryb emoji usuniety calkowicie. Status `human_needed` wynika wylacznie z koniecznosci wizualnej/przegladarkowej weryfikacji estetyki PNG i przyciskow clipboard — nie z brakow w kodzie.

---

_Verified: 2026-06-08_
_Verifier: Claude (gsd-verifier)_
