---
phase: quick-260608-dau
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - content/management/commands/run_weekly_research.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "Call 1 (research) ogranicza liczbe rund web_search przez max_uses, co zmniejsza drenaz minutowego bucketa ITPM"
    - "Call 2 (_call_format) lapie anthropic.RateLimitError (429) i ponawia z poszanowaniem retry-after zamiast wybuchac nieobsluzonym wyjatkiem"
    - "Call 1 (research) tez jest zabezpieczony przed 429 przez ten sam helper retry"
    - "Istniejaca logika retry na json.JSONDecodeError w _call_format pozostaje nienaruszona"
    - "Tresc RESEARCH_PROMPT i FORMAT_PROMPT pozostaje VERBATIM (bez zmian)"
    - "python manage.py check przechodzi bez bledow"
  artifacts:
    - path: "content/management/commands/run_weekly_research.py"
      provides: "Helper retry na 429 + max_uses na web_search + obsluga RateLimitError w call 1 i call 2"
      contains: "RateLimitError"
  key_links:
    - from: "_call_format._do_call"
      to: "_create_with_429_retry helper"
      via: "owijanie client.messages.create"
      pattern: "RateLimitError"
    - from: "tools web_search dict"
      to: "max_uses limit"
      via: "klucz max_uses w diccie narzedzia"
      pattern: "max_uses"
---

<objective>
Naprawic rate-limit 429 w cotygodniowym pipeline `run_weekly_research`. Dwie zmiany w jednym pliku:
1. Dodac `max_uses` do narzedzia web_search (call 1), by ograniczyc agentowy drenaz minutowego bucketa input tokens (Tier 1 = 30K ITPM).
2. Dodac obsluge `anthropic.RateLimitError` (429) z retry honorujacym naglowek `retry-after`, zarowno dla call 2 (_call_format, glowny cel) jak i call 1 (research) — przez wspolny helper, bez nadmiernego refaktoru.

Purpose: Pipeline obecnie failuje (status `failed`) na cron mydevil.net, bo call 1 przekracza bucket (peak 204K/30K), staly sleep 60s nie odbudowuje go wystarczajaco, a `_call_format` lapie WYLACZNIE `json.JSONDecodeError` — `RateLimitError` wybucha jako nieobsluzony wyjatek.

Output: Zaktualizowany `content/management/commands/run_weekly_research.py` ktory przechodzi `manage.py check`, zachowuje VERBATIM prompty i istniejaca logike retry JSON.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@content/management/commands/run_weekly_research.py

<facts>
Zweryfikowane fakty o pakiecie anthropic (.venv, wersja 0.105.2):
- `anthropic.RateLimitError` istnieje, status_code = 429.
- MRO: RateLimitError -> APIStatusError -> APIError -> AnthropicError -> Exception.
- `APIStatusError` przechowuje `response` (obiekt httpx.Response), wiec `exc.response` jest dostepny.
- Naglowek czytamy: `exc.response.headers.get("retry-after")` (string, sekundy — Anthropic zwraca sekundy).
- Klient tworzony lokalnie w handle(): `from anthropic import Anthropic` (lazy, by ImportError dal czytelny CommandError). `RateLimitError` importowac TAK SAMO lazy/lokalnie (wewnatrz helpera) — NIE top-level.

Tier 1 limit: 30,000 input tokens / minute (ITPM). web_search bez max_uses robi wiele rund w jednym requescie — kazdy pobrany wynik wraca jako input tokens (peak z konsoli: 204K = 681%).
</facts>

<interfaces>
Istniejaca sygnatura metody (zachowac):
```python
def _call_format(self, client, prompt: str) -> dict:
    def _do_call() -> str: ...   # owija client.messages.create + ekstrakcja text + strip fence
    text = _do_call()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        ... sleep 60 ... text2 = _do_call() ... json.loads(text2) ... raise CommandError
```

Call 1 (handle(), galaz B, ~linia 264):
```python
research_response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=8000,
    tools=[{"type": "web_search_20250305", "name": "web_search"}],
    messages=[...],
)
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: max_uses na web_search + helper retry na 429</name>
  <files>content/management/commands/run_weekly_research.py</files>
  <action>
Dwie powiazane zmiany w tym samym pliku.

A) max_uses na web_search (call 1, ~linia 267). Zmienic dict narzedzia z:
   `{"type": "web_search_20250305", "name": "web_search"}`
na:
   `{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}`
Komentarz inline (PL): max_uses ogranicza liczbe rund web_search, by nie drenowac minutowego bucketa ITPM (Tier 1 = 30K input tokens/min).

B) Dodac na poziomie modulu czysta funkcje parsera + na poziomie klasy Command metode-helper retry:

   Stala modulu: `MAX_429_RETRIES = 3`.

   Funkcja modulu (latwa do testu, bez API):
   ```python
   def _parse_retry_after(headers, default=60):
       """Czyta naglowek retry-after (sekundy) z mapy naglowkow. Fallback = default."""
       raw = headers.get("retry-after") if headers else None
       if raw is None:
           return default
       try:
           return max(1, int(round(float(raw))))
       except (ValueError, TypeError):
           return default
   ```

   Metoda klasy Command:
   ```python
   def _create_with_429_retry(self, client, call_label, **create_kwargs):
       """client.messages.create(**create_kwargs) z retry na RateLimitError (429).

       Czyta retry-after z exc.response.headers, spi tyle ile kaze serwer
       (fallback 60s), ponawia do MAX_429_RETRIES razy. Po wyczerpaniu prob
       rzuca CommandError z czytelnym komunikatem.
       """
       from anthropic import RateLimitError  # lazy, wzorzec jak Anthropic w handle()
       for attempt in range(MAX_429_RETRIES):
           try:
               return client.messages.create(**create_kwargs)
           except RateLimitError as exc:
               if attempt == MAX_429_RETRIES - 1:
                   raise CommandError(
                       f"{call_label}: rate limit 429 po {MAX_429_RETRIES} probach: {exc}"
                   ) from exc
               response = getattr(exc, "response", None)
               headers = getattr(response, "headers", None)
               wait = _parse_retry_after(headers, default=60)
               self.stderr.write(self.style.WARNING(
                   f"[429] {call_label}: rate limit, retry {attempt + 1}/{MAX_429_RETRIES} za {wait}s..."
               ))
               time.sleep(wait)
   ```
   Helper dotyczy WYLACZNIE 429 i samego wywolania create — NIE lapie json.JSONDecodeError ani innych wyjatkow.

Nie modyfikowac tresci RESEARCH_PROMPT/FORMAT_PROMPT/JSON_STRICTNESS_ADDENDUM. Konwencje: double quotes, snake_case, 4 spacje.
  </action>
  <verify>
    <automated>.venv/bin/python manage.py check 2>&1 | tail -5</automated>
    <automated>grep -n "max_uses" content/management/commands/run_weekly_research.py</automated>
    <automated>grep -n "RateLimitError\|_create_with_429_retry\|_parse_retry_after\|MAX_429_RETRIES" content/management/commands/run_weekly_research.py</automated>
  </verify>
  <done>
- Dict web_search zawiera `"max_uses": 5`.
- Istnieje metoda `_create_with_429_retry`, funkcja `_parse_retry_after`, stala `MAX_429_RETRIES`.
- `from anthropic import RateLimitError` jest lazy (wewnatrz helpera), nie top-level.
- `manage.py check` przechodzi bez bledow.
  </done>
</task>

<task type="auto">
  <name>Task 2: Podpiac helper pod call 1 i call 2 + smoke test parsera</name>
  <files>content/management/commands/run_weekly_research.py</files>
  <action>
Podpiac helper z Task 1 pod oba wywolania, zachowujac CALA istniejaca logike.

A) Call 2 (_call_format, glowny cel). W zagniezdzonej `_do_call()` zamienic bezposrednie
   `response = client.messages.create(model=..., max_tokens=8000, messages=[...])`
   na:
   `response = self._create_with_429_retry(client, "call 2 (format)", model="claude-sonnet-4-6", max_tokens=8000, messages=[{"role": "user", "content": prompt}])`
   Reszta `_call_format` (ekstrakcja text, strip fence, json.loads, retry na JSONDecodeError, sleep 60, drugi call, CommandError) MUSI pozostac bez zmian. Skoro `_do_call` jest wywolywany dwa razy (1. proba i retry po JSONDecodeError), oba automatycznie przejda przez ochrone 429 — to pozadane.

B) Call 1 (handle(), galaz B, ~linia 264). Zamienic
   `research_response = client.messages.create(model=..., max_tokens=8000, tools=[...], messages=[...])`
   na:
   `research_response = self._create_with_429_retry(client, "call 1 (research)", model="claude-sonnet-4-6", max_tokens=8000, tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}], messages=[...])`
   Istniejacy `try/except Exception` wokol call 1 (ustawia status="failed" + error_message) pozostaje — `CommandError` z helpera (po wyczerpaniu prob) zostanie zlapany przez ten `except Exception`, poprawnie oznaczy rekord jako failed i re-raise. To OK.

Konwencje: double quotes dla nowych stringow, snake_case, 4 spacje.

C) Smoke test parsera retry-after (inline, jednorazowy — NIE zapisywac jako test file, brak pytest w projekcie). Patrz blok verify.
  </action>
  <verify>
    <automated>.venv/bin/python manage.py check 2>&1 | tail -5</automated>
    <automated>.venv/bin/python -c "import django,os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings'); django.setup(); from content.management.commands.run_weekly_research import _parse_retry_after as p; assert p({'retry-after':'42'})==42; assert p({})==60; assert p({'retry-after':'bad'})==60; assert p(None)==60; print('parse OK')"</automated>
    <automated>grep -n "_create_with_429_retry(client, \"call 1\|_create_with_429_retry(client, \"call 2" content/management/commands/run_weekly_research.py</automated>
  </verify>
  <done>
- Call 1 (research) i call 2 (_call_format._do_call) wywoluja `self._create_with_429_retry(...)` zamiast bezposredniego `client.messages.create(...)`.
- Smoke test parsera zwraca `parse OK` (42, 60, 60, 60).
- Istniejaca logika JSONDecodeError-retry, sleep 60s i CommandError w `_call_format` jest nienaruszona.
- RESEARCH_PROMPT/FORMAT_PROMPT bez zmian.
- `manage.py check` przechodzi.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| pipeline -> Anthropic API | Wychodzace wywolania HTTP; odpowiedzi (w tym naglowki retry-after i tresc web_search) sa niezaufanym wejsciem z zewnatrz. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-dau-01 | Denial of Service | `_create_with_429_retry` petla retry | mitigate | Twardy limit `MAX_429_RETRIES = 3` — brak nieskonczonej petli; po wyczerpaniu prob CommandError oznacza rekord jako failed. |
| T-dau-02 | Tampering | naglowek `retry-after` z odpowiedzi API | mitigate | `_parse_retry_after` waliduje wartosc (`float` + `max(1, ...)`), fallback 60s przy braku/nieparsowalnym — wartosc nie moze byc ujemna/zlosliwie zerowa. |
| T-dau-03 | Denial of Service | web_search agentowe rundy (drenaz ITPM) | mitigate | `max_uses: 5` ogranicza liczbe rund wyszukiwania, redukujac peak input tokens ponizej granic zdolnych zablokowac caly pipeline. |
</threat_model>

<verification>
- `.venv/bin/python manage.py check` przechodzi bez bledow.
- `grep` potwierdza obecnosc `max_uses`, `RateLimitError`, `_create_with_429_retry`, `_parse_retry_after`, `MAX_429_RETRIES`.
- Smoke test `_parse_retry_after` zwraca `parse OK`.
- Reczna sciezka (opcjonalna, kosztuje API + ~minuty): `.venv/bin/python manage.py run_weekly_research --force` na srodowisku z `ANTHROPIC_API_KEY` — oczekiwane: brak nieobsluzonego 429; przy 429 widoczny warning `[429] ... retry N/3 za Xs...` i kontynuacja; finalnie status `formatted`.
</verification>

<success_criteria>
- web_search ma `max_uses: 5`.
- `anthropic.RateLimitError` jest lapany i ponawiany z retry-after w call 1 i call 2.
- Istniejaca logika JSON-retry i VERBATIM prompty nienaruszone.
- `manage.py check` + smoke test parsera przechodza.
</success_criteria>

<output>
After completion, create `.planning/quick/260608-dau-fix-rate-limit-429-w-run-weekly-research/260608-dau-SUMMARY.md`
</output>
