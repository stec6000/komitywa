# Weekly Research — instrukcja obsługi

Pipeline tygodniowego researchu treści dla marki Kuchenna Komitywa. Robi dwa wywołania do Anthropic Claude: zbiera świeże informacje z sieci (web search) i formatuje je w gotowe posty na blog / Instagram (JSON).

## Co to robi

Komenda `python manage.py run_weekly_research` wykonuje dwa kroki:

1. **Research (call 1)** — Claude przeczesuje sieć w poszukiwaniu konkretów z 7 ostatnich dni: nowinki wegańskiego cukiernictwa, sezonowość, food tech, polski rynek wegański, ciekawostki kulinarne. Wynik to surowy tekst (~15-25k znaków, po polsku).
2. **Format (call 2)** — Drugi call Claude'a (bez web searcha) przerabia surowy research na gotowy JSON: artykuł na blog (600-900 słów, 3-4 sekcje), 5 postów na Instagram (z hashtagami i podpowiedziami zdjęciowymi), 6-7 slajdów stories (z kolorami marki).

Pomiędzy call 1 a call 2 komenda czeka 60s, żeby nie wpaść w rate limit Anthropic Tier 1. Na auto-retry call 2 (1×) komenda również czeka 60s przed drugą próbą.

Wynik trafia do modelu `content.WeeklyResearch` w bazie. Klucz to `week_label` (np. `2026-W22`) — tydzień researchu to **poprzedni tydzień ISO** względem dnia uruchomienia (poniedziałek-niedziela).

## Gdzie to oglądać

Admin: <https://kuchennakomitywa.pl/admin/content/weeklyresearch/>

Lista pokazuje: `week_label`, daty, status, kiedy utworzono. Klikając w wiersz zobaczysz:
- `raw_research` — pełny tekst researchu z call 1 (read-only)
- `formatted_json` — sparsowany JSON z call 2 (read-only)
- `status` i `error_message` jeśli coś poszło źle

W shellu (`python manage.py shell`):
```python
from content.models import WeeklyResearch
w = WeeklyResearch.objects.latest("date_to")
print(w.formatted_json["blog"]["title"])
print(w.formatted_json["instagram_posts"][0]["caption"])
```

## Pole `status` — co oznacza

| Status | Co się stało |
|---|---|
| `pending` | Rekord utworzony, jeszcze nic się nie wydarzyło (rzadkie — przejściowe) |
| `research_done` | Call 1 OK, `raw_research` zapisany, call 2 jeszcze nie poszedł lub padł przed startem |
| `formatted` | Wszystko OK, `formatted_json` gotowy do użycia |
| `failed` | Coś padło — szczegóły w `error_message` |

## Jak odpalić ręcznie

**Na serwerze produkcyjnym** (przez SSH do `panel84.mydevil.net`):
```bash
cd ~/domains/kuchennakomitywa.pl/public_python
~/.virtualenvs/komitywa/bin/python manage.py run_weekly_research
```

**Z `--force`** — regeneruje, nawet jeśli dla danego tygodnia jest już `status=formatted`:
```bash
~/.virtualenvs/komitywa/bin/python manage.py run_weekly_research --force
```

**Z `--retry-format`** — pomija call 1, robi tylko call 2 na istniejącym `raw_research`:
```bash
~/.virtualenvs/komitywa/bin/python manage.py run_weekly_research --retry-format
```

**Lokalnie** (do testów):
```bash
.venv/bin/python manage.py run_weekly_research
```

## Co zrobić, jak padło call 2 (`status=failed`, `raw_research` jest)

Najczęstsza przyczyna: skończyło się saldo na koncie Anthropic. Doładuj kredyty na <https://console.anthropic.com/settings/billing>, potem **`--force`** — komenda przerobi obie fazy od nowa.

**Tańsza opcja — `--retry-format`:** jeśli `raw_research` w bazie jest OK, a padło tylko formatowanie, użyj:

```bash
~/.virtualenvs/komitywa/bin/python manage.py run_weekly_research --retry-format
```

Komenda pomija drogi call 1 (web search), używa istniejącego `raw_research` z bazy i robi tylko call 2 (format). Koszt: ~$0.02-0.05 zamiast pełnych $0.10-0.20.

`--retry-format` jest mutually exclusive z `--force` (nie ma sensu wymuszać call 1 i jednocześnie go pomijać).

## Idempotencja

- Komenda sama oblicza `week_label` z bieżącej daty (poprzedni tydzień ISO).
- Jeśli rekord dla tego `week_label` ma `status=formatted` → komenda się zatrzyma i nic nie zrobi (chyba że `--force`).
- Jeśli rekord ma `status=failed` lub `research_done` → komenda spróbuje od nowa.

Bezpiecznie odpalić wiele razy — nie zdubluje rekordów.

## Koszty (orientacyjnie)

Per uruchomienie:
- Call 1 (Sonnet 4.6 + web search, ~5-10 wyszukiwań) → ok. **$0.05 - $0.15**
- Call 2 (Sonnet 4.6, sam tekst) → ok. **$0.02 - $0.05**
- Razem: **ok. $0.10-0.20 / tydzień**, czyli ~$5-10 / rok przy cotygodniowym uruchomieniu.

Faktyczny koszt sprawdzisz na <https://console.anthropic.com/settings/usage>.

## Czy odpala się sam?

**TAK — co poniedziałek o 06:00 CEST.** Cron jest aktywny na serwerze `panel84.mydevil.net`. Pierwsze automatyczne uruchomienie: najbliższy poniedziałek 06:00 (czas polski).

Aktualny wpis crontab:
```
0 6 * * 1 cd /usr/home/jem3pizze/domains/kuchennakomitywa.pl/public_python && /usr/home/jem3pizze/.virtualenvs/komitywa/bin/python manage.py run_weekly_research >> /usr/home/jem3pizze/domains/kuchennakomitywa.pl/logs/weekly_research.log 2>&1
```

Output (stdout + stderr) ląduje w `~/domains/kuchennakomitywa.pl/logs/weekly_research.log`.

### Jak sprawdzić / zmienić harmonogram

```bash
# Lista zaplanowanych zadań
crontab -l

# Edycja w vi (zmiana godziny, wyłączenie itd.)
crontab -e

# Podgląd logu z ostatnich automatycznych uruchomień
tail -n 100 ~/domains/kuchennakomitywa.pl/logs/weekly_research.log
```

Albo przez GUI MyDevil: <https://panel.mydevil.net/> → CRON.

### Dlaczego poniedziałek 06:00

Cron odpala się **na początku tygodnia** — wtedy `week_label` to dopiero co zakończony tydzień ISO (pon-niedz), więc research jest świeży. 06:00 polskiego czasu to przed startem dnia roboczego, gotowy materiał czeka rano w adminie.

## Co można z tym dalej zrobić

`formatted_json` to gotowy materiał — wystarczy go skopiować i opublikować. Możliwe rozszerzenia (jeśli zechcesz):

1. **Strona admina z podglądem** — ładny preview JSON-a (blog/posty/stories) zamiast surowego JSONField, z przyciskiem "Copy to clipboard" dla każdego segmentu.
2. **Eksport markdownu na blog** — drugi command albo akcja w adminie, która z `formatted_json["blog"]` robi gotowy plik `.md` lub wpis w jakimś modelu `BlogPost`.
3. **✅ Generowanie grafik stories + AI prompty pod posty** — DONE (260603-aou).
   Patrz sekcja "Generowanie grafik IG" ponizej.
4. **Newsletter** — wysyłka co tydzień z najlepszymi fragmentami researchu (newsletter app już jest w projekcie).
5. **Per-tydzień regeneracja konkretnego segmentu** — np. tylko stories albo tylko blog, jak coś jest słabe.

Daj znać, co Cię interesuje — każde z tych można zrobić jako osobny `/gsd:quick`.

## Pliki w tym appie

| Plik | Co tam jest |
|---|---|
| `models.py` | `WeeklyResearch` — model przechowujący wynik |
| `admin.py` | rejestracja w panelu admina |
| `management/commands/run_weekly_research.py` | komenda + prompty (RESEARCH_PROMPT, FORMAT_PROMPT) |
| `migrations/0001_initial.py` | tabela `content_weeklyresearch` |
| `services/colors.py` | Brand palette mapping (text_color_for_bg) |
| `services/story_renderer.py` | PNG renderer dla IG Stories |
| `services/ai_prompts.py` | Brand AI image prompt suffix |
| `management/commands/generate_story_images.py` | CLI generator PNG-ow |
| `fonts/NotoSans-*.ttf` | Bundled fonty (Pillow) |
| `views.py` | + WeeklyResearchStoriesZipView (ZIP download) |

Prompty są verbatim z brifu (paleta kolorów w stories podmieniona na realną z `static/css/main.css`). Modyfikacje promptów: edytuj `run_weekly_research.py`, zrób PR/commit, deploy.

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

ZIP endpoint (staff-only): `/blog/admin/content/weeklyresearch/<pk>/stories_zip`
(URL pattern: `/blog/admin/content/weeklyresearch/<pk>/stories.zip` — name: `content:weeklyresearch_stories_zip`)

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
