---
phase: quick-260608-dau
plan: 01
subsystem: content
tags: [anthropic, rate-limit, web-search, cron, weekly-research]
status: complete

provides:
  - "max_uses:5 na web_search w call 1 (ograniczenie drenazu ITPM bucketa)"
  - "Helper _create_with_429_retry + _parse_retry_after + MAX_429_RETRIES — retry na 429 honorujacy retry-after"
  - "Obsluga RateLimitError w call 1 (research) i call 2 (format)"

key-files:
  modified:
    - content/management/commands/run_weekly_research.py

key-decisions:
  - "Zostajemy na Tier 1 + claude-sonnet-4-6 — fix po stronie kodu, bez upgrade tieru"
  - "Lazy import RateLimitError wewnatrz helpera (wzorzec jak Anthropic w handle())"
  - "MAX_429_RETRIES=3 — twardy limit, brak nieskonczonej petli"
  - "_parse_retry_after waliduje float + max(1,...), fallback 60s przy braku/zlym naglowku"

requirements-completed: []

duration: ~6min
completed: 2026-06-08
---

# Quick 260608-dau: Fix rate-limit 429 w run_weekly_research

**Cotygodniowy pipeline na cron mydevil.net padał z 429 (rate_limit_error, 30K ITPM Tier 1) na call 2 — naprawiony przez ograniczenie drenazu web_search i retry honorujacy retry-after.**

## Root cause (potwierdzony)

Error z produkcji: `call 2 (format): Error code: 429 - rate_limit_error ... 30,000 input tokens per minute ... claude-sonnet-4-6`.

- Call 1 (research z web_search bez `max_uses`) PRZECHODZIŁ, ale drenowal minutowy bucket ITPM (peak 204K / limit 30K = 681% z konsoli Anthropic).
- Staly sleep 60s przed call 2 odbudowywal tylko ~30K — za malo.
- Call 2 (format) dostawal 429 przed wykonaniem.
- `_call_format` lapal WYLACZNIE `json.JSONDecodeError` — `RateLimitError` wybuchal jako nieobsluzony wyjatek → status `failed`.

## Co zrobiono

1. **`max_uses: 5`** na narzedziu web_search (call 1) — ogranicza liczbe agentowych rund wyszukiwania i drenaz bucketa.
2. **Retry na 429** przez wspolny helper `_create_with_429_retry` (metoda Command) + czysta funkcja modulu `_parse_retry_after` + stala `MAX_429_RETRIES = 3`. Helper czyta `retry-after` z `exc.response.headers`, spi tyle ile kaze serwer (fallback 60s), ponawia do 3 razy, po wyczerpaniu rzuca `CommandError`. Podpiety pod call 1 (research) i call 2 (`_call_format._do_call`).

Zachowane bez zmian: VERBATIM prompty (RESEARCH_PROMPT, FORMAT_PROMPT, JSON_STRICTNESS_ADDENDUM) oraz istniejaca logika retry na `json.JSONDecodeError`.

## Weryfikacja

- `.venv/bin/python manage.py check` — 0 issues.
- Smoke test `_parse_retry_after`: `parse OK` (42, 60, 60, 60).
- grep potwierdza markery (max_uses, RateLimitError, helper, parser, stala) w call 1 i call 2.
- Reczna sciezka E2E (opcjonalna, kosztuje API): `.venv/bin/python manage.py run_weekly_research --force` ze skonfigurowanym ANTHROPIC_API_KEY.

## Commity

- `a6a68c6` feat(quick-260608-dau): max_uses na web_search + helper retry na 429
- `9177dfc` feat(quick-260608-dau): podpiac helper 429 pod call 1 i call 2

## Deployment note

Zmiana jest tylko w repo lokalnym. Zeby zadziałała na produkcji, trzeba **wdrozyc na serwer mydevil.net** (git pull / deploy strony) — inaczej cron dalej odpala stara wersje komendy.
