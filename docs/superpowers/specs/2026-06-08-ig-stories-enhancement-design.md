# Ulepszone IG Stories — design

**Data:** 2026-06-08
**Status:** Zatwierdzony do planowania
**Kierunek wizualny:** A — zdjęcie na całość kadru + bogatszy tekst na przyciemnieniu

## Problem

Obecne IG Stories generowane z `WeeklyResearch.formatted_json["instagram_stories"]` to płaski kolor marki + jedno emoji + **jedno krótkie zdanie**, renderowane do PNG 1080×1920 (`StoryRenderer`). Efekt jest ubogi: brak zdjęcia, brak treści. Cel: slajdy ze zdjęciem tła i bogatszym tekstem (nagłówek + rozwinięcie), z możliwością ręcznego wgrania własnego zdjęcia oraz gotowym AI-promptem do wklejenia w zewnętrzny generator obrazów.

## Decyzje (zatwierdzone)

- **Źródło zdjęć:** ręczny upload własnego zdjęcia per slajd. Dodatkowo gotowy **AI-prompt** (tekst do skopiowania) — BEZ integracji z API generującym obrazy (zero kosztu/klucza). Spójne z istniejącym wzorcem postów (`build_ai_image_prompt`).
- **Workflow:** slajdy materializowane jako wiersze modelu `StorySlide` (jak `BlogPost`), z natywnym uploadem Django (`ImageField`) w adminie.
- **Limity tekstu:** `headline` ≤ 55 znaków, `subtext` ≤ 150 znaków (czytelność na ekranie telefonu).
- **Fallback bez zdjęcia:** render w kolorze marki (`bg_color`) z headline+subtext. PNG zawsze powstaje.
- **Emoji:** rezygnujemy — czyste zdjęcie + tekst.

## Architektura

Pipeline (bez zmian do kroku formatowania):
```
run_weekly_research  →  WeeklyResearch.formatted_json["instagram_stories"]
        ↓ (akcja admina: "Promuj stories do StorySlide")
   StorySlide (wiersze)  ──edycja tekstu / upload zdjęcia / kopiuj AI-prompt──>  operator
        ↓ (akcja: "Generuj PNG")
   StoryRenderer (layout A / fallback)  →  PNG 1080×1920 w MEDIA  →  pobranie / publikacja na IG
```

### Komponenty

**1. Schemat treści — zmiana w `FORMAT_PROMPT` (`content/management/commands/run_weekly_research.py`)**

Slajd `instagram_stories` z:
```json
{"slide_type": "hook|fact|tip|cta", "text": "...", "bg_color": "#hex", "emoji": "..."}
```
na:
```json
{"slide_type": "hook|fact|tip|cta", "headline": "...", "subtext": "...", "bg_color": "#hex", "visual_hint": "..."}
```
- `headline` — mocny nagłówek (≤ ~55 zn.)
- `subtext` — rozwinięcie 1–2 zdania (≤ ~150 zn.)
- `visual_hint` — opis kadru (jak w postach) → zasila AI-prompt
- `bg_color` — zostaje (fallback)
- `emoji` — usunięte ze schematu
- Wytyczna w prompcie: 6–7 slajdów, łuk hook → fact/tip → cta, każdy z headline+subtext.

⚠️ `FORMAT_PROMPT` był oznaczony jako VERBATIM (patrz `.planning/quick/260602-i1r-*/PROMPTS-VERBATIM.md`). To **świadoma** ewolucja feature'u — `PROMPTS-VERBATIM.md` zostanie zaktualizowany, żeby źródło prawdy się nie rozjechało.

**2. Model `StorySlide` (`content/models.py`) + migracja**

| Pole | Typ | Uwagi |
|------|-----|-------|
| `research` | FK(WeeklyResearch, related_name="story_slides") | |
| `order` | PositiveIntegerField | kolejność slajdu |
| `slide_type` | CharField | hook/fact/tip/cta |
| `headline` | CharField(max_length=90) | twardy bezpiecznik DB; cel redakcyjny ≤55 (egzekwowany przy promote + w prompcie) |
| `subtext` | TextField | |
| `bg_color` | CharField(max_length=9) | hex, fallback |
| `visual_hint` | TextField(blank) | do AI-promptu |
| `background_image` | ImageField(upload_to="weekly_research/story_uploads/%Y/%m/", blank) | upload operatora |
| `created_at`/`updated_at` | DateTimeField | |

`Meta`: `ordering = ["research", "order"]`, `unique_together = ("research", "order")`, `__str__`.

**3. Admin (`content/admin.py`)**
- Akcja `promote_to_story_slides(modeladmin, request, queryset)` na `WeeklyResearchAdmin` — materializuje `formatted_json["instagram_stories"]` → wiersze `StorySlide`. Idempotentna (`research.story_slides.exists()` → skip). Kompatybilność wsteczna: gdy brak `headline` (stary schemat), użyj `text` jako `headline`; `subtext`/`visual_hint` puste.
- `StorySlideAdmin`: edycja `headline`/`subtext`/`bg_color`/`slide_type`, **upload `background_image`**, pole tylko-do-odczytu z gotowym AI-promptem + przycisk **Kopiuj** (JS jak w preview), akcja **Generuj PNG** (per zaznaczone slajdy).
- Read-only inline listing `StorySlide` na `WeeklyResearchAdmin` (podgląd, link do edycji).

**4. Renderer — rozbudowa `StoryRenderer` (`content/services/story_renderer.py`)**
- Wejście: obiekt/`dict` slajdu z `headline`, `subtext`, `bg_color`, `slide_type`, opcjonalnie ścieżka `background_image`.
- **Layout A (jest zdjęcie):**
  - kadrowanie zdjęcia na 1080×1920 metodą *cover* (skaluj do wypełnienia + center-crop),
  - gradient (RGBA overlay): przezroczysty u góry → ~85% ciemny na dolnych ~45% kadru, kompozycja na zdjęciu,
  - tekst zakotwiczony u dołu: mały eyebrow z `slide_type` (PL mapping, letter-spaced) → `headline` (bold, wrap) → `subtext` (regular, wrap),
  - tekst biały (zdjęcie ma scrim), więc kontrast OK niezależnie od koloru zdjęcia.
- **Fallback (brak zdjęcia):** tło `bg_color` + headline + subtext + eyebrow (bez emoji), kolor tekstu dobrany z `colors.text_color_for_bg`.
- Nowe stałe layoutu (bottom-anchored block, gradient). Stary tryb emoji + jedno-zdaniowy usunięty.
- `slide_type` → PL eyebrow (mapa w rendererze): `hook→"NA POCZĄTEK"`, `fact→"CIEKAWOSTKA"`, `tip→"WSKAZÓWKA"`, `cta→"OD NAS"` (do dopracowania w planie; łatwo zmienić).

**5. AI-prompt dla stories (`content/services/ai_prompts.py`)**
- `build_story_image_prompt(visual_hint: str) -> str` — `visual_hint` + sufiks brandowy **pionowy**: „Vertical 9:16, 1080x1920, photorealistic, no text overlay, kompozycja zostawiająca miejsce na tekst u dołu kadru" + ten sam klimat marki co posty.

**6. Preview (`content/templates/admin/content/weeklyresearch/_preview.html`)**
- Zakładka Stories: dla każdego slajdu pokaż `headline`+`subtext`, AI-prompt z przyciskiem Kopiuj, miniaturę wgranego zdjęcia / złożonego PNG (jeśli istnieje), link „edytuj / wgraj zdjęcie" do `StorySlideAdmin`.

**7. CLI (`generate_story_images.py`)**
- Przestawienie renderu na wiersze `StorySlide` danego `--week` (zamiast surowego JSON). Zachować `--force`. Ścieżka wyjściowa PNG bez zmian: `MEDIA/weekly_research/<week>/stories/<NN>_<slide_type>.png`.

## Przepływ danych

`WeeklyResearch.formatted_json` → (promote) → `StorySlide` rows → operator edytuje/wgrywa/kopiuje → (render) → PNG w `MEDIA_ROOT/weekly_research/<week>/stories/`. Zdjęcia wgrane: `MEDIA_ROOT/weekly_research/story_uploads/<rok>/<mc>/`.

## Dane wsteczne

Istniejące `formatted_json` mają stary schemat (`text`, `emoji`, bez `headline`/`subtext`/`visual_hint`). Akcja promote działa wstecz (fallback `text`→`headline`). Pełny nowy materiał dla starego tygodnia: `run_weekly_research --retry-format --force` (regeneruje JSON nowym promptem). Bez migracji danych w bazie — JSON to blob, nowe pola dochodzą naturalnie.

## Obsługa błędów / edge cases

- Brak zdjęcia → fallback render (bez wyjątku).
- Uszkodzony/nietypowy upload → walidacja `ImageField` + Pillow; błąd renderu izolowany per slajd (reszta się generuje), komunikat w adminie.
- `visual_hint` puste → AI-prompt = sam sufiks brandowy (albo komunikat „uzupełnij visual_hint").
- `headline`/`subtext` za długie → render robi wrap; twarde limity walidowane na modelu (`max_length`) i/lub przycinane przy promote.
- Bardzo długi subtext mimo limitu → wrap + ewentualne przycięcie linii, żeby nie wyjść poza kadr.

## Testy / weryfikacja

- `manage.py check` + `makemigrations --check` (migracja obecna).
- Render smoke test: (1) kompozycja z przykładowym zdjęciem, (2) fallback bez zdjęcia — oba zwracają poprawny PNG 1080×1920.
- `promote_to_story_slides`: idempotencja + fallback `text`→`headline` na starym JSON.
- `build_story_image_prompt`: zawiera `visual_hint` i pionowy sufiks.

## Poza zakresem (YAGNI)

- Integracja z API generującym obrazy (DALL·E/Imagen) — świadomie nie, tylko gotowy prompt do skopiowania.
- Auto-publikacja na Instagramie.
- Animacje / wideo stories.
- Edytor wizualny pozycji tekstu — layout A jest stały.
