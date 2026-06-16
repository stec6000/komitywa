---
quick_id: 260616-fzx
status: complete
date: 2026-06-16
---

# Quick Task 260616-fzx — Summary

**Cel:** Generowany content (blog / IG posty / stories) nie ma wyglądać jak pisany przez AI — konkretna skarga użytkownika: długi myślnik („—"). Dwa komplementarne mechanizmy: deterministyczny sanitizer (pewny — typografia/dasze) + miękki nudge w prompcie (styl/frazy, gdzie deterministyczna edycja psułaby gramatykę).

## Co wylądowało

- **`content/services/humanize.py`** — `humanize_text(s)` (idempotentny) + `humanize_json(obj)` (rekursja po dict/list):
  - em/en dash w spacjach → `, ` ("tekst — więcej" → "tekst, więcej")
  - sklejony literowy em dash ("słowo—słowo") → "słowo, słowo"
  - zakresy liczbowe ("10–15", "6–7") **zachowane** (cyfra po obu stronach)
  - wielokropek "…" → "..."
  - konserwatywna reguła cudzysłowów: polskie „…" **nietknięte**, normalizowane tylko angielskie zakrzywione + apostrof
  - sprzątanie podwójnych spacji
- **`content/tests/__init__.py` + `content/tests/test_humanize.py`** — 14 testów `SimpleTestCase`, wszystkie zielone.
- **`run_weekly_research.py`** — `HUMANIZE_ADDENDUM` doklejany do promptu obok `JSON_STRICTNESS_ADDENDUM` (verbatim FORMAT_PROMPT/RESEARCH_PROMPT nietknięte); `humanize_json(parsed)` zastosowany raz przed zapisem.
- **`content/management/commands/humanize_content.py`** — backfill istniejących danych (WeeklyResearch.formatted_json, BlogPost title/excerpt/body, StorySlide headline/subtext/visual_hint) z flagą `--dry-run`, scoped `update_fields`, `tags` pozostawione nietknięte.

## Commity (lokalnie na main, NIE wypchnięte)

- `9dcc428` test: failing tests for humanize sanitizer (RED)
- `9dff655` feat: humanize sanitizer (GREEN)
- `bf9d79f` feat: wire humanize_json into pipeline + HUMANIZE_ADDENDUM
- `751722b` feat: humanize_content backfill command with --dry-run

## Weryfikacja

- `python manage.py test content.tests.test_humanize` → 14 testów OK.
- Smoke na realnych stringach: em dash→przecinek, zakresy zachowane, sklejony dash, wielokropek, polskie „brownie" nietknięte, rekursja JSON, idempotencja — wszystko potwierdzone.

## Notatki / do decyzji użytkownika

- **Nie wypchnięto** na main (push = auto-deploy prod). Deploy + backfill na prod (`python manage.py humanize_content`, najpierw `--dry-run`) do uruchomienia osobno po decyzji.
- Backfill dotyczy też już wypromowanych BlogPost/StorySlide — realnie widocznych na stronie.
- SUMMARY.md zrekonstruowany przez orchestratora (oryginał z worktree przepadł przy `git worktree remove --force` — był untracked).
