---
phase: quick-260609-ikz
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - content/services/story_renderer.py
  - content/admin.py
  - content/management/commands/generate_story_images.py
autonomous: true
requirements: [QUICK-260609-IKZ]
must_haves:
  truths:
    - "Fallback slides (no background_image) center the eyebrow+headline+subtext block vertically on the 1080x1920 canvas"
    - "Layout A (photo present) keeps the text block bottom-anchored over the gradient scrim, lifted enough to leave room for the wordmark"
    - "Every slide shows a dimmed letter-spaced wordmark 'KUCHENNA KOMITYWA' near the bottom-center"
    - "When index and total are provided, a centered row of progress dots renders near the top with the current dot filled and others dimmed"
    - "When index or total is None the renderer draws NO dots and never raises (old call sites keep working)"
    - "render() and render_to_file() still accept BOTH a dict and a StorySlide instance, and the PNG output path is unchanged"
  artifacts:
    - path: "content/services/story_renderer.py"
      provides: "render(self, slide, index=None, total=None) + render_to_file(self, slide, path, index=None, total=None); vertical-center fallback text; wordmark; progress dots"
      contains: "def render(self, slide, index=None, total=None)"
    - path: "content/admin.py"
      provides: "StorySlideAdmin 'Generuj PNG' action passes index/total via enumerate(start=1)"
      contains: "render_to_file"
    - path: "content/management/commands/generate_story_images.py"
      provides: "CLI loop passes index/total via enumerate(start=1)"
      contains: "render_to_file"
  key_links:
    - from: "content/admin.py generate_story_slide_pngs"
      to: "StoryRenderer.render_to_file"
      via: "render_to_file(slide, path, index=i, total=total)"
      pattern: "render_to_file\\([^)]*index="
    - from: "content/management/commands/generate_story_images.py handle"
      to: "StoryRenderer.render_to_file"
      via: "render_to_file(slide, path, index=i, total=total)"
      pattern: "render_to_file\\([^)]*index="
---

<objective>
Podrasowanie wizualne IG stories (pakiet 1+2+3): trzy zmiany w rendererze plus przekazanie index/total z dwoch wywolan.

1. Balans fallbacku: blok tekstu wysrodkowany w pionie gdy slajd nie ma zdjecia; przy zdjeciu (layout A) pozostaje bottom-anchor.
2. Wordmark marki: maly, letter-spaced, przyciemniony znak "KUCHENNA KOMITYWA" na dole-srodku na kazdym slajdzie.
3. Progress dots: rzad kropek u gory-srodku — kropka biezacego slajdu jasna, reszta przyciemniona; rysowany tylko gdy podano index i total.

Purpose: czytelniejsze, bardziej "markowe" slajdy stories i orientacja w sekwencji (kropki).
Output: zaktualizowany renderer + dwa wywolania przekazujace index/total. Bez zmian w modelu/migracjach/prompcie/sciezkach PNG.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md

<interfaces>
<!-- Aktualne kontrakty (z codebase). Executor uzywa ich bezposrednio. -->

content/services/story_renderer.py — StoryRenderer (kluczowe stale i metody):
```python
CANVAS_SIZE = (1080, 1920)
MARGIN_X = 80
BOTTOM_MARGIN = 120          # dolny margines bloku tekstu
EYEBROW_SIZE = 40
HEADLINE_SIZE = 76
SUBTEXT_SIZE = 46
EYEBROW_GAP = 28
HEADLINE_LINE_GAP = 12
BLOCK_GAP = 24
SUBTEXT_LINE_GAP = 8
SCRIM_HEIGHT_RATIO = 0.45
SCRIM_MAX_ALPHA = 217
self._font_eyebrow   # NotoSans-Regular @ EYEBROW_SIZE
self._font_headline  # NotoSans-Bold @ HEADLINE_SIZE
self._font_subtext   # NotoSans-Regular @ SUBTEXT_SIZE

@staticmethod
def _parse_hex(color: str, default="#f3ead7") -> tuple   # -> (r,g,b)
def _line_height(self, draw, font) -> int
def _draw_text_block(self, draw, eyebrow, headline_lines, subtext_lines,
                     eyebrow_color, text_color) -> None   # liczy total_h, y = canvas_h - BOTTOM_MARGIN - total_h
def render(self, slide) -> bytes
def render_to_file(self, slide, path) -> Path
```

content/services/colors.py:
```python
def text_color_for_bg(value: str) -> str   # hex tekstu czytelnego na danym tle; default "#2a2420"
```

Wywolanie w admin (StorySlideAdmin "Generuj PNG", content/admin.py ~L210):
```python
@admin.action(description="Generuj PNG (1080x1920)")
def generate_story_slide_pngs(modeladmin, request, queryset):
    renderer = StoryRenderer()
    for slide in queryset:
        ...
        renderer.render_to_file(slide, path)
```

Wywolanie w CLI (content/management/commands/generate_story_images.py ~L60-92):
```python
slides = list(wr.story_slides.all())
...
for slide in slides:
    ...
    renderer.render_to_file(slide, path)
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Renderer — vertical-center fallback, wordmark, progress dots, index/total sygnatura</name>
  <files>content/services/story_renderer.py</files>
  <action>
Wszystkie zmiany w StoryRenderer. Double quotes, 4 spacje. Bez emoji.

A) STALE — dodaj do klasy (obok istniejacych):
   - WORDMARK_TEXT = "KUCHENNA KOMITYWA"
   - WORDMARK_SIZE = 26
   - WORDMARK_Y = 1830
   - WORDMARK_BLEND = 0.55   # ile koloru tekstu vs tla (przyciemnienie ku tlu, mocniej niz eyebrow ~0.7)
   - DOTS_Y = 64
   - DOT_RADIUS = 7          # srednica ~14px
   - DOT_GAP = 16
   - DOT_DIM_ALPHA = 0.4     # przyciemnienie nieaktywnych kropek (blend ku tlu)
   - LAYOUT_A_BOTTOM_MARGIN = 240   # bottom-anchor w layout A podniesiony (zostawia ~110-130px na wordmark ponizej bloku)
   Zaladuj wordmark font w __init__: self._font_wordmark = ImageFont.truetype(str(self.FONT_PATH_REGULAR), self.WORDMARK_SIZE)

B) _draw_text_block — rozgalez pozycjonowanie pionowe.
   Dodaj parametr `vertical_center: bool = False` ORAZ pozwol nadpisac dolny margines: dodaj parametr `bottom_margin=None`.
   Po obliczeniu total_h (logika bez zmian):
     - if vertical_center: y = (canvas_h - total_h) // 2
     - else: bm = bottom_margin if bottom_margin is not None else self.BOTTOM_MARGIN; y = canvas_h - bm - total_h
   Reszta rysowania bloku bez zmian.

C) Nowa metoda _blend(self, fg_rgb, bg_rgb, weight) -> tuple:
   zwraca per-kanal int(fg*weight + bg*(1-weight)). Uzyj do wordmark i dimmed dots (jeden helper, DRY — istniejacy eyebrow blend mozna zostawic inline; nie wymagane przepisywac).

D) Nowa metoda _draw_wordmark(self, draw, color_rgb, bg_rgb):
   canvas_w, canvas_h = self.CANVAS_SIZE
   spaced = " ".join(list(self.WORDMARK_TEXT))  # letter-spaced jak eyebrow
   blended = self._blend(color_rgb, bg_rgb, self.WORDMARK_BLEND)
   bbox = draw.textbbox((0, 0), spaced, font=self._font_wordmark)
   lw = bbox[2] - bbox[0]
   x = (canvas_w - lw) // 2
   y = self.WORDMARK_Y
   draw.text((x, y), spaced, font=self._font_wordmark, fill=blended)

E) Nowa metoda _draw_progress_dots(self, draw, index, total, active_rgb, bg_rgb):
   Rysuj TYLKO gdy: total is not None and index is not None and total >= 1 and 1 <= index <= total. W przeciwnym razie return bez rysowania.
   canvas_w, canvas_h = self.CANVAS_SIZE
   dim_rgb = self._blend(active_rgb, bg_rgb, self.DOT_DIM_ALPHA)
   r = self.DOT_RADIUS; gap = self.DOT_GAP
   row_w = total * (2 * r) + (total - 1) * gap
   x0 = (canvas_w - row_w) // 2
   cy = self.DOTS_Y
   for i in range(total):  # i 0-based; aktywny gdy i == index-1
       cx = x0 + i * (2 * r + gap) + r
       fill = active_rgb if (i == index - 1) else dim_rgb
       draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill)
   (active_rgb = kolor tekstu danego layoutu; w layout A bialy, w fallbacku text_color_for_bg.)

F) render — nowa sygnatura: def render(self, slide, index=None, total=None) -> bytes
   Zachowaj normalize/wrap/bg_image bez zmian. Po zbudowaniu obrazu i draw, w KAZDEJ galezi:
   - Layout A (zdjecie):
       text_color = (255, 255, 255); eyebrow_color = (230, 230, 230)
       _draw_text_block(..., vertical_center=False, bottom_margin=self.LAYOUT_A_BOTTOM_MARGIN)  # podniesiony bottom-anchor
       _draw_wordmark(draw, (255, 255, 255), (20, 16, 12))   # wordmark na ciemnym scrim u dolu — blend ku ciemnemu
       _draw_progress_dots(draw, index, total, (255, 255, 255), (0, 0, 0))  # dim ku czerni u gory
   - Fallback (brak zdjecia):
       bg_rgb = _parse_hex(bg_color)
       text_rgb = _parse_hex(text_color_for_bg(bg_color), default="#2a2420")
       eyebrow_rgb jak teraz (blend 0.7, inline bez zmian)
       _draw_text_block(..., vertical_center=True)   # PIONOWE centrowanie, bez bottom_margin
       _draw_wordmark(draw, text_rgb, bg_rgb)
       _draw_progress_dots(draw, index, total, text_rgb, bg_rgb)
   Zapis PNG (optimize=True) bez zmian; zwroc bytes.
   WAZNE: kolejnosc rysowania — text block, potem wordmark, potem dots (dots u gory, wordmark u dolu; brak kolizji). W layout A scrim juz zlozony przed draw — bez zmian.

G) render_to_file — nowa sygnatura: def render_to_file(self, slide, path, index=None, total=None) -> Path
   przekaz: path.write_bytes(self.render(slide, index=index, total=total))
   reszta (mkdir) bez zmian.

ZACHOWAC: layout A cover-crop + scrim, fallback kolor marki, render przyjmuje dict ORAZ obiekt StorySlide (normalize bez zmian), sciezka PNG bez zmian, brak emoji.
  </action>
  <verify>
<automated>cd /home/tomo/workspace/komitywa && set -a && [ -f .env ] && . ./.env; set +a; .venv/bin/python manage.py check 2>&1 | tail -5 && .venv/bin/python -c "
import os, django, tempfile
from io import BytesIO
from PIL import Image
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()
from content.services.story_renderer import StoryRenderer
photo = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
Image.new('RGB', (800, 1000), (120, 90, 60)).save(photo.name, 'JPEG')
r = StoryRenderer()
a = r.render({'headline': 'Test naglowek dluzszy tekst', 'subtext': 'Podtekst opisowy ze zdjeciem.', 'slide_type': 'tip', 'background_image': photo.name}, index=1, total=7)
assert Image.open(BytesIO(a)).size == (1080, 1920)
b = r.render({'headline': 'Fallback naglowek', 'subtext': 'Podtekst w fallbacku, wysrodkowany.', 'slide_type': 'fact', 'bg_color': '#6b7a3a'}, index=3, total=7)
assert Image.open(BytesIO(b)).size == (1080, 1920)
c = r.render({'headline': 'Bez kropek', 'subtext': 'Stare wywolanie.', 'slide_type': 'hook', 'bg_color': '#f3ead7'})
assert Image.open(BytesIO(c)).size == (1080, 1920)
out = tempfile.NamedTemporaryFile(suffix='.png', delete=False).name
p = r.render_to_file({'headline': 'Plik', 'subtext': 'do pliku', 'slide_type': 'cta', 'bg_color': '#b6562e'}, out, index=2, total=5)
assert os.path.getsize(str(p)) > 0
print('SMOKE OK')
"</automated>
  </verify>
  <done>
manage.py check przechodzi (0 issues). Smoke wypisuje "SMOKE OK": (a) zdjecie+index/total -> PNG (1080,1920); (b) fallback+index=3/total=7 -> PNG (1080,1920); (c) bez index/total -> PNG bez wyjatku; (d) render_to_file z index/total zapisuje niepusty PNG. render nadal przyjmuje dict (i obiekt — normalize niezmieniony).
  </done>
</task>

<task type="auto">
  <name>Task 2: Wywolania — przekaz index/total z admin akcji i CLI</name>
  <files>content/admin.py, content/management/commands/generate_story_images.py</files>
  <action>
Przekaz index (1-based) i total do render_to_file. Double quotes, 4 spacje. Bez innych zmian logiki/sciezek.

A) content/admin.py — generate_story_slide_pngs (StorySlideAdmin "Generuj PNG", ~L210):
   - total = queryset.count()
   - petla: for i, slide in enumerate(queryset, start=1):
       (zachowaj istniejaca logike slide_type/path/try/except/liczniki)
       wywolaj: renderer.render_to_file(slide, path, index=i, total=total)

B) content/management/commands/generate_story_images.py — handle (~L60-92):
   - slides = list(wr.story_slides.all()) jest juz zmaterializowana -> total = len(slides)
   - petla: for i, slide in enumerate(slides, start=1):
       (zachowaj logike filename/skip/force; skip przy istniejacym pliku PRZED renderem jak teraz — index/total przekazujemy tylko do render_to_file gdy faktycznie renderujemy)
       wywolaj: renderer.render_to_file(slide, path, index=i, total=total)

NIE zmieniaj generate_story_images_action (dict-based, formatted_json) — poza zakresem; jego render_to_file dziala dalej (index/total domyslnie None -> brak dots).
  </action>
  <verify>
<automated>cd /home/tomo/workspace/komitywa && set -a && [ -f .env ] && . ./.env; set +a; .venv/bin/python manage.py check 2>&1 | tail -3 && grep -nE "render_to_file\([^)]*index=" content/admin.py content/management/commands/generate_story_images.py && grep -nE "enumerate\([^)]*start=1" content/admin.py content/management/commands/generate_story_images.py</automated>
  </verify>
  <done>
manage.py check przechodzi. grep potwierdza: render_to_file(..., index=i, total=total) w content/admin.py (generate_story_slide_pngs) ORAZ w generate_story_images.py (handle); oba uzywaja enumerate(..., start=1). generate_story_images_action niezmieniona.
  </done>
</task>

</tasks>

<verification>
- `.venv/bin/python manage.py check` -> 0 issues (oba zadania).
- Renderer smoke (Task 1): render zwraca PNG (1080,1920) dla: zdjecie+index/total, fallback+index/total, brak index/total (bez wyjatku, bez dots); render_to_file z index/total zapisuje niepusty plik.
- Wywolania (Task 2): grep potwierdza przekazanie index/total i enumerate(start=1) w obu plikach.
- Wizual (orchestrator obejrzy po wykonaniu, nie assertowalne automatycznie): fallback wysrodkowany pionowo; layout A bottom-anchor podniesiony z miejscem na wordmark; wordmark "KUCHENNA KOMITYWA" przyciemniony u dolu; rzad kropek u gory z jasna biezaca kropka.
</verification>

<success_criteria>
- render(self, slide, index=None, total=None) i render_to_file(self, slide, path, index=None, total=None) — nowe sygnatury; stare wywolania (bez index/total) dzialaja, NIE rysuja kropek.
- Fallback (brak zdjecia): blok tekstu wysrodkowany w pionie kanwy.
- Layout A (zdjecie): blok tekstu bottom-anchor podniesiony (LAYOUT_A_BOTTOM_MARGIN), miejsce na wordmark.
- Wordmark "KUCHENNA KOMITYWA" letter-spaced, przyciemniony, dol-srodek na kazdym slajdzie (bialy w layout A, text_color_for_bg blended w fallbacku).
- Progress dots: rzad u gory-srodku, biezaca kropka jasna, reszta przyciemniona; tylko gdy total>=1 i 1<=index<=total.
- StorySlideAdmin "Generuj PNG" i CLI przekazuja index (enumerate start=1) + total.
- Zachowane: cover-crop+scrim, fallback kolor marki, dict ORAZ obiekt, sciezki PNG, brak emoji, double quotes, 4 spacje. Bez zmian modelu/migracji/promptu.
</success_criteria>

<output>
After completion, create `.planning/quick/260609-ikz-podrasowanie-wizualne-stories-balans-fal/260609-ikz-SUMMARY.md`
</output>
