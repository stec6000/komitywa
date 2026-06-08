---
phase: quick-260608-kke
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - content/management/commands/run_weekly_research.py
  - .planning/quick/260602-i1r-nowy-app-content-z-weekly-research-pipel/PROMPTS-VERBATIM.md
  - content/models.py
  - content/migrations/0003_storyslide.py
  - content/services/ai_prompts.py
  - content/services/story_renderer.py
  - content/admin.py
  - content/templates/admin/content/weeklyresearch/_preview.html
  - content/management/commands/generate_story_images.py
autonomous: true
requirements: [IGS-FORMAT, IGS-MODEL, IGS-PROMPT, IGS-RENDER, IGS-ADMIN, IGS-PREVIEW, IGS-CLI]
user_setup: []

must_haves:
  truths:
    - "FORMAT_PROMPT schemat instagram_stories to {slide_type, headline, subtext, bg_color, visual_hint} — bez 'text' i bez 'emoji'"
    - "Operator moze zmaterializowac formatted_json['instagram_stories'] do wierszy StorySlide jedna akcja admina (idempotentnie)"
    - "Operator moze wgrac wlasne zdjecie tla per slajd przez ImageField w adminie"
    - "StoryRenderer renderuje PNG 1080x1920 z layoutem A (zdjecie cover-crop + gradient scrim + headline+subtext bialym tekstem u dolu) gdy jest background_image"
    - "StoryRenderer renderuje fallback PNG 1080x1920 (bg_color + headline + subtext) gdy brak zdjecia — bez wyjatku"
    - "Admin pokazuje gotowy AI-prompt z build_story_image_prompt(visual_hint) z przyciskiem Kopiuj"
    - "CLI generate_story_images --week renderuje z wierszy StorySlide (nie z surowego JSON)"
  artifacts:
    - path: "content/models.py"
      provides: "Model StorySlide (FK research related_name=story_slides, order, slide_type, headline, subtext, bg_color, visual_hint, background_image, timestamps)"
      contains: "class StorySlide"
    - path: "content/migrations/0003_storyslide.py"
      provides: "Migracja tworzaca tabele StorySlide"
      contains: "StorySlide"
    - path: "content/services/ai_prompts.py"
      provides: "build_story_image_prompt(visual_hint) z pionowym sufiksem 9:16"
      contains: "def build_story_image_prompt"
    - path: "content/services/story_renderer.py"
      provides: "render() obslugujacy dict i StorySlide, layout A + fallback, bez emoji"
      contains: "def _load_background"
    - path: "content/admin.py"
      provides: "promote_to_story_slides + StorySlideAdmin + inline + akcja Generuj PNG"
      contains: "class StorySlideAdmin"
    - path: "content/templates/admin/content/weeklyresearch/_preview.html"
      provides: "Zakladka Stories: headline+subtext, AI-prompt z Kopiuj, miniatura"
      contains: "headline"
    - path: "content/management/commands/generate_story_images.py"
      provides: "CLI renderujacy z wierszy StorySlide danego --week"
      contains: "story_slides"
  key_links:
    - from: "content/admin.py::promote_to_story_slides"
      to: "WeeklyResearch.formatted_json['instagram_stories']"
      via: "iteracja + StorySlide.objects.create"
      pattern: "instagram_stories"
    - from: "content/admin.py::StorySlideAdmin"
      to: "content/services/ai_prompts.py::build_story_image_prompt"
      via: "readonly pole z promptem"
      pattern: "build_story_image_prompt"
    - from: "content/services/story_renderer.py::render"
      to: "StorySlide.background_image"
      via: "PIL Image.open(cover-crop) + gradient scrim"
      pattern: "background_image"
    - from: "content/management/commands/generate_story_images.py"
      to: "WeeklyResearch.story_slides"
      via: "wr.story_slides.all() zamiast formatted_json"
      pattern: "story_slides"
---

<objective>
Realizuje DOKLADNIE design `docs/superpowers/specs/2026-06-08-ig-stories-enhancement-design.md` (kierunek A): IG Stories ze zdjeciem tla + bogatszym tekstem (headline+subtext), z recznym uploadem zdjecia per slajd i gotowym AI-promptem do skopiowania. Slajdy materializowane jako wiersze modelu `StorySlide` (wzorzec `BlogPost`).

Purpose: Obecne stories to plaski kolor + emoji + jedno zdanie — efekt ubogi. Cel: edytowalne slajdy ze zdjeciem i tekstem, PNG 1080x1920 zawsze powstaje (layout A lub fallback).
Output: Nowy schemat FORMAT_PROMPT, model StorySlide + migracja, rozbudowany StoryRenderer (layout A + fallback), build_story_image_prompt, admin (promote + StorySlideAdmin + inline), preview, CLI przestawione na StorySlide.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@docs/superpowers/specs/2026-06-08-ig-stories-enhancement-design.md
@CLAUDE.md
@content/models.py
@content/admin.py
@content/services/story_renderer.py
@content/services/ai_prompts.py
@content/services/colors.py
@content/management/commands/run_weekly_research.py
@content/management/commands/generate_story_images.py
@content/templates/admin/content/weeklyresearch/_preview.html

<notes>
- `python` NIE jest w PATH. Uzywaj `.venv/bin/python`.
- Brak pytest — weryfikacja przez `manage.py check`, `makemigrations --check`, inline smoke testy (`.venv/bin/python manage.py shell -c "..."`).
- Pillow 12.2.0 dostepny w .venv. Fonty NotoSans-Regular/Bold w `content/fonts/`.
- Media JUZ servowane lokalnie: `backend/urls.py` ma `static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` w bloku `if settings.DEBUG`. MEDIA_ROOT = `public/media`, MEDIA_URL = `/media/`. Upload `background_image` (upload_to="weekly_research/story_uploads/%Y/%m/") oraz miniatury PNG beda dostepne — BRAK potrzeby zmian w urls.py.
- Konwencje (CLAUDE.md): double quotes, snake_case, @admin.register, @admin.action(description=...), get_user_model gdy User, __str__ na modelach, BigAutoField default.
- Migracja: numeruj auto przez `makemigrations content` (poprzednie 0001/0002 — sprawdz `ls content/migrations/`; spodziewane 0003).
- StorySlideAdmin akcja "Generuj PNG" oraz promote — wzoruj sie na istniejacym `generate_story_images_action` i `promote_to_blogpost` (idempotencja przez `.exists()`).
- Przycisk "Kopiuj" — wzorzec JS data-copy-text z _preview.html (klasa kk-copy-btn juz ma handler globalny w preview; w StorySlideAdmin trzeba minimalny inline JS clipboard).
- admin.py JUZ importuje (sprawdz przed edycja): `from content.services.ai_prompts import AI_IMAGE_BRAND_SUFFIX` (~linia 7) oraz `from .models import BlogPost, WeeklyResearch` (~linia 10). Rozszerzaj te istniejace linie zamiast dodawac nowe (patrz Task 4).
</notes>
</context>

<tasks>

<task type="auto">
  <name>Task 1: FORMAT_PROMPT nowy schemat stories + aktualizacja PROMPTS-VERBATIM.md</name>
  <files>content/management/commands/run_weekly_research.py, .planning/quick/260602-i1r-nowy-app-content-z-weekly-research-pipel/PROMPTS-VERBATIM.md</files>
  <action>
W `run_weekly_research.py` zmien BLOK `instagram_stories` w `FORMAT_PROMPT`:
- Schemat JSON (linia ~67-69): z
  `{{"slide_type": "hook|fact|tip|cta", "text": "...", "bg_color": "#hex", "emoji": "..."}}`
  na
  `{{"slide_type": "hook|fact|tip|cta", "headline": "...", "subtext": "...", "bg_color": "#hex", "visual_hint": "..."}}`
- Wytyczna INSTAGRAM STORIES (linia ~82-85): zastap aktualny opis nowym. Wymagania ze speca:
  - 6-7 slajdow, luk: 1x hook -> 3-4x fact/tip -> 1x cta
  - kazdy slajd ma `headline` (mocny naglowek, <=55 znakow) i `subtext` (rozwiniecie 1-2 zdania, <=150 znakow)
  - `visual_hint`: konkretny opis kadru (jak w postach) — zasila AI-prompt do zdjecia tla
  - `bg_color` z palety marki (zostaje jako fallback): #f3ead7, #6b7a3a, #b6562e, #c89a3a, #2a2420
  - BEZ emoji (usun zdanie "Dobierz pasujacy emoji do kazdego slajdu")
  Zachowaj polski jezyk i ton wytycznej spojny z reszta promptu.

Zaktualizuj `PROMPTS-VERBATIM.md` (sciezka: `.planning/quick/260602-i1r-nowy-app-content-z-weekly-research-pipel/PROMPTS-VERBATIM.md`):
- linie ~73-74 (schemat instagram_stories) i ~91 (wytyczna emoji) tak, by odzwierciedlaly nowy schemat — identycznie jak w FORMAT_PROMPT.
- Dodaj na gorze sekcji stories krotka adnotacje (1 linia komentarza markdown), np.:
  `> Zmieniono 2026-06-08 (quick 260608-kke): schemat stories headline+subtext+visual_hint, bez emoji. Swiadoma ewolucja VERBATIM — patrz spec ig-stories-enhancement-design.md.`
To swiadoma zmiana "verbatim" — zrodlo prawdy ma sie nie rozjechac z FORMAT_PROMPT.

NIE ruszaj `JSON_STRICTNESS_ADDENDUM` ani `RESEARCH_PROMPT`.
  </action>
  <verify>
<automated>cd /home/tomo/workspace/komitywa && .venv/bin/python -c "
src = open('content/management/commands/run_weekly_research.py').read()
# Izoluj DOKLADNIE blok schematu instagram_stories: od pierwszego wystapienia
# klucza 'instagram_stories' do nastepnego klucza najwyzszego poziomu lub konca obiektu.
after = src.split('instagram_stories', 1)[1]
# Blok pojedynczego slajdu konczy sie na zamknieciu listy/obiektu — wystarczy
# do najblizszego ']' (koniec listy stories) lub 600 znakow jako bezpiecznik.
end = after.find(']')
block = after[: end if 0 < end < 600 else 600]
# Nowy schemat MUSI byc obecny w bloku stories:
assert 'headline' in block and 'subtext' in block and 'visual_hint' in block, 'brak headline/subtext/visual_hint w bloku stories'
# Stare quoted-keys NIE moga juz wystepowac w bloku schematu stories:
assert '\"text\"' not in block, 'stary klucz \"text\" wciaz w schemacie stories'
assert '\"emoji\"' not in block, 'stary klucz \"emoji\" wciaz w schemacie stories'
# Defensywnie: slowo emoji w jakiejkolwiek formie nie powinno wystapic w bloku stories
assert 'emoji' not in block.lower(), 'emoji nadal wystepuje w bloku stories'
print('FORMAT_PROMPT OK')
"</automated>
  </verify>
  <done>FORMAT_PROMPT ma schemat stories z headline/subtext/visual_hint, a quoted-keys "text" i "emoji" NIE wystepuja w bloku schematu stories. PROMPTS-VERBATIM.md zaktualizowany z adnotacja o swiadomej zmianie. RESEARCH_PROMPT i JSON_STRICTNESS_ADDENDUM nietkniete.</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Model StorySlide + migracja + build_story_image_prompt</name>
  <files>content/models.py, content/migrations/0003_storyslide.py, content/services/ai_prompts.py</files>
  <behavior>
    - StorySlide(research=wr, order=1, slide_type="hook", headline="X", subtext="Y", bg_color="#6b7a3a") zapisuje sie poprawnie
    - unique_together (research, order) — drugi slajd z tym samym (research, order) rzuca IntegrityError
    - StorySlide bez background_image jest valid (blank=True)
    - build_story_image_prompt("ciasto na stole") zawiera "ciasto na stole" ORAZ "1080x1920" ORAZ "9:16"
    - build_story_image_prompt("") zwraca sam sufiks brandowy (nie crashuje)
  </behavior>
  <action>
W `content/models.py` dodaj model `StorySlide` (po BlogPost, na koncu pliku). Pola dokladnie wg speca (tabela komponent 2):
- `research = models.ForeignKey(WeeklyResearch, on_delete=models.CASCADE, related_name="story_slides")`
- `order = models.PositiveIntegerField(help_text="Kolejnosc slajdu (1-based).")`
- `slide_type = models.CharField(max_length=20, help_text="hook/fact/tip/cta")`
- `headline = models.CharField(max_length=90, help_text="Twardy bezpiecznik DB; cel redakcyjny <=55 znakow.")`
- `subtext = models.TextField(blank=True, default="")`
- `bg_color = models.CharField(max_length=9, default="#f3ead7", help_text="Hex, fallback gdy brak zdjecia.")`
- `visual_hint = models.TextField(blank=True, default="", help_text="Opis kadru -> zasila AI-prompt.")`
- `background_image = models.ImageField(upload_to="weekly_research/story_uploads/%Y/%m/", blank=True, null=True, help_text="Wgrane zdjecie tla (layout A).")`
- `created_at = models.DateTimeField(auto_now_add=True)`
- `updated_at = models.DateTimeField(auto_now=True)`
Meta: `verbose_name="Story slide"`, `verbose_name_plural="Story slides"`, `ordering = ["research", "order"]`, `unique_together = ("research", "order")`.
`__str__`: `return f"{self.research.week_label} #{self.order} ({self.slide_type})"`.
UWAGA: `ImageField` wymaga Pillow (jest, 12.2.0). Uzyj `null=True` na ImageField (Django zaleca null+blank dla file fields, by puste = NULL zamiast "").

W `content/services/ai_prompts.py` dodaj `build_story_image_prompt(visual_hint: str) -> str`:
- Zdefiniuj nowa stala `AI_STORY_BRAND_SUFFIX` — sufiks PIONOWY (analogicznie do AI_IMAGE_BRAND_SUFFIX, ale 9:16). Tresc PL, ten sam klimat marki + dopisek pionowy. Przyklad:
  ```
  AI_STORY_BRAND_SUFFIX = (
      "\n\n"
      "Styl: rzemieslnicza fotografia kulinarna, naturalne swiatlo, "
      "cieple tony, autentyczna kompozycja, klimat domowej weganskiej "
      "piekarni z Bialegostoku. Vertical 9:16, 1080x1920, photorealistic, "
      "no text overlay, kompozycja zostawiajaca miejsce na tekst u dolu kadru."
  )
  ```
- `build_story_image_prompt` analogiczne do `build_ai_image_prompt`: `hint = (visual_hint or "").strip(); return f"{hint}{AI_STORY_BRAND_SUFFIX}"`.
- NIE ruszaj istniejacego AI_IMAGE_BRAND_SUFFIX ani build_ai_image_prompt.

Wygeneruj migracje: `cd /home/tomo/workspace/komitywa && .venv/bin/python manage.py makemigrations content`. Plik powinien dostac numer 0003 (sprawdz `ls content/migrations/`). Jesli numer inny — zaktualizuj wpis `files_modified` w glowie planu mentalnie, ale plik nazwany przez Django jest poprawny.
  </action>
  <verify>
<automated>cd /home/tomo/workspace/komitywa && .venv/bin/python manage.py makemigrations content --check --dry-run && .venv/bin/python manage.py check && .venv/bin/python -c "import django,os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings'); django.setup(); from content.services.ai_prompts import build_story_image_prompt as b; p=b('ciasto na stole'); assert 'ciasto na stole' in p and '1080x1920' in p and '9:16' in p, p; assert b('').strip().startswith('Styl'), 'pusty hint zle'; from content.models import StorySlide; print('OK', StorySlide._meta.unique_together)"</automated>
  </verify>
  <done>Model StorySlide istnieje z polami wg speca, migracja 0003 wygenerowana, `makemigrations --check` czyste, `manage.py check` przechodzi. build_story_image_prompt zwraca hint + pionowy sufiks (zawiera 9:16 i 1080x1920); pusty hint nie crashuje. unique_together=(("research","order"),).</done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: StoryRenderer — layout A (zdjecie + gradient scrim) + fallback, bez emoji</name>
  <files>content/services/story_renderer.py</files>
  <behavior>
    - render(slide) przyjmuje ZAROWNO dict {headline, subtext, bg_color, slide_type, background_image?} JAK I obiekt StorySlide (duck-typing/adapter) — zdecyduj: adapter wewnetrzny normalizujacy oba do dict-a z polami headline/subtext/bg_color/slide_type/background_image_path
    - Smoke A: render z testowym zdjeciem (PIL Image w pamieci -> zapisane do tmp -> sciezka jako background_image) zwraca PNG, rozmiar dekodowany przez PIL == (1080, 1920)
    - Smoke fallback: render bez zdjecia (background_image=None) zwraca PNG 1080x1920 bez wyjatku
    - eyebrow: slide_type "hook" -> "NA POCZATEK", "fact" -> "CIEKAWOSTKA", "tip" -> "WSKAZOWKA", "cta" -> "OD NAS"
  </behavior>
  <action>
Przebuduj `StoryRenderer.render`. USUN CALKOWICIE stary tryb emoji + jedno-zdaniowy text. Konkretnie do usuniecia (jawnie, nie zostawiaj martwego kodu):
- inicjalizacja `self._font_emoji` w `__init__` (oraz wszelkie pomocnicze ladowanie fontu emoji)
- stala/atrybut sciezki fontu emoji `FONT_PATH_EMOJI` (jesli istnieje na poziomie modulu lub klasy)
- caly blok rysowania emoji w render (draw emoji glyph / `slide.get("emoji")`)
- uzycie `slide.get("text")` jako jedyne zrodlo tekstu
Po usunieciu w pliku NIE moze juz wystepowac identyfikator `_font_emoji`, `FONT_PATH_EMOJI`, ani odwolanie do klucza `emoji` slajdu.
Zachowaj `CANVAS_SIZE=(1080,1920)`, `_parse_hex`, sciezki fontow regular/bold, `render_to_file`.

1. Adapter wejscia — dodaj `_normalize(slide)` zwracajacy dict:
   - jesli `slide` to dict: czytaj klucze headline/subtext/bg_color/slide_type; background_image_path = slide.get("background_image") (str sciezki lub None)
   - jesli obiekt (np. StorySlide): `getattr(slide, "headline", "")` itd.; background_image_path = `slide.background_image.path` jesli `getattr(slide, "background_image", None)` ma wartosc (try/except — pole moze byc puste), inaczej None
   Zwroc {"headline", "subtext", "bg_color", "slide_type", "bg_path"}.

2. Stale layoutu (nadpisz/dodaj): blok zakotwiczony u dolu.
   - `SLIDE_TYPE_PL = {"hook": "NA POCZATEK", "fact": "CIEKAWOSTKA", "tip": "WSKAZOWKA", "cta": "OD NAS"}` (uzyj polskich znakow: "NA POCZĄTEK", "WSKAZÓWKA")
   - rozmiary fontow: eyebrow ~40, headline bold ~76, subtext regular ~46 (dopasuj by miescilo sie w marginesie ~80px po bokach)
   - `MARGIN_X = 80`, blok tekstu zaczyna sie od dolu (anchor bottom): policz wysokosc bloku i ustaw y tak, by dolna krawedz byla ~120px od dolu kadru.

3. Layout A (bg_path istnieje i plik sie otwiera):
   - `bg = Image.open(bg_path).convert("RGB")` w try/except; przy bledzie -> fallback (izolacja per slajd).
   - cover-crop do 1080x1920: skaluj zachowujac proporcje by WYPELNIC kadr (scale = max(1080/w, 1920/h)), potem center-crop do dokladnie (1080,1920).
   - gradient scrim: stworz warstwe RGBA (1080,1920) przezroczysta u gory, ciemniejaca ku dolowi. Dolne ~45% kadru: alpha rosnie liniowo od 0 do ~217 (~85%). Zaimplementuj petla po wierszach (range) rysujac poziome linie z rosnacym alpha, lub buduj maske przez `Image.new("L")` + numpy-free petla. Skomponuj: `img = Image.alpha_composite(bg.convert("RGBA"), scrim).convert("RGB")`.
   - tekst BIALY (255,255,255) — scrim zapewnia kontrast. eyebrow lekko przygaszony bialy (np. 230,230,230) z letter-spacing (jak istniejacy " ".join(list(label))).

4. Fallback (brak bg_path lub blad otwarcia):
   - `img = Image.new("RGB", CANVAS_SIZE, _parse_hex(bg_color))`
   - kolor tekstu z `text_color_for_bg(bg_color)` (import juz jest).
   - ten sam uklad: eyebrow -> headline (bold wrap) -> subtext (regular wrap), zakotwiczone u dolu.

5. Wrap tekstu: uzyj `textwrap.wrap` z szerokoscia w znakach dobrana do fontu (headline ~22-24 zn/linia przy 76px, subtext ~34-38 zn/linia przy 46px) LUB zmierz przez draw.textlength i lam recznie. Wystarczy textwrap z empirycznym width. Subtext: limit ~4 linii (przytnij reszta + "…") by nie wyjsc poza kadr.

6. Helper rysujacy blok tekstu (wspolny dla A i fallback): przyjmuje draw, eyebrow, headline, subtext, fill_color, dim_eyebrow_color, anchor_bottom_y. Centrowanie poziome kazdej linii (jak istniejacy kod liczy lw przez textbbox).

Zachowaj `render(self, slide)` sygnature (slide: dict | StorySlide) i `render_to_file(self, slide, path)`.
  </action>
  <verify>
<automated>cd /home/tomo/workspace/komitywa && .venv/bin/python -c "
import django,os,tempfile; os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings'); django.setup()
from io import BytesIO; from PIL import Image
from content.services.story_renderer import StoryRenderer
r=StoryRenderer()
# fallback (dict, brak zdjecia)
png=r.render({'headline':'Aquafaba zamiast jajek','subtext':'Woda z cieciorki ubita na sztywno zastapi biala pianke w bezach.','bg_color':'#6b7a3a','slide_type':'tip'})
im=Image.open(BytesIO(png)); assert im.size==(1080,1920), im.size
# layout A (zdjecie testowe w tmp)
tf=tempfile.NamedTemporaryFile(suffix='.jpg',delete=False); Image.new('RGB',(1600,900),(120,80,40)).save(tf.name); tf.close()
png2=r.render({'headline':'Sezon na rabarbar','subtext':'Kwasny, rozowy, idealny do wegańskiego ciasta.','bg_color':'#b6562e','slide_type':'hook','background_image':tf.name})
im2=Image.open(BytesIO(png2)); assert im2.size==(1080,1920), im2.size
# stary tryb emoji MUSI byc usuniety — sensowne asercje na nieobecnosc identyfikatorow:
src=open('content/services/story_renderer.py').read()
assert '_font_emoji' not in src, 'pozostal _font_emoji'
assert 'FONT_PATH_EMOJI' not in src, 'pozostala stala FONT_PATH_EMOJI'
assert 'slide.get(\"emoji\")' not in src and \".get('emoji')\" not in src, 'pozostalo odwolanie do klucza emoji slajdu'
assert 'NA POCZ' in src, 'brak PL eyebrow'
print('RENDER OK fallback+layoutA, emoji usuniety')
"</automated>
  </verify>
  <done>render() przyjmuje dict i StorySlide. Layout A: zdjecie cover-crop 1080x1920 + gradient scrim u dolu + bialy headline/subtext/eyebrow. Fallback: bg_color + headline/subtext, kolor z text_color_for_bg. Oba zwracaja PNG 1080x1920. Stary tryb emoji usuniety w calosci: brak `_font_emoji`, `FONT_PATH_EMOJI` i odwolan do klucza `emoji` w pliku. PL eyebrow mapping obecny.</done>
</task>

<task type="auto" tdd="false">
  <name>Task 4: Admin — promote_to_story_slides + StorySlideAdmin + inline + Generuj PNG</name>
  <files>content/admin.py</files>
  <behavior>
    - promote_to_story_slides na WR z formatted_json['instagram_stories'] (nowy schemat) tworzy N wierszy StorySlide z headline/subtext/bg_color/visual_hint/slide_type/order
    - Idempotencja: drugie wywolanie na tym samym WR (research.story_slides.exists()) -> skip
    - Fallback stary JSON: slajd ma 'text' zamiast 'headline' -> headline=text[:90], subtext="", visual_hint=""
    - StorySlideAdmin readonly pole ai_prompt_display zawiera wynik build_story_image_prompt(obj.visual_hint)
  </behavior>
  <action>
W `content/admin.py`:

1. Importy — ROZSZERZ ISTNIEJACE linie, NIE dodawaj duplikatow:
   - admin.py JUZ ma `from content.services.ai_prompts import AI_IMAGE_BRAND_SUFFIX` (~linia 7) — rozszerz te linie do `from content.services.ai_prompts import AI_IMAGE_BRAND_SUFFIX, AI_STORY_BRAND_SUFFIX, build_story_image_prompt` (AI_STORY_BRAND_SUFFIX bedzie potrzebny w Task 5 dla change_view; dodaj go juz teraz lub w Task 5 — wystarczy build_story_image_prompt tutaj).
   - admin.py JUZ ma `from .models import BlogPost, WeeklyResearch` (~linia 10) — rozszerz te linie do `from .models import BlogPost, StorySlide, WeeklyResearch`.
   - `from django.utils.html import format_html` — dodaj TYLKO jesli jeszcze nie ma (sprawdz gora pliku; jesli istnieje, nie duplikuj).

2. Akcja `@admin.action(description="Promuj stories do StorySlide")` `promote_to_story_slides(modeladmin, request, queryset)` — wzoruj na `promote_to_blogpost`:
   - per research: jesli `research.story_slides.exists()` -> skipped += 1, continue (idempotencja).
   - `stories = (research.formatted_json or {}).get("instagram_stories") or []`; brak -> warning/skip.
   - per slajd z `enumerate(stories, start=1)`:
     - `headline = (slide.get("headline") or slide.get("text") or "").strip()[:90]` (fallback stary schemat)
     - `subtext = (slide.get("subtext") or "").strip()`
     - `bg_color = (slide.get("bg_color") or "#f3ead7").strip()`
     - `visual_hint = (slide.get("visual_hint") or "").strip()`
     - `slide_type = (slide.get("slide_type") or "").strip()[:20]`
     - jesli brak headline -> pomin ten slajd (defensywnie), zlicz w failed
     - `StorySlide.objects.create(research=research, order=idx, slide_type=slide_type, headline=headline, subtext=subtext, bg_color=bg_color[:9], visual_hint=visual_hint)`
   - komunikaty messages.success/info/warning analogicznie do promote_to_blogpost (utworzono / pominieto idempotentnie / brak danych).

3. Akcja `@admin.action(description="Generuj PNG (1080x1920)")` `generate_story_slide_pngs(modeladmin, request, queryset)` na StorySlideAdmin — renderuje zaznaczone StorySlide:
   - `renderer = StoryRenderer()`
   - per slajd: out path = `Path(settings.MEDIA_ROOT)/"weekly_research"/slide.research.week_label/"stories"/f"{slide.order:02d}_{(slide.slide_type or 'slide').lower().replace(' ','_')}.png"`
   - `renderer.render_to_file(slide, path)` (renderer juz przyjmuje obiekt StorySlide z Task 3). try/except per slajd -> messages.warning, reszta leci dalej (izolacja).
   - sukces: messages.success z liczba.

4. `StorySlideInline` (readonly inline na WeeklyResearchAdmin):
   ```
   class StorySlideInline(admin.TabularInline):
       model = StorySlide
       extra = 0
       fields = ("order", "slide_type", "headline", "bg_color", "background_image")
       readonly_fields = fields
       can_delete = False
       show_change_link = True
       def has_add_permission(self, request, obj=None): return False
   ```
   Dodaj `inlines = [StorySlideInline]` i `promote_to_story_slides` do `actions` na WeeklyResearchAdmin (obok promote_to_blogpost, generate_story_images_action).

5. `@admin.register(StorySlide)` `StorySlideAdmin`:
   - `list_display = ("research", "order", "slide_type", "headline", "has_image")`
   - `list_filter = ("research", "slide_type")`
   - `ordering = ("research", "order")`
   - `fields = ("research", "order", "slide_type", "headline", "subtext", "bg_color", "visual_hint", "background_image", "ai_prompt_display", "created_at", "updated_at")`
   - `readonly_fields = ("ai_prompt_display", "created_at", "updated_at")`
   - `actions = [generate_story_slide_pngs]`
   - metoda `has_image(self, obj)` -> bool (boolean=True) `return bool(obj.background_image)`
   - metoda `ai_prompt_display(self, obj)`:
     ```
     prompt = build_story_image_prompt(obj.visual_hint or "")
     # readonly pole z <pre> + przycisk Kopiuj (inline JS clipboard)
     return format_html(
         '<div><pre style="white-space:pre-wrap;...">{}</pre>'
         '<button type="button" onclick="navigator.clipboard.writeText(this.previousElementSibling.textContent)">Kopiuj prompt AI</button></div>',
         prompt,
     )
     ai_prompt_display.short_description = "AI-prompt do zdjecia tla"
     ```
     (Inline onclick z navigator.clipboard — prosty, bez zaleznosci od preview JS.)

NIE ruszaj istniejacego `generate_story_images_action` (zostaje na WR dla kompat. — choc Task 5 przestawia CLI; akcja moze zostac jako legacy lub usun jesli czysciej — ZOSTAW, niskie ryzyko). Zachowaj BlogPostAdmin i jego akcje bez zmian.
  </action>
  <verify>
<automated>cd /home/tomo/workspace/komitywa && .venv/bin/python manage.py check && .venv/bin/python -c "
import django,os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings'); django.setup()
from django.contrib import admin as dadmin
from content.models import StorySlide, WeeklyResearch
assert StorySlide in dadmin.site._registry, 'StorySlideAdmin nie zarejestrowany'
from content.admin import promote_to_story_slides, StorySlideAdmin, StorySlideInline
sa=dadmin.site._registry[StorySlide]
# ai_prompt_display dziala na dummy obiekcie
class Dummy: visual_hint='ciasto na stole'
html=sa.ai_prompt_display(Dummy()); assert 'ciasto na stole' in str(html) and '1080x1920' in str(html), str(html)[:200]
wra=dadmin.site._registry[WeeklyResearch]
assert any(getattr(a,'__name__','')=='promote_to_story_slides' for a in wra.actions), 'promote brak w WR actions'
# Django przechowuje klasy inline w .inlines:
assert StorySlideInline in wra.inlines, 'StorySlideInline brak w WeeklyResearchAdmin.inlines'
print('ADMIN OK')
"</automated>
  </verify>
  <done>promote_to_story_slides tworzy wiersze StorySlide z nowego schematu (fallback text->headline dla starego), idempotentne przez story_slides.exists(). StorySlideAdmin zarejestrowany z uploadem background_image, readonly ai_prompt_display (build_story_image_prompt + przycisk Kopiuj) i akcja Generuj PNG. StorySlideInline readonly na WeeklyResearchAdmin (klasa obecna w .inlines). Importy ai_prompts i .models rozszerzone bez duplikatu linii. manage.py check czysty.</done>
</task>

<task type="auto" tdd="false">
  <name>Task 5: Preview zakladka Stories (headline+subtext+AI-prompt+miniatura) + CLI na StorySlide</name>
  <files>content/templates/admin/content/weeklyresearch/_preview.html, content/management/commands/generate_story_images.py</files>
  <action>
A) `_preview.html` — przebuduj zakladke Stories (sekcja `kk-panel-stories`, linie ~87-156). Zrodlo danych preview to nadal `data.instagram_stories` (surowy JSON z formatted_json), ale nowy schemat ma `headline`/`subtext`/`visual_hint` zamiast `text`/`emoji`:
   - Dla kazdego slajdu `s` pokaz: `s.headline` (mocno), `s.subtext` (mniejsze), chip `s.slide_type`, swatch `s.bg_color`.
   - USUN `s.emoji` i zamien `s.text` -> `s.headline` (+ dodaj `s.subtext`). Kompat. wsteczna: stary JSON ma `s.text` — uzyj `{{ s.headline|default:s.text }}` by stare researche tez sie renderowaly.
   - AI-prompt: dodaj blok jak w POSTS — `{% if ai_image_brand_suffix %}` jest dla postow; dla stories potrzebny PIONOWY sufiks. Przekaz nowy kontekst z admina LUB renderuj prompt inline. NAJPROSTSZE: w `change_view` (admin) dodaj `extra_context["ai_story_brand_suffix"] = AI_STORY_BRAND_SUFFIX` (import z ai_prompts — w Task 4 rozszerzylismy import o AI_STORY_BRAND_SUFFIX; jesli nie, dodaj go teraz do istniejacej linii ai_prompts) — i w template: `{% with sp=s.visual_hint|stringformat:"s"|add:ai_story_brand_suffix %}<pre>{{ sp }}</pre><button class="kk-copy-btn" data-copy-text="{{ sp }}">Skopiuj prompt AI</button>{% endwith %}` (klasa kk-copy-btn ma juz handler w preview).
     -> WYMAGA male dotkniecie `content/admin.py` change_view WeeklyResearchAdmin: dodaj linie extra_context z AI_STORY_BRAND_SUFFIX. (To jedyna dodatkowa edycja admin.py w tym tasku — dozwolone, plik juz w files_modified planu.)
   - Miniatura: sekcja `stories_files` (wygenerowane PNG) zostaje BEZ ZMIAN — to dalej dziala (PNG na dysku). Dodatkowo jesli chcesz miniature wgranego background_image: link do StorySlideAdmin. Minimalnie: dodaj pod kazdym slajdem link "edytuj / wgraj zdjecie" do changelist StorySlide: `<a href="{% url 'admin:content_storyslide_changelist' %}?research__id__exact={{ original.pk }}">Edytuj slajdy / wgraj zdjecia</a>` (jeden link na panel wystarczy).
   - Bulk copy na dole: zmien z `{{ s.emoji }} {{ s.text }}` na `{{ s.headline }} — {{ s.subtext }}`.

B) `generate_story_images.py` — przestaw render na wiersze StorySlide:
   - Po ustaleniu `wr` (logika --week/--latest zostaje): zamiast `stories = wr.formatted_json.get("instagram_stories")`, uzyj `slides = list(wr.story_slides.all())` (ordering przez Meta ["research","order"]).
   - Jesli `not slides`: `CommandError(f"WR {wr.week_label}: brak StorySlide — najpierw 'Promuj stories do StorySlide' w adminie")`.
   - Petla: dla kazdego `slide` (obiekt StorySlide):
     - `slide_type = (slide.slide_type or f"slide{slide.order}").lower().replace(" ", "_")`
     - `filename = f"{slide.order:02d}_{slide_type}.png"` (ZACHOWAJ format sciezki MEDIA/weekly_research/<week>/stories/<NN>_<slide_type>.png)
     - `path = out_dir / filename`; `if path.exists() and not force: skip`
     - `renderer.render_to_file(slide, path)` (renderer przyjmuje obiekt StorySlide z Task 3)
   - Zachowaj `--force`, `--week`, `--latest`, komunikaty stdout (generated/skipped/total).
   - Usun zaleznosc od `formatted_json.get("instagram_stories")` w tej komendzie.
  </action>
  <verify>
<automated>cd /home/tomo/workspace/komitywa && .venv/bin/python manage.py check && .venv/bin/python -c "
src=open('content/management/commands/generate_story_images.py').read()
assert 'story_slides' in src, 'CLI nie uzywa story_slides'
assert 'slide.order' in src and 'slide.slide_type' in src, 'CLI nie iteruje po obiektach StorySlide'
tpl=open('content/templates/admin/content/weeklyresearch/_preview.html').read()
assert 's.headline' in tpl and 's.subtext' in tpl, 'preview brak headline/subtext'
adm=open('content/admin.py').read()
assert 'AI_STORY_BRAND_SUFFIX' in adm and 'ai_story_brand_suffix' in adm, 'admin nie przekazuje ai_story_brand_suffix'
print('PREVIEW+CLI OK')
" && .venv/bin/python manage.py generate_story_images --help >/dev/null && echo "CLI help OK"</automated>
  </verify>
  <done>Preview zakladka Stories pokazuje headline+subtext (fallback s.text dla starego JSON), AI-prompt stories z pionowym sufiksem + przycisk Kopiuj, link do StorySlideAdmin. CLI generate_story_images renderuje z wr.story_slides (obiekty StorySlide), zachowuje --force i sciezke PNG MEDIA/weekly_research/<week>/stories/<NN>_<slide_type>.png. manage.py check czysty.</done>
</task>

</tasks>

<verification>
Po wszystkich taskach (uruchom z `/home/tomo/workspace/komitywa`):
- `.venv/bin/python manage.py check` — czysto
- `.venv/bin/python manage.py makemigrations --check --dry-run` — brak niezaaplikowanych zmian (migracja 0003 obecna)
- Smoke render (Task 3 verify) — layout A + fallback zwracaja PNG 1080x1920
- Smoke promote idempotencja + fallback text->headline (mozna doweryfikowac na shell z dummy WR jesli istnieje formatted_json w bazie)
- FORMAT_PROMPT i PROMPTS-VERBATIM.md spojne (headline/subtext/visual_hint, bez emoji)
</verification>

<success_criteria>
1. FORMAT_PROMPT generuje schemat {slide_type, headline, subtext, bg_color, visual_hint}, bez emoji; PROMPTS-VERBATIM.md zsynchronizowany z adnotacja o swiadomej zmianie.
2. Model StorySlide + migracja 0003; pola, Meta (ordering, unique_together), __str__ wg speca.
3. build_story_image_prompt(visual_hint) zwraca hint + pionowy sufiks (9:16, 1080x1920, no text overlay).
4. StoryRenderer: layout A (zdjecie cover-crop + gradient scrim + bialy headline/subtext/eyebrow) gdy jest background_image; fallback (bg_color + tekst z text_color_for_bg) bez zdjecia; render() przyjmuje dict i StorySlide; stary tryb emoji usuniety; PNG zawsze 1080x1920.
5. Admin: promote_to_story_slides (idempotentne, fallback text->headline), StorySlideAdmin (upload, readonly AI-prompt + Kopiuj, akcja Generuj PNG), readonly StorySlideInline na WeeklyResearchAdmin.
6. Preview Stories: headline+subtext, AI-prompt z Kopiuj, link do StorySlideAdmin, miniatury PNG.
7. CLI generate_story_images renderuje z wierszy StorySlide danego --week; --force i sciezka PNG bez zmian.
</success_criteria>

<output>
Po ukonczeniu utworz `.planning/quick/260608-kke-ulepszone-ig-stories-model-storyslide-up/260608-kke-SUMMARY.md`.
</output>
