---
phase: 260602-i1r
plan: 01
subsystem: content
tags:
  - django-app
  - management-command
  - anthropic
  - weekly-pipeline
dependency_graph:
  requires:
    - backend/settings.py (django-environ pattern, INSTALLED_APPS, AUTH backends)
    - recipes/models.py (model style reference)
    - accounts/admin.py (admin decorator style reference)
  provides:
    - "content.models.WeeklyResearch (ORM model + table content_weeklyresearch)"
    - "content.admin.WeeklyResearchAdmin (admin UI under /admin/content/weeklyresearch/)"
    - "manage.py run_weekly_research [--force] (CLI entry point)"
    - "settings.ANTHROPIC_API_KEY (env-driven)"
  affects:
    - backend/settings.py (INSTALLED_APPS += "content", + ANTHROPIC_API_KEY)
    - requirements.txt (+ anthropic>=0.40,<1.0)
tech-stack:
  added:
    - anthropic SDK (>=0.40,<1.0) — Python client for Anthropic Messages API
  patterns:
    - "Lazy import dla SDK (try/except ImportError → CommandError)"
    - "Idempotency via week_label unique + status check + --force override"
    - "Per-step status persist (pending → research_done → formatted | failed)"
    - "FORMAT_PROMPT.replace zamiast .format() — JSON klamry zostaja literalne"
key-files:
  created:
    - content/__init__.py
    - content/apps.py
    - content/models.py
    - content/admin.py
    - content/migrations/__init__.py
    - content/migrations/0001_initial.py
    - content/management/__init__.py
    - content/management/commands/__init__.py
    - content/management/commands/run_weekly_research.py
  modified:
    - backend/settings.py
    - requirements.txt
decisions:
  - "ANTHROPIC_API_KEY przez django-environ (env('ANTHROPIC_API_KEY', default='')) zamiast os.environ.get — zgodnie z istniejacym wzorcem P24_*/EMAIL_* w settings.py"
  - "FORMAT_PROMPT laczy z researchem przez .replace('{raw_research}', ...) zamiast .format() — pozwala zachowac literalne klamry JSON-a bez podwajania w stringu"
  - "Lazy import anthropic SDK wewnatrz handle() — pozwala manage.py --help i manage.py check dzialac bez zainstalowanego pakietu"
  - "Idempotency check przed API key check — jesli status='formatted' i nie ma --force, kojarzy zbedne zuzycie quoty i przerywa wczesnie"
  - "Zakres dat = poprzedni tydzien ISO (pon-niedz) — wyliczany przez date.today() - weekday, niezalezny od dnia uruchomienia (idealne na cron w pon. rano)"
metrics:
  duration: "~5 min"
  tasks_completed: 6
  files_created: 9
  files_modified: 2
  completed: 2026-06-02
---

# Quick Task 260602-i1r: nowy app `content` z weekly research pipeline — Summary

Stworzony nowy Django app `content/` hostujacy tygodniowy pipeline researchu + generowania
contentu dla marki Kuchenna Komitywa: model `WeeklyResearch`, admin, oraz management
command `run_weekly_research` ktory wykonuje dwa wywolania Anthropic (research z web search
+ format do JSON-a) z persystencja statusu na kazdym kroku.

## Co zostalo zbudowane

### App `content/`
- **`content/apps.py`** — `ContentConfig(AppConfig)` z `name = "content"` i `default_auto_field = "django.db.models.BigAutoField"`.
- **`content/models.py`** — `WeeklyResearch` z 9 polami:
  - `week_label` (ISO YYYY-Www, unique, indexed)
  - `date_from`, `date_to` (DateField)
  - `raw_research` (TextField, blank default="")
  - `formatted_json` (JSONField, null/blank)
  - `status` (CharField z choices: pending / research_done / formatted / failed, default="pending")
  - `error_message` (TextField, blank default="")
  - `created_at`, `updated_at` (auto)
  - `Meta.ordering = ["-date_to"]`, verbose_name "Weekly research"
  - `__str__` zwraca `"{week_label} ({status})"`
- **`content/admin.py`** — `@admin.register(WeeklyResearch)` z list_display
  (week_label, date_from, date_to, status, created_at), list_filter (status),
  search_fields (week_label), readonly_fields (raw_research, formatted_json, created_at, updated_at).
- **`content/migrations/0001_initial.py`** — wygenerowana automatycznie, zaaplikowana
  (tabela `content_weeklyresearch` istnieje).

### Management command
- **`content/management/commands/run_weekly_research.py`**:
  - Module-level constants `RESEARCH_PROMPT` i `FORMAT_PROMPT` — DOSLOWNE kopie z
    `PROMPTS-VERBATIM.md` (RESEARCH_PROMPT = 1679 chars, FORMAT_PROMPT = 2138 chars,
    weryfikowane byte-for-byte vs source).
  - Argument `--force` (action="store_true") — wymusza ponowne wygenerowanie nawet
    jesli istnieje row ze statusem `formatted`.
  - `handle()`:
    1. Wyznacza poprzedni tydzien ISO (poniedzialek-niedziela) z `date.today()`.
    2. Idempotency check: jesli row dla `week_label` ma status `formatted` i brak `--force` → return z WARNING.
    3. API key check: jesli brak `settings.ANTHROPIC_API_KEY` → `CommandError`.
    4. `get_or_create` row + reset stanu do `pending` (zeby `--force` mogl nadpisac).
    5. Lazy import `Anthropic` (po API key check, dla `--help` bez SDK).
    6. **Call 1** (research, z web search): `claude-sonnet-4-6`, max 8000 tokenow,
       tool `web_search_20250305`. Filtruje response.content po `block.type == "text"`,
       zapisuje do `raw_research`, ustawia status `research_done`.
    7. **Call 2** (format, bez web search): `FORMAT_PROMPT.replace("{raw_research}", raw_research)`,
       sciaga markdown fence'y (` ``` ` / `json`), `json.loads()`, zapisuje do `formatted_json`,
       status `formatted`. JSON parse error → status `failed` + truncated raw w `error_message`.
  - Persystencja statusu na kazdym kroku — kazdy fail zapisuje `status="failed"` + `error_message` z prefixem `call 1 (research): ...` lub `call 2 (format): ...`.

### Konfiguracja
- **`backend/settings.py`**:
  - `"content"` dodane do `INSTALLED_APPS` (po `"newsletter"`).
  - `ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default="")` dodane miedzy sekcja Email a Logging.
- **`requirements.txt`**:
  - `anthropic>=0.40,<1.0` na koncu pliku.

## Pliki utworzone / zmienione

| Status | Plik |
|--------|------|
| Created | content/__init__.py |
| Created | content/apps.py |
| Created | content/models.py |
| Created | content/admin.py |
| Created | content/migrations/__init__.py |
| Created | content/migrations/0001_initial.py |
| Created | content/management/__init__.py |
| Created | content/management/commands/__init__.py |
| Created | content/management/commands/run_weekly_research.py |
| Modified | backend/settings.py |
| Modified | requirements.txt |

## Commits (atomic per task)

| # | Task | Hash |
|---|------|------|
| 1 | Szkielet appa content (AppConfig + puste moduly) | `7eb99c9` |
| 2 | Model WeeklyResearch z 9 polami i Meta | `c863bcc` |
| 3 | Admin dla WeeklyResearch z filtrem i readonly | `de6e620` |
| 4 | Komenda run_weekly_research z 2-call pipeline | `f1e2cf2` |
| 5 | content w INSTALLED_APPS + ANTHROPIC_API_KEY + anthropic dep | `4b7a885` |
| 6 | Migracja 0001_initial dla WeeklyResearch | `2d547a5` |

## Jak uruchomic

1. **Zainstaluj nowa zaleznosc** (na lokalu i na serwerze):
   ```bash
   pip install -r requirements.txt
   ```

2. **Dodaj klucz API do `.env`**:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-...
   ```

3. **Uruchom pipeline**:
   ```bash
   # Standardowo (raz w tygodniu, najlepiej w poniedzialek rano):
   python manage.py run_weekly_research

   # Wymus ponowne wygenerowanie (gdy chcesz nadpisac juz sformatowany tydzien):
   python manage.py run_weekly_research --force
   ```

4. **Podejrzyj wyniki**:
   - Admin: `/admin/content/weeklyresearch/` — lista wszystkich tygodni z filtrem statusu;
     `raw_research` i `formatted_json` jako readonly w detail view.
   - ORM: `WeeklyResearch.objects.filter(status="formatted").latest("date_to").formatted_json`

## Co dalej (TODO dla uzytkownika)

1. **Dodac `ANTHROPIC_API_KEY` do `.env`** lokalnie i na produkcji (MyDevil).
2. **Skonfigurowac cron** na MyDevil zeby pipeline biegal raz w tygodniu, np.:
   ```cron
   # Poniedzialek 7:00 rano, generuje content dla zakonczonego tygodnia
   0 7 * * 1 cd /home/USER/domains/kuchennakomitywa.pl/public_python && /home/USER/.virtualenv/.../bin/python manage.py run_weekly_research >> logs/run_weekly_research.log 2>&1
   ```
3. **Opcjonalnie** — dodac panel adminowy do publikacji/edycji `formatted_json`
   przed wrzuceniem na blog / Instagram (nastepny quick task).

## Decisions Made

1. **`env()` zamiast `os.environ.get()`** — Plan sugerowal `os.environ.get`, ale wzorzec
   projektu (P24_*, EMAIL_*) konsekwentnie uzywa `django-environ`. Wybralem spojnosc
   z istniejacym kodem.
2. **`FORMAT_PROMPT.replace()` zamiast `.format()`** — PROMPTS-VERBATIM.md zostawia
   klamry JSON-a pojedyncze (literalne), wiec `.format()` by sie wywrocil na `KeyError: '"blog"'`.
   `.replace("{raw_research}", ...)` jest bezpieczniejszy i lepiej dokumentowany.
3. **Lazy import `anthropic`** — pozwala `manage.py --help`, `manage.py check` i ad-hoc
   workflow developera dzialac bez zainstalowanego SDK; CommandError dopiero w handle().
4. **Idempotency check PRZED API key check** — jesli row jest juz `formatted`, nie ma
   sensu nawet pytac o klucz; przerywa tanszej sciezki najwczesniej.

## Verbatim Prompt Audit

Skontrolowane programatycznie po napisaniu pliku komendy: oba prompty (`RESEARCH_PROMPT`
i `FORMAT_PROMPT`) zgadzaja sie z `PROMPTS-VERBATIM.md` byte-for-byte (lacznie z
trailing-whitespace na koncach linii ktore w Markdownie funkcjonuja jako soft-breaks):

- RESEARCH_PROMPT: 1679 znakow — EXACT MATCH
- FORMAT_PROMPT: 2138 znakow — EXACT MATCH

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Trailing whitespace stripped on initial Write**
- **Found during:** Task 4 (verbatim audit po napisaniu pliku)
- **Issue:** Pierwszy zapis `run_weekly_research.py` przez tool Write zignorowal trailing
  spaces na koncu linii promptow (rozbieznosc 12 i 16 znakow vs verbatim).
- **Fix:** Regenerowalem caly plik poprzez `Python open().write()` z stringami wczytanymi
  bezposrednio z PROMPTS-VERBATIM.md (extract markerow `RESEARCH_PROMPT = """` /
  `FORMAT_PROMPT = """`). Po regeneracji oba prompty matchuja byte-for-byte.
- **Files modified:** content/management/commands/run_weekly_research.py
- **Commit:** `f1e2cf2` (single Task 4 commit obejmuje juz finalna wersje)

### Out of Scope (none)

Brak — pre-existing warnings w innych appach nie byly napotkane (manage.py check przeszedl
0 issues od baseline'u).

## Smoke Test Results

```
$ python manage.py check
System check identified no issues (0 silenced).

$ python manage.py run_weekly_research --help
usage: manage.py run_weekly_research [-h] [--force] [...]

Uruchamia tygodniowy research + format na contentu (call 1 + call 2 do
Anthropic).

options:
  -h, --help    show this help message and exit
  --force       Wymus ponowne wygenerowanie nawet jesli status to 'formatted'.
  ...

$ python manage.py shell -c "from content.models import WeeklyResearch; print(WeeklyResearch.objects.count())"
0
```

Brak wywolania Anthropic API w trakcie tego planu — to placeholder na pozniej, kiedy
ANTHROPIC_API_KEY trafi do `.env`.

## Self-Check: PASSED

- [x] content/__init__.py — FOUND
- [x] content/apps.py — FOUND
- [x] content/models.py — FOUND
- [x] content/admin.py — FOUND
- [x] content/migrations/__init__.py — FOUND
- [x] content/migrations/0001_initial.py — FOUND
- [x] content/management/__init__.py — FOUND
- [x] content/management/commands/__init__.py — FOUND
- [x] content/management/commands/run_weekly_research.py — FOUND
- [x] backend/settings.py — modified (INSTALLED_APPS + ANTHROPIC_API_KEY)
- [x] requirements.txt — modified (+anthropic>=0.40,<1.0)
- [x] Commit 7eb99c9 — FOUND
- [x] Commit c863bcc — FOUND
- [x] Commit de6e620 — FOUND
- [x] Commit f1e2cf2 — FOUND
- [x] Commit 4b7a885 — FOUND
- [x] Commit 2d547a5 — FOUND
- [x] `python manage.py check` — 0 issues
- [x] `python manage.py run_weekly_research --help` — pokazuje `--force`
- [x] Prompty match byte-for-byte z PROMPTS-VERBATIM.md
