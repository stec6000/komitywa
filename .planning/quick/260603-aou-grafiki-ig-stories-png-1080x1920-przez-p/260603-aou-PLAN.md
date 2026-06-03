---
phase: quick-260603-aou
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - content/services/__init__.py
  - content/services/colors.py
  - content/services/story_renderer.py
  - content/services/ai_prompts.py
  - content/templatetags/content_extras.py
  - content/fonts/NotoSans-Regular.ttf
  - content/fonts/NotoSans-Bold.ttf
  - content/fonts/NotoColorEmoji.ttf
  - content/management/__init__.py
  - content/management/commands/__init__.py
  - content/management/commands/generate_story_images.py
  - content/admin.py
  - content/views.py
  - content/urls.py
  - content/templates/admin/content/weeklyresearch/_preview.html
  - content/static/content/admin/weekly_research_preview.css
  - content/README.md
autonomous: true
requirements:
  - QUICK-260603-aou
must_haves:
  truths:
    - "Staff może w admin list view zaznaczyć WR i odpalić akcję 'Generuj grafiki stories' — PNG-i 1080x1920 powstają w MEDIA_ROOT/weekly_research/<week_label>/stories/"
    - "Staff widzi w admin change view (tab IG Stories) miniatury wygenerowanych PNG-ów oraz link 'Pobierz wszystkie jako ZIP'"
    - "ZIP endpoint zwraca .zip ze wszystkimi PNG-ami stories dla danego WR; nieautoryzowany użytkownik dostaje 403"
    - "Staff widzi w admin change view (tab IG Posty) pod każdym postem prompt AI (visual_hint + brand suffix) z przyciskiem 'Skopiuj prompt do AI'"
    - "Management command 'generate_story_images --latest' generuje grafiki dla ostatniego formatted WR"
    - "Helper text_color_for_bg ma jedno źródło prawdy w content/services/colors.py; template filter content_extras.text_color_for_bg i StoryRenderer używają tej samej funkcji"
    - "Brand prompt suffix istnieje jako jedna stała Pythonowa (services/ai_prompts.py) i jest wstrzykiwana do template przez context — nie duplikowana"
    - "Strona produkcyjna ma deployed kod (Pillow + fonty loadable, manage.py check zielony, GET /admin/login/ -> 200)"
  artifacts:
    - path: "content/services/colors.py"
      provides: "text_color_for_bg single source of truth (hardcoded brand palette)"
      contains: "def text_color_for_bg"
    - path: "content/services/story_renderer.py"
      provides: "StoryRenderer class with render() and render_to_file()"
      contains: "class StoryRenderer"
    - path: "content/services/ai_prompts.py"
      provides: "Brand AI image prompt suffix constant + builder"
      contains: "AI_IMAGE_BRAND_SUFFIX"
    - path: "content/management/commands/generate_story_images.py"
      provides: "CLI command to generate stories PNGs"
      contains: "class Command"
    - path: "content/fonts/NotoSans-Regular.ttf"
      provides: "Regular font for PNG rendering"
    - path: "content/fonts/NotoSans-Bold.ttf"
      provides: "Bold font for PNG rendering"
  key_links:
    - from: "content/admin.py WeeklyResearchAdmin"
      to: "content/services/story_renderer.py StoryRenderer"
      via: "actions = [..., generate_story_images_action]"
      pattern: "StoryRenderer\\(\\)\\.render_to_file"
    - from: "content/admin.py WeeklyResearchAdmin.change_view"
      to: "_preview.html template context"
      via: "extra_context['stories_files'] + extra_context['stories_zip_url'] + extra_context['ai_image_brand_suffix']"
      pattern: "extra_context\\["
    - from: "content/views.py WeeklyResearchStoriesZipView"
      to: "content/urls.py + backend/urls.py include('content.urls', namespace='content')"
      via: "name='weeklyresearch_stories_zip' (rozwiązuje pod /blog/admin/content/weeklyresearch/<pk>/stories.zip)"
      pattern: "weeklyresearch_stories_zip"
    - from: "content/templatetags/content_extras.py text_color_for_bg filter"
      to: "content/services/colors.py text_color_for_bg"
      via: "from content.services.colors import text_color_for_bg"
      pattern: "from content\\.services\\.colors import"
---

<objective>
Programowe generowanie grafik IG Stories (PNG 1080x1920) z formatted_json["instagram_stories"] przy uzyciu Pillow,
plus AI image prompt generator do postow (visual_hint + brand styling) embed w admin preview do skopiowania.

Purpose:
- Skrocic workflow publikacji: po `run_weekly_research` admin dostaje gotowe PNG-i do uploadu na IG Stories.
- Dostarczyc copy-paste prompty AI do postow z trzymanym brand stylem (Bialystok, weganska piekarnia,
  rzemieslnicza fotografia).

Output:
- PNG-i 1080x1920 w MEDIA_ROOT/weekly_research/<week_label>/stories/01_hook.png itd.
- ZIP download endpoint w adminie (staff-only).
- Admin tab "IG Stories": miniatury rzeczywistych PNG-ow + link ZIP (jesli wygenerowane); CSS placeholder
  jako fallback gdy plikow nie ma.
- Admin tab "IG Posty": pod kazdym postem dodatkowo prompt AI z brand suffix + Copy button.
- Management command `generate_story_images --week <label>|--latest [--force]`.
- Bundled fonty w content/fonts/.
- README content/ zaktualizowany.

Constraints (z planning_context):
- Pillow juz w requirements.txt — NIE duplikowac
- Fonty w repo (sumie <15MB), NIE w .gitignore
- ZIP staff-only
- Brand suffix jedno zrodlo prawdy (services/ai_prompts.py)
- Nie odpalac AI image API, nie odpalac run_weekly_research
- Smoke prod sprawdza Pillow + fonty + login URL HTTP 200; NIE odpala akcji generate na prod
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@.planning/STATE.md
@content/models.py
@content/admin.py
@content/views.py
@content/urls.py
@content/templates/admin/content/weeklyresearch/_preview.html
@content/templates/admin/content/weeklyresearch/change_form.html
@content/templatetags/content_extras.py
@content/static/content/admin/weekly_research_preview.css
@content/static/content/admin/weekly_research_preview.js
@content/README.md
@content/management/commands/run_weekly_research.py
@backend/settings.py
@backend/urls.py
@requirements.txt

<interfaces>
<!-- Slide shape (z formatted_json["instagram_stories"][i], potwierdzone w _preview.html): -->
```python
slide = {
    "slide_type": "hook" | "stat" | "tip" | "cta" | str,
    "emoji": "🌱",                  # 1-3 znaki unicode, moze byc pusty
    "text": "Krotki tekst",          # main copy, ~80 znakow
    "bg_color": "#f3ead7",           # hex z '#' (brand palette)
}
```

<!-- WeeklyResearch (content/models.py): -->
```python
class WeeklyResearch(models.Model):
    week_label: CharField      # np. "2026-W23"
    status: CharField          # "pending" | "research_done" | "formatted" | "failed"
    date_to: DateField
    formatted_json: JSONField  # ma "instagram_stories": [...], "instagram_posts": [...], "blog": {...}
```

<!-- Istniejacy admin (content/admin.py linia 56-64): -->
```python
@admin.register(WeeklyResearch)
class WeeklyResearchAdmin(admin.ModelAdmin):
    change_form_template = "admin/content/weeklyresearch/change_form.html"
    list_display = ("week_label", "date_from", "date_to", "status", "created_at")
    actions = [promote_to_blogpost]   # <-- dopisac generate_story_images_action
```
Uwaga: ADMIN NIE MA jeszcze override `change_view`. Trzeba dodac nowy override.
`change_form.html` extends "admin/change_form.html" i w `after_field_sets` includuje `_preview.html`
z `data=original.formatted_json`. Aby przeniesc `stories_files` / `stories_zip_url` /
`ai_image_brand_suffix` do _preview.html, musimy dolozyc je do extra_context i przekazac
do include w change_form.html (lub w _preview.html odczytac z root context).

<!-- Istniejacy template filter (content/templatetags/content_extras.py): -->
```python
# Hardcoded mapping brand palette -> text color:
_BRAND_TEXT_COLOR_MAP = {
    "#2a2420": "#f3ead7",  # ink -> paper
    "#6b7a3a": "#f3ead7",  # olive -> paper
    "#b6562e": "#f3ead7",  # terracotta -> paper
    "#c89a3a": "#2a2420",  # mustard -> ink
    "#f3ead7": "#2a2420",  # paper -> ink
}
_DEFAULT_TEXT_COLOR = "#2a2420"
```
**To NIE jest algorytm luminancji.** Przenosimy mapping 1:1 do services/colors.py.

<!-- content/urls.py JUZ ma app_name = "content" + 2 patterny (blog_list, blog_detail). -->
<!-- backend/urls.py JUZ ma path("blog/", include("content.urls", namespace="content")) -->
<!-- => ZIP URL bedzie pod /blog/admin/content/weeklyresearch/<pk>/stories.zip — funkcjonalnie OK, -->
<!--    reverse('content:weeklyresearch_stories_zip', kwargs={'pk':X}) dziala. -->

<!-- Istniejacy JS handler (weekly_research_preview.js) — dziala dla wszystkich data-copy-text, -->
<!-- nie wymaga modyfikacji. -->

<!-- Brand palette: -->
<!-- tla:   #f3ead7, #ebe0c5, #d9c9a3 -->
<!-- tekst: #2a2420, #5a4a3a -->
<!-- akcenty: #6b7a3a (oliwka/ziola), #b6562e (terakota), #c89a3a (musztarda) -->

<!-- MEDIA_ROOT = BASE_DIR / "public" / "media" (backend/settings.py linia 204) -->
<!-- MEDIA_URL  = "/media/" -->
</interfaces>

<inputs>
- Working directory: /home/tomo/workspace/komitywa
- Python 3.12 (z __pycache__/__init__.cpython-312.pyc w content/management)
- Django 5.2.x, Pillow juz w requirements.txt
- MEDIA_ROOT: BASE_DIR / "public" / "media"
- SSH deploy: panel84.mydevil.net, user jem3pizze, haslo "Tak12toto." (z kropka)
- Systemowy python3 ma paramiko
- Server path: /usr/home/jem3pizze/domains/kuchennakomitywa.pl/public_python
- Server venv: /usr/home/jem3pizze/.virtualenvs/komitywa/bin/python
</inputs>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Wyodrebnij text_color_for_bg do content/services/colors.py</name>
  <files>
    content/services/__init__.py,
    content/services/colors.py,
    content/templatetags/content_extras.py
  </files>
  <action>
    1. Stworz `content/services/__init__.py`:
       ```python
       """Service layer for content app."""
       ```

    2. Stworz `content/services/colors.py` — przenies hardcoded mapping 1:1:
       ```python
       """Brand palette helpers (single source of truth)."""

       # Hardcoded mapping for brand palette colors.
       # Returns the text color that should be used on top of the given background.
       BRAND_TEXT_COLOR_MAP = {
           "#2a2420": "#f3ead7",  # ink -> paper
           "#6b7a3a": "#f3ead7",  # olive -> paper
           "#b6562e": "#f3ead7",  # terracotta -> paper
           "#c89a3a": "#2a2420",  # mustard -> ink
           "#f3ead7": "#2a2420",  # paper -> ink
       }

       DEFAULT_TEXT_COLOR = "#2a2420"


       def text_color_for_bg(value: str) -> str:
           """Return readable text color for a given background hex.

           Case-insensitive. Tolerates hex without leading '#'.
           Unknown colors default to ink (#2a2420).
           """
           if not value:
               return DEFAULT_TEXT_COLOR
           key = str(value).strip().lower()
           if not key.startswith("#"):
               key = "#" + key
           return BRAND_TEXT_COLOR_MAP.get(key, DEFAULT_TEXT_COLOR)
       ```
       UWAGA: dodatkowo akceptujemy hex bez `#` (StoryRenderer moze tak podac), oryginalna funkcja
       w content_extras NIE tolerowala tego — ale tu rozszerzamy, NIE zmieniamy zachowania dla
       zgodnego inputu.

    3. Zmodyfikuj `content/templatetags/content_extras.py` — delegacja do services:
       ```python
       from django import template

       from content.services.colors import text_color_for_bg as _text_color_for_bg

       register = template.Library()


       @register.filter
       def text_color_for_bg(value):
           """Return readable text color for a given background hex (delegate to services.colors)."""
           return _text_color_for_bg(value)
       ```

    4. Backward-compat sanity: import `from content.templatetags.content_extras import text_color_for_bg`
       dalej musi dzialac (funkcja jest re-exported na module level).
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; python -c "
from content.services.colors import text_color_for_bg, BRAND_TEXT_COLOR_MAP
assert text_color_for_bg('#f3ead7') == '#2a2420'
assert text_color_for_bg('#2a2420') == '#f3ead7'
assert text_color_for_bg('#6b7a3a') == '#f3ead7'
assert text_color_for_bg('#c89a3a') == '#2a2420'
assert text_color_for_bg('f3ead7') == '#2a2420', 'no-hash tolerance broken'
assert text_color_for_bg('') == '#2a2420'
assert text_color_for_bg(None) == '#2a2420'
assert text_color_for_bg('#deadbe') == '#2a2420', 'unknown should default to ink'
print('services.colors OK')
" &amp;&amp; python -c "
from content.templatetags.content_extras import text_color_for_bg
assert text_color_for_bg('#f3ead7') == '#2a2420'
assert text_color_for_bg('#000000') == '#2a2420'
print('templatetag delegate OK')
" &amp;&amp; python manage.py check 2&gt;&amp;1 | tail -2</automated>
  </verify>
  <done>
    - content/services/__init__.py i content/services/colors.py istnieja
    - text_color_for_bg w services zwraca te same wartosci co stara wersja dla #f3ead7, #2a2420,
      #6b7a3a, #b6562e, #c89a3a + default #2a2420 dla nieznanych
    - tolerancja hex bez '#'
    - templatetag deleguje do services.colors
    - python manage.py check 0 issues
  </done>
</task>

<task type="auto">
  <name>Task 2: Pobierz fonty Noto Sans (Regular/Bold) do content/fonts/</name>
  <files>
    content/fonts/NotoSans-Regular.ttf,
    content/fonts/NotoSans-Bold.ttf,
    content/fonts/NotoColorEmoji.ttf,
    .gitignore
  </files>
  <action>
    1. Stworz katalog `content/fonts/` jesli nie istnieje:
       ```bash
       mkdir -p content/fonts
       ```

    2. Pobierz fonty (try-list URLs, pierwszy ktory dziala):
       - **NotoSans-Regular.ttf**:
         ```bash
         curl -fL --retry 3 -o content/fonts/NotoSans-Regular.ttf \
           "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf"
         ```
       - **NotoSans-Bold.ttf**:
         ```bash
         curl -fL --retry 3 -o content/fonts/NotoSans-Bold.ttf \
           "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Bold.ttf"
         ```
       - **NotoColorEmoji.ttf** (opcjonalny, prob):
         ```bash
         curl -fL --retry 3 -o content/fonts/NotoColorEmoji.ttf \
           "https://github.com/googlefonts/noto-emoji/raw/main/fonts/NotoColorEmoji.ttf" || true
         ```

    3. Sprawdz rozmiary:
       ```bash
       ls -la content/fonts/
       du -sh content/fonts/
       ```

    4. **Logika gatingu emoji fontu:**
       - Jesli `NotoColorEmoji.ttf` istnieje i ma > 12 MiB (12*1024*1024 = 12582912 bajtow) → `rm content/fonts/NotoColorEmoji.ttf`
       - Jesli plik nie istnieje (curl fail) → odnotuj w summary "Emoji font niedostepny — fallback do tekstu w NotoSans-Bold"
       - Jesli istnieje i miesci sie w budgecie — zostaw.

    5. **Aktualizacja .gitignore:**
       - Obecny .gitignore NIE ma `*.ttf` ani `content/fonts/` w wykluczeniach, wiec fonty automatycznie sa trackowane.
       - **Walidacja:** `git check-ignore -v content/fonts/NotoSans-Regular.ttf` powinno zwrocic exit code != 0 (nie jest ignorowane).
       - Jesli z jakichkolwiek powodow byloby ignorowane: dodaj `!content/fonts/*.ttf` na koncu .gitignore.

    6. **Verify fonty loadable przez PIL:**
       ```bash
       python -c "
       from PIL import ImageFont
       ImageFont.truetype('content/fonts/NotoSans-Regular.ttf', 80)
       ImageFont.truetype('content/fonts/NotoSans-Bold.ttf', 80)
       print('NotoSans fonts loadable')
       "
       ```

    7. **Final size check** (suma < 15 MiB):
       ```bash
       python -c "
       import os
       total = sum(os.path.getsize(f'content/fonts/{f}') for f in os.listdir('content/fonts') if f.endswith('.ttf'))
       print(f'total: {total} bytes ({total/1024/1024:.1f} MiB)')
       assert total &lt; 15*1024*1024, 'total fonts > 15MB'
       "
       ```
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; ls -la content/fonts/ &amp;&amp; python -c "
import os
assert os.path.exists('content/fonts/NotoSans-Regular.ttf'), 'Regular missing'
assert os.path.exists('content/fonts/NotoSans-Bold.ttf'), 'Bold missing'
assert os.path.getsize('content/fonts/NotoSans-Regular.ttf') &gt; 100_000, 'Regular too small'
assert os.path.getsize('content/fonts/NotoSans-Bold.ttf') &gt; 100_000, 'Bold too small'
total = sum(os.path.getsize(f'content/fonts/{f}') for f in os.listdir('content/fonts') if f.endswith('.ttf'))
assert total &lt; 15*1024*1024, f'total {total} &gt; 15MB'
print(f'sizes OK, total {total/1024/1024:.1f} MiB')
" &amp;&amp; python -c "from PIL import ImageFont; ImageFont.truetype('content/fonts/NotoSans-Regular.ttf', 80); ImageFont.truetype('content/fonts/NotoSans-Bold.ttf', 80); print('PIL load OK')" &amp;&amp; (git check-ignore -v content/fonts/NotoSans-Regular.ttf; echo "exit=$?") | tail -1</automated>
  </verify>
  <done>
    - content/fonts/NotoSans-Regular.ttf istnieje (>100KB)
    - content/fonts/NotoSans-Bold.ttf istnieje (>100KB)
    - NotoColorEmoji.ttf: jesli >12MiB lub fail download → usuniety/brak (i odnotowane w summary)
    - Suma rozmiarow plikow w content/fonts/ < 15 MiB
    - PIL.ImageFont.truetype laduje oba pliki bez bledu
    - git nie ignoruje plikow z content/fonts/
  </done>
</task>

<task type="auto">
  <name>Task 3: StoryRenderer + AI prompts builder</name>
  <files>
    content/services/story_renderer.py,
    content/services/ai_prompts.py
  </files>
  <action>
    1. Stworz `content/services/ai_prompts.py`:
       ```python
       """Brand-styled AI image prompts (single source of truth for visual_hint enrichment)."""

       AI_IMAGE_BRAND_SUFFIX = (
           "\n\n"
           "Styl: rzemieslnicza fotografia kulinarna, naturalne swiatlo, "
           "cieple tony, autentyczna kompozycja, klimat domowej weganskiej "
           "piekarni z Bialegostoku. Square 1:1, 1080x1080, photorealistic, "
           "no text overlay."
       )


       def build_ai_image_prompt(visual_hint: str) -> str:
           """Compose final AI prompt: visual_hint + brand suffix."""
           hint = (visual_hint or "").strip()
           return f"{hint}{AI_IMAGE_BRAND_SUFFIX}"
       ```

    2. Stworz `content/services/story_renderer.py`:
       ```python
       """PNG renderer for Instagram Stories (1080x1920) — uses bundled Noto Sans fonts."""

       from __future__ import annotations

       import textwrap
       from io import BytesIO
       from pathlib import Path
       from typing import Optional

       from PIL import Image, ImageDraw, ImageFont

       from content.services.colors import text_color_for_bg

       FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"


       class StoryRenderer:
           CANVAS_SIZE = (1080, 1920)
           FONT_PATH_REGULAR = FONTS_DIR / "NotoSans-Regular.ttf"
           FONT_PATH_BOLD = FONTS_DIR / "NotoSans-Bold.ttf"
           FONT_PATH_EMOJI = FONTS_DIR / "NotoColorEmoji.ttf"

           EMOJI_SIZE = 240
           EMOJI_Y = 320
           TEXT_SIZE = 80
           TEXT_Y_TOP = 720
           TEXT_LINE_HEIGHT = 100
           TEXT_MAX_CHARS_PER_LINE = 14
           LABEL_SIZE = 36
           LABEL_Y = 1760

           def __init__(self) -> None:
               if not self.FONT_PATH_REGULAR.exists() or not self.FONT_PATH_BOLD.exists():
                   raise RuntimeError(
                       f"Required fonts missing in {FONTS_DIR}: NotoSans-Regular.ttf and NotoSans-Bold.ttf"
                   )
               self._font_regular = ImageFont.truetype(str(self.FONT_PATH_REGULAR), self.LABEL_SIZE)
               self._font_bold = ImageFont.truetype(str(self.FONT_PATH_BOLD), self.TEXT_SIZE)
               self._font_emoji: Optional[ImageFont.FreeTypeFont] = None
               if self.FONT_PATH_EMOJI.exists():
                   try:
                       # NotoColorEmoji is a bitmap font with fixed size (typically 109).
                       self._font_emoji = ImageFont.truetype(str(self.FONT_PATH_EMOJI), 109)
                   except Exception:
                       self._font_emoji = None

           @staticmethod
           def _parse_hex(color: str, default: str = "#f3ead7") -> tuple:
               value = (color or default).strip().lstrip("#")
               if len(value) != 6:
                   value = default.lstrip("#")
               try:
                   return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))
               except ValueError:
                   value = default.lstrip("#")
                   return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))

           def render(self, slide: dict) -> bytes:
               bg_hex = slide.get("bg_color") or "#f3ead7"
               bg_rgb = self._parse_hex(bg_hex)
               text_color_hex = text_color_for_bg(bg_hex)
               text_rgb = self._parse_hex(text_color_hex, default="#2a2420")

               img = Image.new("RGB", self.CANVAS_SIZE, bg_rgb)
               draw = ImageDraw.Draw(img)
               canvas_w, _ = self.CANVAS_SIZE

               # ---- Emoji (top, centered) ----
               emoji = (slide.get("emoji") or "").strip()
               if emoji:
                   rendered = False
                   if self._font_emoji is not None:
                       try:
                           bbox = draw.textbbox((0, 0), emoji, font=self._font_emoji, embedded_color=True)
                           ew = bbox[2] - bbox[0]
                           draw.text(
                               ((canvas_w - ew) // 2, self.EMOJI_Y),
                               emoji,
                               font=self._font_emoji,
                               embedded_color=True,
                           )
                           rendered = True
                       except Exception:
                           rendered = False
                   if not rendered:
                       fallback_font = ImageFont.truetype(str(self.FONT_PATH_BOLD), self.EMOJI_SIZE)
                       bbox = draw.textbbox((0, 0), emoji, font=fallback_font)
                       ew = bbox[2] - bbox[0]
                       draw.text(
                           ((canvas_w - ew) // 2, self.EMOJI_Y),
                           emoji,
                           font=fallback_font,
                           fill=text_rgb,
                       )

               # ---- Main text (auto-wrap, centered) ----
               text = (slide.get("text") or "").strip()
               if text:
                   lines = textwrap.wrap(text, width=self.TEXT_MAX_CHARS_PER_LINE) or [text]
                   y = self.TEXT_Y_TOP
                   for line in lines:
                       bbox = draw.textbbox((0, 0), line, font=self._font_bold)
                       lw = bbox[2] - bbox[0]
                       draw.text(
                           ((canvas_w - lw) // 2, y),
                           line,
                           font=self._font_bold,
                           fill=text_rgb,
                       )
                       y += self.TEXT_LINE_HEIGHT

               # ---- Label (bottom, uppercase, letter-spaced, dimmed) ----
               label = (slide.get("slide_type") or "").upper()
               if label:
                   spaced = " ".join(list(label))
                   bbox = draw.textbbox((0, 0), spaced, font=self._font_regular)
                   lw = bbox[2] - bbox[0]
                   # simulate 70% opacity by blending text color toward bg
                   r = int(text_rgb[0] * 0.7 + bg_rgb[0] * 0.3)
                   g = int(text_rgb[1] * 0.7 + bg_rgb[1] * 0.3)
                   b = int(text_rgb[2] * 0.7 + bg_rgb[2] * 0.3)
                   draw.text(
                       ((canvas_w - lw) // 2, self.LABEL_Y),
                       spaced,
                       font=self._font_regular,
                       fill=(r, g, b),
                   )

               buf = BytesIO()
               img.save(buf, format="PNG", optimize=True)
               return buf.getvalue()

           def render_to_file(self, slide: dict, path) -> Path:
               path = Path(path)
               path.parent.mkdir(parents=True, exist_ok=True)
               path.write_bytes(self.render(slide))
               return path
       ```

    3. Smoke test inline (z weryfikatorem):
       ```bash
       python -c "
       from content.services.story_renderer import StoryRenderer
       r = StoryRenderer()
       data = r.render({'slide_type':'hook','emoji':'🌱','text':'Test slajdu','bg_color':'#f3ead7'})
       assert data[:8] == b'\\x89PNG\\r\\n\\x1a\\n', 'not PNG'
       assert len(data) > 10000, f'too small: {len(data)}'
       print(f'PNG bytes: {len(data)}')
       "
       ```
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; python -c "
from content.services.ai_prompts import AI_IMAGE_BRAND_SUFFIX, build_ai_image_prompt
assert 'Bialegostoku' in AI_IMAGE_BRAND_SUFFIX
assert 'no text overlay' in AI_IMAGE_BRAND_SUFFIX
p = build_ai_image_prompt('flat lay z ziolo-cytrynowym pesto')
assert p.startswith('flat lay z ziolo-cytrynowym pesto')
assert 'rzemieslnicza' in p
print('ai_prompts OK')
" &amp;&amp; python -c "
from content.services.story_renderer import StoryRenderer
import pathlib, tempfile
r = StoryRenderer()
for color in ['#f3ead7', '#d9c9a3', '#2a2420', '#6b7a3a']:
    data = r.render({'slide_type':'hook','emoji':'🌱','text':'Sezonowe smaki na talerzu','bg_color':color})
    assert data[:8] == b'\x89PNG\r\n\x1a\n', f'not PNG for {color}'
    assert len(data) > 10000, f'too small for {color}: {len(data)}'
    print(f'{color}: {len(data)} bytes')
with tempfile.TemporaryDirectory() as td:
    out = r.render_to_file({'slide_type':'tip','emoji':'💡','text':'Tip','bg_color':'#ebe0c5'}, pathlib.Path(td)/'sub'/'tip.png')
    assert out.exists() and out.stat().st_size > 10000
print('renderer OK')
"</automated>
  </verify>
  <done>
    - content/services/ai_prompts.py istnieje z AI_IMAGE_BRAND_SUFFIX i build_ai_image_prompt
    - content/services/story_renderer.py istnieje z klasa StoryRenderer
    - StoryRenderer().render(slide) zwraca bytes >10KB, valid PNG header (b'\\x89PNG...')
    - render_to_file tworzy plik na dysku, mkdir parents=True
    - Tolerancja hex z/bez '#', fallback bg_color do #f3ead7
    - Emoji font opcjonalny — kod nie wybucha gdy brak NotoColorEmoji.ttf
    - Test 4 roznych kolorow przechodzi
  </done>
</task>

<task type="auto">
  <name>Task 4: Management command generate_story_images</name>
  <files>
    content/management/commands/generate_story_images.py
  </files>
  <action>
    1. Stworz `content/management/commands/generate_story_images.py`:
       ```python
       """Generate IG Stories PNGs (1080x1920) for a WeeklyResearch."""

       from pathlib import Path

       from django.conf import settings
       from django.core.management.base import BaseCommand, CommandError

       from content.models import WeeklyResearch
       from content.services.story_renderer import StoryRenderer


       class Command(BaseCommand):
           help = "Generate Instagram Stories PNGs (1080x1920) for a WeeklyResearch."

           def add_arguments(self, parser):
               parser.add_argument(
                   "--week",
                   type=str,
                   help="WeeklyResearch.week_label (np. 2026-W23)",
               )
               parser.add_argument(
                   "--latest",
                   action="store_true",
                   help="Generate for newest WeeklyResearch with status='formatted'",
               )
               parser.add_argument(
                   "--force",
                   action="store_true",
                   help="Overwrite existing PNGs",
               )

           def handle(self, *args, **opts):
               week = opts.get("week")
               latest = opts.get("latest")
               force = bool(opts.get("force"))

               if bool(week) == bool(latest):
                   raise CommandError(
                       "Podaj dokladnie jedno z: --week LABEL lub --latest"
                   )

               if week:
                   try:
                       wr = WeeklyResearch.objects.get(week_label=week)
                   except WeeklyResearch.DoesNotExist as exc:
                       raise CommandError(
                           f"WeeklyResearch o week_label={week!r} nie istnieje"
                       ) from exc
               else:
                   wr = (
                       WeeklyResearch.objects.filter(status="formatted")
                       .order_by("-date_to")
                       .first()
                   )
                   if wr is None:
                       raise CommandError(
                           "Brak WeeklyResearch ze statusem 'formatted'"
                       )

               if not wr.formatted_json:
                   raise CommandError(
                       f"WR {wr.week_label}: brak formatted_json"
                   )

               stories = wr.formatted_json.get("instagram_stories") or []
               if not stories:
                   raise CommandError(
                       f"WR {wr.week_label}: brak instagram_stories w formatted_json"
                   )

               out_dir = (
                   Path(settings.MEDIA_ROOT)
                   / "weekly_research"
                   / wr.week_label
                   / "stories"
               )
               renderer = StoryRenderer()

               generated, skipped = 0, 0
               for idx, slide in enumerate(stories):
                   slide_type = (
                       (slide.get("slide_type") or f"slide{idx + 1}")
                       .lower()
                       .replace(" ", "_")
                   )
                   filename = f"{idx + 1:02d}_{slide_type}.png"
                   path = out_dir / filename

                   if path.exists() and not force:
                       self.stdout.write(self.style.WARNING(f"skip (exists): {path}"))
                       skipped += 1
                       continue

                   renderer.render_to_file(slide, path)
                   self.stdout.write(self.style.SUCCESS(f"wrote: {path}"))
                   generated += 1

               self.stdout.write(
                   self.style.SUCCESS(
                       f"Done {wr.week_label}: generated={generated}, "
                       f"skipped={skipped}, total={len(stories)}"
                   )
               )
       ```

    2. Verify command zarejestrowany:
       ```bash
       python manage.py help generate_story_images
       ```
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; python manage.py help generate_story_images 2&gt;&amp;1 | grep -q "Generate Instagram Stories" &amp;&amp; echo "registered OK" &amp;&amp; python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings')
django.setup()
from django.core.management import call_command
from django.core.management.base import CommandError
# no args
try:
    call_command('generate_story_images')
    assert False, 'should have raised'
except CommandError as e:
    assert 'dokladnie jedno' in str(e)
# both args
try:
    call_command('generate_story_images', week='X', latest=True)
    assert False, 'should have raised'
except CommandError as e:
    assert 'dokladnie jedno' in str(e)
# nonexistent week
try:
    call_command('generate_story_images', week='9999-W99')
    assert False, 'should have raised'
except CommandError as e:
    assert 'nie istnieje' in str(e)
print('command arg validation OK')
"</automated>
  </verify>
  <done>
    - content/management/commands/generate_story_images.py istnieje
    - manage.py help generate_story_images pokazuje help text
    - Brak --week i --latest -> CommandError
    - --week i --latest jednoczesnie -> CommandError
    - --week NIE-istniejacy -> CommandError
    - --latest gdy brak formatted WR -> CommandError
    - --force nadpisuje, bez --force pomija istniejace
  </done>
</task>

<task type="auto">
  <name>Task 5: Admin action + get_stories_files + change_view extra_context</name>
  <files>
    content/admin.py
  </files>
  <action>
    1. W `content/admin.py` dodaj importy na gorze (pod istniejacymi):
       ```python
       from pathlib import Path

       from django.conf import settings
       from django.urls import reverse

       from content.services.ai_prompts import AI_IMAGE_BRAND_SUFFIX
       from content.services.story_renderer import StoryRenderer
       ```
       `messages` juz jest importowane (linia 1: `from django.contrib import admin, messages`).

    2. Dodaj funkcje akcji (jako standalone, podobnie jak `promote_to_blogpost` w linii 6) PRZED klasa
       `WeeklyResearchAdmin`:
       ```python
       @admin.action(description="Generuj grafiki stories (PNG 1080x1920)")
       def generate_story_images_action(modeladmin, request, queryset):
           renderer = StoryRenderer()
           total_gen, total_skip, total_err = 0, 0, 0
           for wr in queryset:
               if not wr.formatted_json:
                   messages.warning(
                       request,
                       f"{wr.week_label}: brak formatted_json — pominieto",
                   )
                   continue
               stories = wr.formatted_json.get("instagram_stories") or []
               if not stories:
                   messages.warning(
                       request,
                       f"{wr.week_label}: brak instagram_stories — pominieto",
                   )
                   continue
               out_dir = (
                   Path(settings.MEDIA_ROOT)
                   / "weekly_research"
                   / wr.week_label
                   / "stories"
               )
               for idx, slide in enumerate(stories):
                   slide_type = (
                       (slide.get("slide_type") or f"slide{idx + 1}")
                       .lower()
                       .replace(" ", "_")
                   )
                   filename = f"{idx + 1:02d}_{slide_type}.png"
                   path = out_dir / filename
                   if path.exists():
                       total_skip += 1
                       continue
                   try:
                       renderer.render_to_file(slide, path)
                       total_gen += 1
                   except Exception as exc:  # noqa: BLE001
                       total_err += 1
                       messages.warning(
                           request,
                           f"{wr.week_label} slajd {idx + 1}: {exc}",
                       )
           messages.success(
               request,
               f"Wygenerowano {total_gen} grafik, pominieto {total_skip} istniejacych, "
               f"bledow {total_err}",
           )
       ```

    3. Zarejestruj akcje w `WeeklyResearchAdmin.actions`. Obecnie (linia 64):
       ```python
       actions = [promote_to_blogpost]
       ```
       Zmien na:
       ```python
       actions = [promote_to_blogpost, generate_story_images_action]
       ```

    4. Dodaj metode `get_stories_files` na `WeeklyResearchAdmin`:
       ```python
       def get_stories_files(self, obj):
           if obj is None or not obj.week_label:
               return []
           media_root = Path(settings.MEDIA_ROOT)
           stories_dir = media_root / "weekly_research" / obj.week_label / "stories"
           if not stories_dir.exists():
               return []
           files = []
           for png in sorted(stories_dir.glob("*.png")):
               stem = png.stem  # "01_hook"
               try:
                   idx_str, slide_type = stem.split("_", 1)
                   idx = int(idx_str)
               except ValueError:
                   idx = 9999
                   slide_type = stem
               try:
                   rel = png.relative_to(media_root)
                   url = f"{settings.MEDIA_URL.rstrip('/')}/{rel.as_posix()}"
               except ValueError:
                   url = ""
               files.append({
                   "index": idx,
                   "slide_type": slide_type,
                   "url": url,
                   "filename": png.name,
               })
           files.sort(key=lambda f: f["index"])
           return files
       ```

    5. Override `change_view` (NOWY override — adminowi go nie ma w obecnym kodzie):
       ```python
       def change_view(self, request, object_id, form_url="", extra_context=None):
           extra_context = extra_context or {}
           try:
               obj = self.get_object(request, object_id)
           except Exception:
               obj = None
           extra_context["ai_image_brand_suffix"] = AI_IMAGE_BRAND_SUFFIX
           if obj is not None:
               stories_files = self.get_stories_files(obj)
               extra_context["stories_files"] = stories_files
               if stories_files:
                   extra_context["stories_zip_url"] = reverse(
                       "content:weeklyresearch_stories_zip",
                       kwargs={"pk": obj.pk},
                   )
           return super().change_view(
               request, object_id, form_url=form_url, extra_context=extra_context,
           )
       ```

    6. **WAZNE:** Aby kontekst dotarl do `_preview.html` (ktory jest includowany z
       `change_form.html` via `{% include "..." with data=original.formatted_json %}`),
       trzeba zmodyfikowac `change_form.html` LUB `_preview.html` — robimy to w Task 6.
       Tu tylko zapewniamy ze `stories_files`, `stories_zip_url`, `ai_image_brand_suffix`
       sa w root context (extra_context).

    7. Verify:
       ```bash
       python manage.py check
       ```
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; python manage.py check 2&gt;&amp;1 | tail -3 &amp;&amp; python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings')
django.setup()
from django.contrib import admin
from content.admin import WeeklyResearchAdmin, generate_story_images_action
from content.models import WeeklyResearch
adm = WeeklyResearchAdmin(WeeklyResearch, admin.site)
assert generate_story_images_action in adm.actions, 'action not in admin.actions'
assert hasattr(adm, 'get_stories_files')
assert hasattr(adm, 'change_view')
class FakeObj: pk=1; week_label='2099-W99'
assert adm.get_stories_files(FakeObj()) == [], 'expected [] for nonexistent dir'
assert adm.get_stories_files(None) == []
print('admin wiring OK')
"</automated>
  </verify>
  <done>
    - WeeklyResearchAdmin.actions zawiera promote_to_blogpost i generate_story_images_action
    - generate_story_images_action standalone funkcja z @admin.action decoratorem
    - get_stories_files zwraca [] gdy brak katalogu, posortowana lista dict-ow gdy istnieja PNG-i
    - change_view dodaje extra_context: ai_image_brand_suffix zawsze, stories_files i stories_zip_url
      (jesli sa pliki)
    - manage.py check: 0 issues
  </done>
</task>

<task type="auto">
  <name>Task 6: WeeklyResearchStoriesZipView + URL pattern</name>
  <files>
    content/views.py,
    content/urls.py
  </files>
  <action>
    1. W `content/views.py` dodaj na gorze importy (po istniejacych):
       ```python
       import zipfile
       from io import BytesIO
       from pathlib import Path

       from django.conf import settings
       from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
       from django.shortcuts import get_object_or_404
       from django.views import View

       from .models import WeeklyResearch
       ```
       (Sprawdz duplikaty — `BlogPost` jest juz importowany; `WeeklyResearch` jeszcze nie.)

    2. Dodaj klase `WeeklyResearchStoriesZipView` na koncu pliku:
       ```python
       class WeeklyResearchStoriesZipView(View):
           """Staff-only download endpoint: ZIP all generated story PNGs for a WR."""

           def dispatch(self, request, *args, **kwargs):
               if not (request.user.is_authenticated and request.user.is_staff):
                   return HttpResponseForbidden("Forbidden")
               return super().dispatch(request, *args, **kwargs)

           def get(self, request, pk):
               wr = get_object_or_404(WeeklyResearch, pk=pk)
               stories_dir = (
                   Path(settings.MEDIA_ROOT)
                   / "weekly_research"
                   / wr.week_label
                   / "stories"
               )
               if not stories_dir.exists():
                   return HttpResponseNotFound("Brak wygenerowanych grafik")
               pngs = sorted(stories_dir.glob("*.png"))
               if not pngs:
                   return HttpResponseNotFound("Brak wygenerowanych grafik")
               buf = BytesIO()
               with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                   for png in pngs:
                       zf.write(png, arcname=png.name)
               buf.seek(0)
               resp = HttpResponse(buf.getvalue(), content_type="application/zip")
               resp["Content-Disposition"] = (
                   f'attachment; filename="stories_{wr.week_label}.zip"'
               )
               return resp
       ```

    3. W `content/urls.py` dodaj pattern (zachowaj istniejace blog_list i blog_detail).
       **WAZNE:** existujace patterny to:
       ```python
       path("", views.BlogListView.as_view(), name="blog_list"),
       path("<slug:slug>/", views.BlogDetailView.as_view(), name="blog_detail"),
       ```
       `<slug:slug>/` zlapie WSZYSTKO co nie jest pustym stringiem — wiec NOWY pattern musi byc PRZED nim,
       albo wlasciwie zostawimy na koncu z slugiem-przewaga (slug matchuje, ale nasze "admin/..."
       zawiera `/` ktorych slug nie obsluguje).

       Dodaj pattern PRZED `<slug:slug>/`:
       ```python
       path(
           "admin/content/weeklyresearch/<int:pk>/stories.zip",
           views.WeeklyResearchStoriesZipView.as_view(),
           name="weeklyresearch_stories_zip",
       ),
       ```

       Finalny `content/urls.py`:
       ```python
       from django.urls import path

       from . import views


       app_name = "content"

       urlpatterns = [
           path("", views.BlogListView.as_view(), name="blog_list"),
           path(
               "admin/content/weeklyresearch/<int:pk>/stories.zip",
               views.WeeklyResearchStoriesZipView.as_view(),
               name="weeklyresearch_stories_zip",
           ),
           path("<slug:slug>/", views.BlogDetailView.as_view(), name="blog_detail"),
       ]
       ```

    4. **NIE modyfikuj `backend/urls.py`** — `content.urls` juz jest dolaczone pod prefix `blog/`
       (linia 16: `path("blog/", include("content.urls", namespace="content"))`).
       URL bedzie pod: `/blog/admin/content/weeklyresearch/<pk>/stories.zip` — funkcjonalnie OK,
       `reverse('content:weeklyresearch_stories_zip', kwargs={'pk':X})` dziala bez zmian w admin.py.

    5. Verify:
       ```bash
       python manage.py check
       python -c "
       import os, django
       os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings')
       django.setup()
       from django.urls import reverse
       url = reverse('content:weeklyresearch_stories_zip', kwargs={'pk': 1})
       print(f'URL: {url}')
       assert url.endswith('/stories.zip'), url
       "
       ```
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; python manage.py check 2&gt;&amp;1 | tail -3 &amp;&amp; python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings')
django.setup()
from django.urls import reverse
url = reverse('content:weeklyresearch_stories_zip', kwargs={'pk': 1})
assert url.endswith('/stories.zip'), url
print(f'reverse OK: {url}')
" &amp;&amp; python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings')
django.setup()
from django.test import Client
c = Client()
r = c.get('/blog/admin/content/weeklyresearch/1/stories.zip')
assert r.status_code in (302, 403, 404), f'expected 302/403/404 for anon, got {r.status_code}'
print(f'anon access: {r.status_code}')
"</automated>
  </verify>
  <done>
    - WeeklyResearchStoriesZipView istnieje w content/views.py
    - URL 'content:weeklyresearch_stories_zip' rozwiazywalne przez reverse()
    - URL pattern dodany w content/urls.py PRZED <slug:slug>/
    - Anonimowy GET -> 403 (Forbidden bo dispatch sprawdza staff)
    - Staff GET + brak plikow -> 404
    - Staff GET + sa pliki -> 200 + Content-Type application/zip + Content-Disposition attachment
    - blog_list i blog_detail nadal dzialaja (smoke)
    - manage.py check 0 issues
  </done>
</task>

<task type="auto">
  <name>Task 7: Template _preview.html — Stories tab z PNG-ami + Posts tab z AI promptem</name>
  <files>
    content/templates/admin/content/weeklyresearch/_preview.html
  </files>
  <action>
    1. **WAZNE — context propagation:** `_preview.html` jest includowany z `change_form.html`
       przez `{% include "..." with data=original.formatted_json %}`. Aby `stories_files`,
       `stories_zip_url`, `ai_image_brand_suffix` byly widoczne w included template,
       musimy je przekazac przez `with`. Zmodyfikuj `change_form.html` rownolegle:

       W `content/templates/admin/content/weeklyresearch/change_form.html` zmien linie z `{% include %}`:
       ```django
       {% include "admin/content/weeklyresearch/_preview.html" with data=original.formatted_json stories_files=stories_files stories_zip_url=stories_zip_url ai_image_brand_suffix=ai_image_brand_suffix %}
       ```
       (Django auto-przepuszcza tylko kontekst gdy `only` flag — bez `only` rodzic context jest
       dostepny, ALE bezpieczniej jawnie przekazac.)

    2. W `_preview.html` w `kk-panel-stories` (linia 75-96) zastap caly blok stories:
       ```django
       {# ===== STORIES ===== #}
       <div class="kk-panel kk-panel-stories">
         {% if stories_files %}
           <div class="kk-stories-generated">
             <div class="kk-stories-actions">
               {% if stories_zip_url %}
                 <a class="kk-stories-zip-link" href="{{ stories_zip_url }}" download>
                   Pobierz wszystkie jako ZIP ({{ stories_files|length }} plikow)
                 </a>
               {% endif %}
             </div>
             <div class="kk-stories-grid">
               {% for sf in stories_files %}
                 <div class="kk-story-actual">
                   <a href="{{ sf.url }}" download="{{ sf.filename }}" target="_blank" rel="noopener">
                     <img class="kk-story-actual-img" src="{{ sf.url }}" alt="{{ sf.filename }}" loading="lazy">
                   </a>
                   <div class="kk-story-actual-meta">
                     <span class="kk-story-actual-label">{{ sf.slide_type }}</span>
                     <a class="kk-story-actual-download" href="{{ sf.url }}" download="{{ sf.filename }}">PNG</a>
                   </div>
                 </div>
               {% endfor %}
             </div>
           </div>
           <details class="kk-stories-placeholder-toggle">
             <summary>Pokaz podglad CSS (placeholder)</summary>
             <div class="kk-stories-grid">
               {% for s in data.instagram_stories %}
                 <div class="kk-story-wrapper">
                   <div class="kk-story-card"
                        style="background-color: {{ s.bg_color }}; color: {{ s.bg_color|text_color_for_bg }};">
                     <div class="kk-story-emoji">{{ s.emoji }}</div>
                     <div class="kk-story-text">{{ s.text }}</div>
                     <div class="kk-story-type">{{ s.slide_type }}</div>
                   </div>
                   <div class="kk-story-hex">{{ s.bg_color }}</div>
                   <button type="button" class="kk-copy-btn" data-copy-text="{{ s.text }}">Tekst</button>
                 </div>
               {% endfor %}
             </div>
           </details>
         {% else %}
           <p class="kk-stories-info">
             Brak wygenerowanych grafik. W list view zaznacz ten research, akcja
             <b>"Generuj grafiki stories (PNG 1080x1920)"</b>, lub odpal:
             <code>python manage.py generate_story_images --week {{ original.week_label|default:"&lt;label&gt;" }}</code>
           </p>
           <div class="kk-stories-grid">
             {% for s in data.instagram_stories %}
               <div class="kk-story-wrapper">
                 <div class="kk-story-card"
                      style="background-color: {{ s.bg_color }}; color: {{ s.bg_color|text_color_for_bg }};">
                   <div class="kk-story-emoji">{{ s.emoji }}</div>
                   <div class="kk-story-text">{{ s.text }}</div>
                   <div class="kk-story-type">{{ s.slide_type }}</div>
                 </div>
                 <div class="kk-story-hex">{{ s.bg_color }}</div>
                 <button type="button" class="kk-copy-btn" data-copy-text="{{ s.text }}">Tekst</button>
               </div>
             {% endfor %}
           </div>
         {% endif %}
         <div class="kk-bulk-actions">
           <button type="button" class="kk-copy-btn kk-copy-btn-primary"
                   data-copy-text="{% for s in data.instagram_stories %}{{ forloop.counter }}. [{{ s.slide_type }}] {{ s.emoji }} {{ s.text }}&#10;{% endfor %}">
             Skopiuj wszystkie teksty stories
           </button>
         </div>
       </div>
       ```

    3. W `_preview.html` w `kk-panel-posts` (linia 48-72) wewnatrz petli `{% for p in data.instagram_posts %}`
       dodaj sekcje AI prompt PO obecnym `.kk-post-actions` div:

       ```django
       {% if ai_image_brand_suffix %}
         {% with ai_prompt=p.visual_hint|stringformat:"s"|add:ai_image_brand_suffix %}
           <div class="kk-post-ai-prompt">
             <div class="kk-post-ai-prompt-header">Prompt AI (z brand stylem)</div>
             <pre class="kk-ai-prompt-preview">{{ ai_prompt }}</pre>
             <div class="kk-post-ai-actions">
               <button type="button" class="kk-copy-btn" data-copy-text="{{ ai_prompt }}">
                 Skopiuj prompt do AI (z brand stylem)
               </button>
             </div>
           </div>
         {% endwith %}
       {% endif %}
       ```

       Gwarancja `{% if ai_image_brand_suffix %}` zabezpiecza przed bledem jesli context
       nie zostal przekazany (backward-compat).

    4. **Uwaga: kk-panel-stories grid CSS** — istniejacy `.kk-stories-grid` ma
       `grid-template-columns: repeat(auto-fill, 140px)`. Dziala dla nowych img tez (140px szerokosci,
       proporcje 9:16 z natury PNG 1080x1920 → wysokosc ~248px). OK.

    5. Verify template parsuje + ma nowe klasy:
       ```bash
       python -c "
       import django, os
       os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings')
       django.setup()
       from django.template.loader import get_template
       t = get_template('admin/content/weeklyresearch/_preview.html')
       src = t.template.source
       assert 'stories_files' in src, 'stories_files conditional missing'
       assert 'kk-stories-zip-link' in src, 'ZIP link missing'
       assert 'kk-story-actual-img' in src, 'actual img class missing'
       assert 'kk-post-ai-prompt' in src, 'AI prompt section missing'
       assert 'ai_image_brand_suffix' in src, 'AI suffix var missing'
       print('template structure OK')
       "
       ```
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings')
django.setup()
from django.template.loader import get_template
t = get_template('admin/content/weeklyresearch/_preview.html')
src = t.template.source
assert 'stories_files' in src
assert 'kk-stories-zip-link' in src
assert 'kk-story-actual-img' in src
assert 'kk-post-ai-prompt' in src
assert 'ai_image_brand_suffix' in src
print('preview template OK')
t2 = get_template('admin/content/weeklyresearch/change_form.html')
src2 = t2.template.source
assert 'stories_files=stories_files' in src2 or 'stories_files' in src2, 'change_form needs to pass stories_files'
print('change_form template OK')
" &amp;&amp; python manage.py check 2&gt;&amp;1 | tail -3</automated>
  </verify>
  <done>
    - _preview.html ma blok `{% if stories_files %}...{% else %}` w kk-panel-stories
    - Pokazuje rzeczywiste PNG-i jako <img class="kk-story-actual-img"> z download linkami
    - Link "Pobierz wszystkie jako ZIP" wyswietla sie gdy stories_zip_url jest
    - CSS placeholder zachowany w details (gdy sa PNG-i) lub jako fallback (gdy nie ma)
    - kk-panel-posts: pod kazdym postem sekcja .kk-post-ai-prompt z <pre> i Copy btn
    - change_form.html przekazuje stories_files, stories_zip_url, ai_image_brand_suffix do include
    - manage.py check 0 issues
  </done>
</task>

<task type="auto">
  <name>Task 8: CSS dla nowych elementow (stories img grid + AI prompt)</name>
  <files>
    content/static/content/admin/weekly_research_preview.css
  </files>
  <action>
    Dodaj na koncu `content/static/content/admin/weekly_research_preview.css` (NIE modyfikuj
    istniejacych regul):

    ```css
    /* ===== Stories — wygenerowane PNG ===== */
    .kk-stories-generated {
        margin-bottom: 16px;
    }

    .kk-stories-actions {
        margin-bottom: 12px;
    }

    .kk-stories-zip-link {
        display: inline-block;
        background: var(--ink);
        color: #fff;
        padding: 10px 18px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 600;
        text-decoration: none;
        transition: background 0.15s;
    }

    .kk-stories-zip-link:hover {
        background: #1a1612;
        color: #fff;
    }

    .kk-story-actual {
        display: flex;
        flex-direction: column;
        gap: 6px;
        align-items: center;
    }

    .kk-story-actual-img {
        width: 140px;
        height: auto;
        aspect-ratio: 9 / 16;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        display: block;
        object-fit: cover;
    }

    .kk-story-actual-meta {
        display: flex;
        gap: 8px;
        align-items: center;
        font-size: 11px;
        color: var(--ink-soft);
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .kk-story-actual-download {
        color: var(--accent-2);
        font-weight: 700;
        text-decoration: none;
    }

    .kk-story-actual-download:hover {
        text-decoration: underline;
    }

    .kk-stories-placeholder-toggle {
        margin-top: 20px;
        padding: 12px 0;
        border-top: 1px dashed var(--rule);
    }

    .kk-stories-placeholder-toggle > summary {
        cursor: pointer;
        color: var(--ink-soft);
        font-size: 13px;
        font-weight: 600;
    }

    .kk-stories-info {
        background: #fff8ea;
        border: 1px dashed var(--rule);
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 13px;
        color: var(--ink-soft);
        margin-bottom: 16px;
        line-height: 1.5;
    }

    .kk-stories-info code {
        font-family: "JetBrains Mono", monospace;
        font-size: 12px;
        background: var(--paper-shadow);
        padding: 2px 6px;
        border-radius: 4px;
        color: var(--ink);
    }

    /* ===== Posts — AI prompt (visual_hint + brand suffix) ===== */
    .kk-post-ai-prompt {
        margin-top: 12px;
        padding: 12px 14px;
        background: #fff8ea;
        border: 1px dashed var(--accent-3);
        border-radius: 8px;
    }

    .kk-post-ai-prompt-header {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--accent-3);
        margin-bottom: 8px;
    }

    .kk-ai-prompt-preview {
        font-family: "JetBrains Mono", monospace;
        font-size: 12px;
        line-height: 1.5;
        background: var(--paper);
        color: var(--ink);
        padding: 10px 12px;
        border-radius: 6px;
        max-height: 140px;
        overflow: auto;
        margin: 0 0 8px;
        white-space: pre-wrap;
        border: 1px solid var(--rule);
    }

    .kk-post-ai-actions {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }
    ```

    Verify, CSS jest valid (no syntax errors) — wystarczy ze plik istnieje i sie includuje
    przez `{% static %}` w change_form.html (juz tak jest).
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; grep -q "kk-stories-zip-link" content/static/content/admin/weekly_research_preview.css &amp;&amp; grep -q "kk-story-actual-img" content/static/content/admin/weekly_research_preview.css &amp;&amp; grep -q "kk-post-ai-prompt" content/static/content/admin/weekly_research_preview.css &amp;&amp; grep -q "kk-ai-prompt-preview" content/static/content/admin/weekly_research_preview.css &amp;&amp; python -c "
# Quick CSS sanity: balanced braces
with open('content/static/content/admin/weekly_research_preview.css') as f:
    src = f.read()
assert src.count('{') == src.count('}'), f'unbalanced braces: {src.count(chr(123))} vs {src.count(chr(125))}'
print(f'CSS OK: {len(src)} bytes, balanced')
"</automated>
  </verify>
  <done>
    - CSS dodaje klasy: kk-stories-zip-link, kk-story-actual, kk-story-actual-img,
      kk-story-actual-meta, kk-story-actual-download, kk-stories-placeholder-toggle,
      kk-stories-info, kk-post-ai-prompt, kk-post-ai-prompt-header, kk-ai-prompt-preview,
      kk-post-ai-actions
    - Balanced braces (parse-OK)
    - Plik dalej jest includowany przez change_form.html via {% static %}
  </done>
</task>

<task type="auto">
  <name>Task 9: README content/ — dokumentacja + odznaczenie roadmap punkt 3</name>
  <files>
    content/README.md
  </files>
  <action>
    1. W `content/README.md`:
       a) W sekcji "Co mozna z tym dalej zrobic" (linia 126) zmien punkt 3:
          ```
          3. **Generowanie obrazkow pod IG** — `visual_hint`...
          ```
          NA:
          ```
          3. **✅ Generowanie grafik stories + AI prompty pod posty** — DONE (260603-aou).
             Patrz sekcja "Generowanie grafik IG" ponizej.
          ```

       b) Po sekcji "Pliki w tym appie" (na koncu pliku) dodaj nowa sekcje:
          ```markdown
          ## Generowanie grafik IG

          ### Stories (PNG 1080x1920)

          Pipeline produkuje gotowe pliki PNG na rozmiar IG Stories — generowane lokalnie przez
          Pillow z bundled fontow Noto Sans (w `content/fonts/`). Pliki ladawia w
          `MEDIA_ROOT/weekly_research/<week_label>/stories/01_hook.png` itd.

          **Z admina:**
          1. Wejdz na `/admin/content/weeklyresearch/`
          2. Zaznacz checkbox przy interesujacym researchu
          3. W menu "Action" wybierz **"Generuj grafiki stories (PNG 1080x1920)"** i klik Go
          4. Komunikat na gorze: "Wygenerowano N grafik, pominieto M istniejacych"
          5. Wejdz na change view tego researchu — tab "IG Stories" pokazuje miniatury
             rzeczywistych PNG-ow z linkami download + przyciskiem **"Pobierz wszystkie jako ZIP"**

          **Z CLI** (lokalnie lub na serwerze):
          ```bash
          # Najnowszy formatted research
          python manage.py generate_story_images --latest

          # Konkretny tydzien
          python manage.py generate_story_images --week 2026-W23

          # Nadpisz istniejace pliki
          python manage.py generate_story_images --latest --force
          ```

          ZIP endpoint (staff-only): `/blog/admin/content/weeklyresearch/<pk>/stories.zip`

          Jesli nie ma jeszcze NotoColorEmoji.ttf bundled (lub byl >12MiB) — emoji renderuja sie
          jako tekst w NotoSans Bold (czasem widoczne jako kolko/puste).

          ### Posty — AI image prompts

          Pod kazdym postem w tabie "IG Posty" jest sekcja **"Prompt AI (z brand stylem)"** —
          `visual_hint` z formatted_json + brand styling suffix (Bialystok, rzemieslnicza
          fotografia, square 1080x1080, no text overlay).

          Klik **"Skopiuj prompt do AI (z brand stylem)"** → wklej w ChatGPT (DALL-E),
          Midjourney lub innym generatorze obrazow → dostaniesz spojny brand-wise obrazek
          pod posta.

          Brand suffix mieszka w `content/services/ai_prompts.py::AI_IMAGE_BRAND_SUFFIX` — to
          jedyne miejsce do edycji jezeli chcesz zmienic styling.

          ### Architektura

          | Komponent | Lokalizacja | Co robi |
          |---|---|---|
          | `StoryRenderer` | `content/services/story_renderer.py` | Buduje PNG 1080x1920 z dict-a slajdu |
          | `text_color_for_bg` | `content/services/colors.py` | Brand palette mapping bg → text |
          | `AI_IMAGE_BRAND_SUFFIX` | `content/services/ai_prompts.py` | Stala brand styling do promptow AI |
          | `generate_story_images` | `content/management/commands/` | CLI command |
          | `generate_story_images_action` | `content/admin.py` | Admin action |
          | `WeeklyResearchStoriesZipView` | `content/views.py` | ZIP download endpoint |
          | Fonty | `content/fonts/NotoSans-{Regular,Bold}.ttf` | Bundled, w repo (~600KB-1MB total) |
          ```

       c) Update tabeli "Pliki w tym appie" — dodaj nowe wiersze:
          ```markdown
          | `services/colors.py` | Brand palette mapping (text_color_for_bg) |
          | `services/story_renderer.py` | PNG renderer dla IG Stories |
          | `services/ai_prompts.py` | Brand AI image prompt suffix |
          | `management/commands/generate_story_images.py` | CLI generator PNG-ow |
          | `fonts/NotoSans-*.ttf` | Bundled fonty (Pillow) |
          | `views.py` | + WeeklyResearchStoriesZipView (ZIP download) |
          ```

    2. Verify:
       ```bash
       grep -q "Generowanie grafik IG" content/README.md
       grep -q "generate_story_images" content/README.md
       grep -q "AI_IMAGE_BRAND_SUFFIX" content/README.md
       ```
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; grep -q "Generowanie grafik IG" content/README.md &amp;&amp; grep -q "generate_story_images" content/README.md &amp;&amp; grep -q "AI_IMAGE_BRAND_SUFFIX" content/README.md &amp;&amp; grep -q "stories_zip" content/README.md &amp;&amp; echo "README updated OK"</automated>
  </verify>
  <done>
    - README sekcja "Generowanie grafik IG" istnieje
    - Punkt 3 roadmapy oznaczony jako DONE (lub przeniesiony do dedykowanej sekcji)
    - Dokumentowane: admin action workflow, CLI command (--week/--latest/--force), ZIP URL,
      brand suffix location, fonts location
    - Tabela "Pliki w tym appie" ma nowe wiersze
  </done>
</task>

<task type="auto">
  <name>Task 10: End-to-end smoke + sanity, commit, push</name>
  <files>
    (no new files — git operations)
  </files>
  <action>
    1. `manage.py check` (musi byc 0 issues):
       ```bash
       python manage.py check
       ```

    2. Pelny smoke test — bez fixtures, tworzymy WR inline w shell:
       ```bash
       python -c "
       import os, django
       os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings')
       django.setup()
       from datetime import date, timedelta
       from content.models import WeeklyResearch
       # Sprawdz czy juz istnieje testowy
       try:
           wr = WeeklyResearch.objects.get(week_label='9999-W99')
           wr.delete()
       except WeeklyResearch.DoesNotExist:
           pass
       wr = WeeklyResearch.objects.create(
           week_label='9999-W99',
           date_from=date.today(),
           date_to=date.today() + timedelta(days=6),
           status='formatted',
           formatted_json={
               'instagram_stories': [
                   {'slide_type':'hook','emoji':'🌱','text':'Test slajdu pierwszy','bg_color':'#f3ead7'},
                   {'slide_type':'tip','emoji':'💡','text':'Drugi slajd','bg_color':'#6b7a3a'},
               ],
               'instagram_posts': [
                   {'caption':'test','hashtags':['x'],'visual_hint':'flat lay'},
               ],
           },
       )
       print(f'Created test WR: {wr.pk}')
       "
       ```

    3. Odpal management command:
       ```bash
       python manage.py generate_story_images --week 9999-W99
       ```

    4. Sprawdz wygenerowane pliki:
       ```bash
       ls -la public/media/weekly_research/9999-W99/stories/
       python -c "
       import os
       d = 'public/media/weekly_research/9999-W99/stories'
       files = sorted(os.listdir(d))
       assert files == ['01_hook.png', '02_tip.png'], files
       for f in files:
           p = os.path.join(d, f)
           with open(p, 'rb') as fh:
               head = fh.read(8)
           assert head == b'\x89PNG\r\n\x1a\n', f'{f} not PNG'
           assert os.path.getsize(p) > 10000, f'{f} too small'
       print('smoke OK')
       "
       ```

    5. Smoke ZIP via Django test client (staff user):
       ```bash
       python -c "
       import os, django
       os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings')
       django.setup()
       from django.test import Client
       from django.contrib.auth import get_user_model
       from content.models import WeeklyResearch
       U = get_user_model()
       u, _ = U.objects.get_or_create(email='smoke@test.local', defaults={'is_staff':True, 'is_active':True})
       u.is_staff = True
       u.is_active = True
       u.set_password('xT9bn!2fdsa#zxLP')
       u.save()
       c = Client()
       assert c.login(email='smoke@test.local', password='xT9bn!2fdsa#zxLP')
       wr = WeeklyResearch.objects.get(week_label='9999-W99')
       r = c.get(f'/blog/admin/content/weeklyresearch/{wr.pk}/stories.zip')
       assert r.status_code == 200, f'expected 200, got {r.status_code}'
       assert r['Content-Type'] == 'application/zip', r['Content-Type']
       assert 'attachment' in r['Content-Disposition']
       assert len(r.content) > 20000, f'zip too small: {len(r.content)}'
       print(f'ZIP OK: {len(r.content)} bytes')
       u.delete()
       "
       ```

    6. Cleanup po smoke:
       ```bash
       python -c "
       import os, django, shutil
       os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings')
       django.setup()
       from content.models import WeeklyResearch
       try:
           WeeklyResearch.objects.get(week_label='9999-W99').delete()
       except WeeklyResearch.DoesNotExist:
           pass
       p = 'public/media/weekly_research/9999-W99'
       if os.path.isdir(p):
           shutil.rmtree(p)
       print('cleanup OK')
       "
       ```

    7. Git commit (atomic, tematyczne):
       ```bash
       # Pierwszy commit: services + fonty (foundation)
       git add content/services/ content/fonts/ content/templatetags/content_extras.py
       git commit -m "feat(content): services layer (colors, story_renderer, ai_prompts) + bundled Noto fonts"

       # Drugi commit: command + admin action + views/urls
       git add content/management/commands/generate_story_images.py content/admin.py content/views.py content/urls.py
       git commit -m "feat(content): IG stories PNG generator (admin action, CLI command, ZIP download)"

       # Trzeci commit: templates + CSS + README
       git add content/templates/admin/content/weeklyresearch/ content/static/content/admin/weekly_research_preview.css content/README.md
       git commit -m "feat(content): admin preview - real PNG miniatures + AI image prompt with brand styling"
       ```

    8. Push:
       ```bash
       git push origin main
       ```
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; python manage.py check 2&gt;&amp;1 | tail -2 &amp;&amp; git log --oneline -5 &amp;&amp; git status --short</automated>
  </verify>
  <done>
    - manage.py check: 0 issues
    - Smoke command generate_story_images --week 9999-W99 produkuje 2 PNG-i (01_hook.png, 02_tip.png)
    - Smoke ZIP endpoint zwraca 200 + application/zip + attachment header dla staff usera
    - Cleanup: usuniety testowy WR i pliki public/media/weekly_research/9999-W99/
    - 3 commity utworzone (services/fonty, command/admin/views, templates/css/readme)
    - git push origin main: success
    - git status: clean (no uncommitted changes)
  </done>
</task>

<task type="auto">
  <name>Task 11: Deploy na panel84.mydevil.net + smoke prod (Pillow + fonty + HTTP 200)</name>
  <files>
    (deploy via paramiko — no new repo files)
  </files>
  <action>
    1. Skrypt deploy via paramiko (uzyc systemowego python3):
       ```bash
       /usr/bin/python3 << 'PY_EOF'
       import paramiko
       host = 'panel84.mydevil.net'
       user = 'jem3pizze'
       password = 'Tak12toto.'
       app_dir = '/usr/home/jem3pizze/domains/kuchennakomitywa.pl/public_python'
       venv_py = '/usr/home/jem3pizze/.virtualenvs/komitywa/bin/python'

       ssh = paramiko.SSHClient()
       ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
       ssh.connect(host, username=user, password=password, timeout=30)

       def run(cmd, check=True):
           print(f'$ {cmd}')
           stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
           out = stdout.read().decode()
           err = stderr.read().decode()
           rc = stdout.channel.recv_exit_status()
           if out: print(out)
           if err: print(f'STDERR: {err}')
           if check and rc != 0:
               raise RuntimeError(f'cmd failed rc={rc}: {cmd}')
           return out, err, rc

       # 1. Pull latest
       run(f'cd {app_dir} && git fetch origin && git reset --hard origin/main')

       # 2. Pokaz aktualny HEAD na serwerze
       run(f'cd {app_dir} && git log --oneline -3')

       # 3. Install/upgrade deps (Pillow juz jest, ale nie zaszkodzi)
       run(f'cd {app_dir} && {venv_py} -m pip install -r requirements.txt --upgrade-strategy only-if-needed')

       # 4. Collectstatic (CSS update wymaga)
       run(f'cd {app_dir} && {venv_py} manage.py collectstatic --noinput')

       # 5. Migrate (nie powinno byc nic, ale safety)
       run(f'cd {app_dir} && {venv_py} manage.py migrate --noinput')

       # 6. Check
       run(f'cd {app_dir} && {venv_py} manage.py check')

       # 7. Smoke Pillow + fonty
       smoke = (
           f'cd {app_dir} && {venv_py} -c "'
           'from PIL import ImageFont; '
           "ImageFont.truetype('content/fonts/NotoSans-Regular.ttf', 80); "
           "ImageFont.truetype('content/fonts/NotoSans-Bold.ttf', 80); "
           'from content.services.story_renderer import StoryRenderer; '
           'r = StoryRenderer(); '
           "data = r.render({'slide_type':'hook','emoji':'X','text':'prod smoke','bg_color':'#f3ead7'}); "
           "assert data[:8] == b'\\x89PNG\\r\\n\\x1a\\n'; "
           "print(f'PNG bytes: {len(data)}')"
           '"'
       )
       run(smoke)

       # 8. Touch passenger restart (apache restart trick)
       run(f'cd {app_dir} && touch tmp/restart.txt || mkdir -p tmp && touch tmp/restart.txt')

       ssh.close()
       print('DEPLOY OK')
       PY_EOF
       ```

    2. **Smoke HTTP** — login page powinien zwrocic 200 (sprawdza ze app w ogole boot-uje):
       ```bash
       curl -sS -o /dev/null -w "HTTP %{http_code}\n" https://kuchennakomitywa.pl/admin/login/
       ```
       Spodziewane: `HTTP 200` (lub 302 jesli juz zalogowany, ale anonimowy curl bez cookie → 200).

    3. **NIE odpalaj `generate_story_images` na prod** (per constraints) — user uruchomi sam.

    4. **Final summary smoke** — sprawdz dostepnosc strony glownej + bloga:
       ```bash
       curl -sS -o /dev/null -w "/ %{http_code}\n" https://kuchennakomitywa.pl/
       curl -sS -o /dev/null -w "/blog/ %{http_code}\n" https://kuchennakomitywa.pl/blog/
       ```
       Spodziewane: oba `HTTP 200`.
  </action>
  <verify>
    <automated>curl -sS -o /dev/null -w "%{http_code}\n" https://kuchennakomitywa.pl/admin/login/ | grep -E "^200$" &amp;&amp; curl -sS -o /dev/null -w "%{http_code}\n" https://kuchennakomitywa.pl/ | grep -E "^(200|301|302)$" &amp;&amp; echo "prod smoke OK"</automated>
  </verify>
  <done>
    - Deploy script wykonal: git pull (HEAD = latest local commit), pip install, collectstatic,
      migrate, check, smoke Pillow+fonty+StoryRenderer render
    - Wszystkie ssh commandy zwrocily rc=0
    - touch tmp/restart.txt — passenger restart
    - GET https://kuchennakomitywa.pl/admin/login/ → HTTP 200
    - GET https://kuchennakomitywa.pl/ → HTTP 200 (lub 301/302)
    - GET https://kuchennakomitywa.pl/blog/ → HTTP 200
    - NIE odpalono `generate_story_images` na prod (user zrobi sam)
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| anonymous user -> ZIP endpoint | unauth uzytkownik probuje pobrac archiwum stories |
| staff user -> ZIP filesystem path | staff przy aktywnej sesji moglby probowac path traversal przez pk |
| filesystem -> Pillow render | dane slajdu (z formatted_json) przekazywane do PIL ImageDraw |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-aou-01 | Information disclosure | WeeklyResearchStoriesZipView | mitigate | dispatch() wymaga request.user.is_authenticated AND is_staff; nie-staff → 403 |
| T-aou-02 | Tampering | WeeklyResearchStoriesZipView pk | mitigate | get_object_or_404 + pk to int PK z DB; brak path traversal bo path bazuje na `wr.week_label` (CharField z bazy, nie z URL) |
| T-aou-03 | Denial of service | ZIP build w pamieci | accept | n=6-7 PNG-ow ~50KB kazdy → ~400KB w pamieci; pomijalne |
| T-aou-04 | Tampering | StoryRenderer slide dict | accept | dane z formatted_json zapisanego przez run_weekly_research (Claude JSON); admin-trusted source; ImageDraw na zlych danych raczej zglosi exception, ktory adminowo zalapie messages.warning |
| T-aou-05 | Information disclosure | MEDIA path leak in URLs | accept | URL ma postac `/media/weekly_research/<label>/stories/<idx>_<type>.png` — label i type sa znane staff-only przez admin; brak PII |
| T-aou-06 | Spoofing | curl/wget na fonty z GitHub | accept | jednorazowy download w dev; weryfikacja przez PIL.ImageFont.truetype (parse PNG sanity); fonty z repo (signed commit) potem |
| T-aou-07 | Tampering | content/fonts/* tracked in git | mitigate | weryfikacja `.gitignore` nie wyklucza; fonty trafiaja do repo i deployowane gita |
| T-aou-08 | Denial of service | `generate_story_images` na N WR x M slajdow | accept | N typowo 1-2, M=6-7; render 1080x1920 PNG ~200ms, max kilkanascie sekund |
</threat_model>

<verification>

## End-to-end checks

1. **manage.py check** zwraca 0 issues po kazdym tasku (lokalnie + prod).
2. **Imports:** `from content.services.colors import text_color_for_bg`, `from content.services.story_renderer import StoryRenderer`, `from content.services.ai_prompts import AI_IMAGE_BRAND_SUFFIX, build_ai_image_prompt` dzialaja bez bledu.
3. **PIL:** `ImageFont.truetype('content/fonts/NotoSans-{Regular,Bold}.ttf', 80)` laduje bez bledu.
4. **StoryRenderer:** `render({'slide_type':'hook','emoji':'🌱','text':'...','bg_color':'#f3ead7'})` zwraca PNG bytes >10KB.
5. **CLI command:** `manage.py generate_story_images --latest` lub `--week LABEL` produkuje PNG-i w `MEDIA_ROOT/weekly_research/<label>/stories/NN_<type>.png`. `--force` nadpisuje. Brak args / oba args -> CommandError.
6. **Admin action:** Zaznaczenie WR + akcja "Generuj grafiki stories" produkuje pliki + messages.success.
7. **Admin change view:**
   - Tab "IG Stories" pokazuje miniatury rzeczywistych PNG-ow gdy sa wygenerowane.
   - Pokazuje link "Pobierz wszystkie jako ZIP" gdy `stories_zip_url` jest.
   - Pokazuje fallback (CSS placeholder + info) gdy brak plikow.
   - Tab "IG Posty" pod kazdym postem pokazuje sekcje `.kk-post-ai-prompt` z preview + Copy button.
8. **ZIP endpoint:**
   - Anonimowy GET -> 403.
   - Staff GET + brak plikow -> 404.
   - Staff GET + sa pliki -> 200 + application/zip + Content-Disposition attachment + content > 20KB.
9. **Template parse:** `get_template('admin/content/weeklyresearch/_preview.html')` i `change_form.html` ladowane bez bledu.
10. **Smoke prod (HTTP):** /admin/login/ -> 200, / -> 200/301/302, /blog/ -> 200.
11. **Smoke prod (Pillow):** `python -c "from PIL import ImageFont; ImageFont.truetype('content/fonts/NotoSans-Bold.ttf', 80); from content.services.story_renderer import StoryRenderer; print(len(StoryRenderer().render({...})))"` → > 10000.

</verification>

<success_criteria>

- [ ] `content/services/colors.py` istnieje, `text_color_for_bg` 1:1 z mappingu w content_extras + tolerancja hex bez `#`
- [ ] `content/services/story_renderer.py` istnieje, StoryRenderer.render() zwraca valid PNG >10KB
- [ ] `content/services/ai_prompts.py` istnieje, AI_IMAGE_BRAND_SUFFIX ma "Bialegostoku" i "no text overlay"
- [ ] `content/fonts/NotoSans-Regular.ttf` + `NotoSans-Bold.ttf` w repo, kazdy >100KB, suma <15MiB
- [ ] `content/management/commands/generate_story_images.py` istnieje, `manage.py help generate_story_images` dziala
- [ ] `content/admin.py`: `generate_story_images_action` w actions + `get_stories_files` method + `change_view` override
- [ ] `content/views.py`: WeeklyResearchStoriesZipView staff-only
- [ ] `content/urls.py`: pattern `weeklyresearch_stories_zip` dodany PRZED `<slug:slug>/`
- [ ] `content/templates/.../_preview.html`: blok `{% if stories_files %}` w stories tab + `{% if ai_image_brand_suffix %}` w posts tab
- [ ] `content/templates/.../change_form.html`: include przekazuje stories_files / stories_zip_url / ai_image_brand_suffix
- [ ] `content/static/.../weekly_research_preview.css`: dodane klasy kk-stories-zip-link, kk-story-actual-img, kk-post-ai-prompt, kk-ai-prompt-preview
- [ ] `content/README.md`: sekcja "Generowanie grafik IG" + punkt 3 roadmapy oznaczony DONE
- [ ] Smoke lokalny: command generuje pliki, ZIP test client zwraca 200 z application/zip, cleanup OK
- [ ] 3 atomic commity, git status clean, push do origin/main
- [ ] Deploy na panel84.mydevil.net: git HEAD = local HEAD, pip install OK, collectstatic OK, migrate OK, check OK
- [ ] Smoke prod: Pillow + fonty + StoryRenderer.render zwracaja PNG bytes
- [ ] Smoke prod HTTP: /admin/login/ → 200
- [ ] NIE odpalono `generate_story_images` na prod (user zrobi sam)
- [ ] NIE odpalono `run_weekly_research` (zero AI API calls)
- [ ] NIE zmodyfikowano WeeklyResearch model, BlogPost model, run_weekly_research.py

</success_criteria>

<output>
After completion, create `.planning/quick/260603-aou-grafiki-ig-stories-png-1080x1920-przez-p/260603-aou-SUMMARY.md`
with:
- What was built (services layer, fonts, renderer, CLI command, admin action, ZIP view, template updates, CSS, README)
- 3 commit hashes
- Deploy status (HEAD on server, smoke prod results)
- NotoColorEmoji.ttf status (bundled / fallback to text)
- Known limitations (no auto-regenerate on save, no watermark, no per-slide manual edit)
- Quick win: command to test from CLI on prod
</output>
