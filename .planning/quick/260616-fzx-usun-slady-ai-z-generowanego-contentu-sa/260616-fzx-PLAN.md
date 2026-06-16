---
phase: quick-260616-fzx
plan: 01
type: tdd
wave: 1
depends_on: []
files_modified:
  - content/tests/__init__.py
  - content/tests/test_humanize.py
  - content/services/humanize.py
  - content/management/commands/run_weekly_research.py
  - content/management/commands/humanize_content.py
autonomous: true
requirements: [HUMANIZE-01]
must_haves:
  truths:
    - "humanize_text turns ' — ' (em dash with surrounding whitespace) into ', '"
    - "Numeric ranges like '10–15' and '6–7' are left untouched"
    - "Glued letter em dash 'słowo—słowo' becomes 'słowo, słowo'"
    - "Ellipsis '…' becomes '...'"
    - "humanize_text is idempotent (running twice equals running once)"
    - "Polish „cytat\" quotes are left intact"
    - "humanize_json recurses through nested dict/list, cleaning string leaves"
    - "run_weekly_research applies humanize_json to parsed JSON before saving"
    - "run_weekly_research appends HUMANIZE_ADDENDUM to the format prompt"
    - "humanize_content command backfills existing rows with --dry-run support"
  artifacts:
    - path: "content/services/humanize.py"
      provides: "humanize_text + humanize_json deterministic sanitizer"
      contains: "def humanize_text"
    - path: "content/tests/test_humanize.py"
      provides: "Unit tests for the sanitizer"
      contains: "class"
    - path: "content/management/commands/humanize_content.py"
      provides: "Backfill command with --dry-run"
      contains: "def handle"
  key_links:
    - from: "content/management/commands/run_weekly_research.py"
      to: "content/services/humanize.py"
      via: "humanize_json(parsed) before row.formatted_json save"
      pattern: "humanize_json"
    - from: "content/management/commands/humanize_content.py"
      to: "content/services/humanize.py"
      via: "humanize_text / humanize_json import"
      pattern: "from content.services.humanize import"
---

<objective>
Remove "AI tells" from generated blog/IG-post/stories content. The user's concrete
complaint is the long em dash "—". Two complementary levers:
1. Deterministic sanitizer (`content/services/humanize.py`) — reliable typography/dash fixes.
2. Soft prompt nudge (HUMANIZE_ADDENDUM) — style/phrase guidance where deterministic
   edits would break grammar.

Plus a backfill command to clean content already stored in the DB.

Purpose: Generated content should read as human-written, not machine-generated.
Output: A tested sanitizer service, an edited generation pipeline, and a backfill command.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@./CLAUDE.md
@content/management/commands/run_weekly_research.py
@content/models.py
@content/templatetags/content_extras.py

<interfaces>
<!-- Established patterns the executor uses directly — no codebase exploration needed. -->

Services layer (content/services/) holds single-responsibility, testable modules
(ai_prompts.py, colors.py, story_renderer.py already follow this). humanize.py joins them.

Existing addendum pattern in run_weekly_research.py (line ~100):
```python
JSON_STRICTNESS_ADDENDUM = (
    "\n\nKRYTYCZNE: zwroc WYLACZNIE prawidlowy, parsowalny JSON. "
    ...
)
```
And applied at line ~356:
```python
prompt = FORMAT_PROMPT.replace("{raw_research}", raw_research) + JSON_STRICTNESS_ADDENDUM
```
Save point (line ~372):
```python
row.formatted_json = parsed
row.status = "formatted"
```

Backfill targets (content/models.py):
- WeeklyResearch.formatted_json (JSONField, null=True) — humanize_json, skip null rows.
- BlogPost.title / .excerpt / .body — humanize_text each. tags: leave (comma-separated).
- StorySlide.headline / .subtext / .visual_hint — humanize_text each.

Models import via: `from content.models import WeeklyResearch, BlogPost, StorySlide`

NO content/tests/ dir exists yet — create the package fresh.
venv at .venv. Double quotes for all new strings (CLAUDE.md). gettext NOT needed.
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1 (RED): Write failing tests for the sanitizer</name>
  <files>content/tests/__init__.py, content/tests/test_humanize.py</files>
  <action>
    Create the tests package (empty content/tests/__init__.py) and content/tests/test_humanize.py.
    Use `from django.test import SimpleTestCase` (no DB needed — humanize_text/humanize_json are pure).
    Import target (does NOT exist yet — this is RED):
    `from content.services.humanize import humanize_text, humanize_json`

    Cover AT MINIMUM these cases (one assertion-focused test method each, double quotes):
    - Em dash with surrounding whitespace → comma+space: humanize_text("tekst — więcej") == "tekst, więcej"
      (also test en dash variant "tekst – więcej" → "tekst, więcej")
    - Numeric ranges PRESERVED: humanize_text("10–15") == "10–15" and humanize_text("6–7") == "6–7"
      (digit on both sides, en or em dash, no surrounding space — must stay)
    - Glued letter em dash → comma: humanize_text("słowo—słowo") == "słowo, słowo"
    - Ellipsis: humanize_text("Czekamy…") == "Czekamy..."
    - IDEMPOTENCE on a mixed string: x = "tekst — więcej, słowo—słowo, 10–15, Czekamy…"
      then humanize_text(humanize_text(x)) == humanize_text(x)
    - Polish quotes left intact: humanize_text("„Kuchenna Komitywa\"") == "„Kuchenna Komitywa\""
      (the low-open U+201E + high-close U+201D pair must NOT be touched)
    - English curly quotes normalize: assert that a string using the English-role opening
      curly quote U+201C ("“tekst”") has its U+201C converted to a straight ", while a
      Polish „…" string is left uncorrupted (this guards the conservative quote rule).
    - humanize_json recursion: humanize_json({"a": "x — y", "b": ["p—q", 5, {"c": "z…"}]})
      == {"a": "x, y", "b": ["p, q", 5, {"c": "z..."}]}  (note non-string leaf 5 untouched)

    Run the suite to confirm it FAILS with ImportError/ModuleNotFound (RED is real).
    Commit: `test(quick-260616-fzx): add failing tests for humanize sanitizer`
  </action>
  <verify>
    <automated>.venv/bin/python manage.py test content.tests.test_humanize 2>&1 | grep -qE "Error|FAILED|No module" && echo "RED confirmed"</automated>
  </verify>
  <done>content/tests/test_humanize.py exists with the listed cases; suite fails because content.services.humanize does not exist yet.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2 (GREEN): Implement content/services/humanize.py</name>
  <files>content/services/humanize.py</files>
  <behavior>
    All Task 1 tests pass. Idempotent. Numeric ranges preserved. Polish „…" intact.
  </behavior>
  <action>
    Create content/services/humanize.py with two functions (double quotes, module docstring).
    Keep ALL logic here (single responsibility — commands/pipeline only call it).

    `humanize_text(s: str) -> str` — deterministic, IDEMPOTENT normalization of ONE string:
    1. Dashes:
       - Surrounded-by-whitespace dash: regex `\s+[—–]\s+` (em U+2014 / en U+2013) → ", ".
       - Glued LETTER dash: a letter, then [—–], then a letter → "letter, letter". Use a
         regex with letter classes (NOT digits) so numeric ranges are excluded. Recommended:
         `re.sub(r"(?<=\w)[—–](?=\w)", ...)` will ALSO catch digits — so guard against digits:
         match only when neither side is a digit. Practical approach:
         `re.sub(r"(?<=[^\W\d_])[—–](?=[^\W\d_])", ", ", s)` (Unicode letter on both sides,
         excludes digits/underscore). This leaves "10–15" / "6–7" untouched (digit neighbours).
    2. Ellipsis: replace "…" (U+2026) with "...".
    3. Quotes — CONSERVATIVE rule (document in a comment exactly as chosen):
       - KEEP Polish „…" (low U+201E open + high U+201D close — correct brand typography).
       - Convert English opening curly U+201C → straight ".
       - Convert curly apostrophe U+2019 → straight '.
       - For U+201D (ambiguous: Polish closing AND English closing): only convert U+201D → "
         when it is NOT part of a Polish pair, i.e. when there is NO U+201E earlier in the
         string. Safe heuristic: `if "„" not in s: replace U+201D with straight quote`.
         If U+201E IS present, leave U+201D alone (prefer leaving over corrupting Polish quotes).
         Add a comment explaining this is intentionally conservative.
    4. Cleanup: collapse runs of spaces/tabs to a single space (do NOT touch newlines).
       e.g. `re.sub(r"[ \t]{2,}", " ", s)`. Order steps so the dash→", " replacement
       does not leave double spaces; the cleanup is the safety net for idempotence.

    Make idempotence robust: after replacements, " — " becomes ", " (single space). Running
    again must NOT match ", " against the dash pattern (it won't — no dash present). Verify
    against the Task 1 idempotence test.

    `humanize_json(obj)` — recursively walk: if dict → new dict mapping keys to
    humanize_json(value); if list → list of humanize_json(item); if str → humanize_text(obj);
    else return obj unchanged (ints, floats, bool, None untouched). Return the cleaned structure.

    Run tests until all GREEN.
    Commit: `feat(quick-260616-fzx): humanize sanitizer (dashes, ellipsis, conservative quotes, json recursion)`
  </action>
  <verify>
    <automated>.venv/bin/python manage.py test content.tests.test_humanize</automated>
  </verify>
  <done>All Task 1 tests pass (OK). Numeric ranges preserved, Polish „…" intact, idempotence holds.</done>
</task>

<task type="auto">
  <name>Task 3: Wire sanitizer into pipeline + add HUMANIZE_ADDENDUM</name>
  <files>content/management/commands/run_weekly_research.py</files>
  <action>
    Edit content/management/commands/run_weekly_research.py (double quotes, do NOT touch the
    verbatim FORMAT_PROMPT / RESEARCH_PROMPT bodies — addendum only, mirroring JSON_STRICTNESS_ADDENDUM).

    1. Add import at top with the other content imports:
       `from content.services.humanize import humanize_json`

    2. Add a module-level HUMANIZE_ADDENDUM string right after JSON_STRICTNESS_ADDENDUM
       (around line 104). Content (Polish, double-quoted, leading "\n\n"): instruct the model
       to write like a human — NO long em dashes (—); use a comma or period instead. Avoid
       AI filler/cliché phrases, then list the curated phrases to avoid:
       "warto pamiętać", "nie tylko… ale również" / "nie tylko… ale także",
       "w dzisiejszych czasach", "w dzisiejszym świecie", "w dobie", "podsumowując".
       Make clear these phrases are handled ONLY by the prompt (the deterministic sanitizer
       does not remove phrases). Keep tone consistent with the existing addendum.

    3. Append it to the format prompt at line ~356:
       `prompt = FORMAT_PROMPT.replace("{raw_research}", raw_research) + JSON_STRICTNESS_ADDENDUM + HUMANIZE_ADDENDUM`

    4. Apply the sanitizer to parsed JSON BEFORE saving. After `parsed = self._call_format(client, prompt)`
       succeeds (the try block ~line 358) and before `row.formatted_json = parsed` (~line 372),
       insert: `parsed = humanize_json(parsed)`. Pick that single clean spot — do not clean twice.
  </action>
  <verify>
    <automated>.venv/bin/python -c "import ast,sys; ast.parse(open('content/management/commands/run_weekly_research.py').read()); src=open('content/management/commands/run_weekly_research.py').read(); assert 'HUMANIZE_ADDENDUM' in src and 'humanize_json(parsed)' in src and '+ HUMANIZE_ADDENDUM' in src; print('OK')"</automated>
  </verify>
  <done>File parses; HUMANIZE_ADDENDUM defined and appended to prompt; humanize_json(parsed) applied before save. FORMAT_PROMPT/RESEARCH_PROMPT bodies unchanged.</done>
</task>

<task type="auto">
  <name>Task 4: Backfill command humanize_content (with --dry-run)</name>
  <files>content/management/commands/humanize_content.py</files>
  <action>
    Create content/management/commands/humanize_content.py — a Django BaseCommand (double quotes).
    Imports: `from django.core.management.base import BaseCommand` and
    `from content.services.humanize import humanize_text, humanize_json` and
    `from content.models import WeeklyResearch, BlogPost, StorySlide`.

    add_arguments: a `--dry-run` flag (action="store_true", help="Pokaz co BY sie zmienilo, bez zapisu.").

    handle():
    - WeeklyResearch: iterate all rows; skip rows where formatted_json is None. Compute
      `cleaned = humanize_json(row.formatted_json)`; if cleaned != row.formatted_json, it changed.
      If not dry-run: row.formatted_json = cleaned; row.save(update_fields=["formatted_json", "updated_at"]).
    - BlogPost: iterate all rows. For each of title, excerpt, body compute humanize_text and
      compare. Leave `tags` untouched (comma-separated — acceptable per decision). If any of the
      three changed and not dry-run: assign the cleaned values and
      row.save(update_fields=[<only changed fields>, "updated_at"]).
    - StorySlide: iterate all rows. Same approach for headline, subtext, visual_hint. Save with
      update_fields of only the changed fields + "updated_at" when not dry-run.

    Reporting:
    - Count changed rows per model and print a summary line per model (use self.style.SUCCESS /
      NOTICE). Prefix with "[DRY-RUN]" when dry-run.
    - In dry-run, also print a few (cap ~3 per model) before/after diffs so the user can eyeball
      them (e.g. show the first changed field truncated to ~120 chars: `f"  - {before!r} -> {after!r}"`).
    - Do NOT save anything when --dry-run is set.

    Be careful with update_fields: only include fields that actually changed (avoid clobbering).
    Empty string fields (excerpt/subtext/visual_hint default "") are fine — humanize_text("") == "".
  </action>
  <verify>
    <automated>.venv/bin/python -c "import ast; ast.parse(open('content/management/commands/humanize_content.py').read()); print('parse OK')" && .venv/bin/python manage.py humanize_content --dry-run 2>&1 | tail -5</automated>
  </verify>
  <done>Command exists and parses; `manage.py humanize_content --dry-run` runs without error and prints per-model summary; no DB writes occur in dry-run. Full test suite (`content.tests.test_humanize`) still green.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| LLM output → DB | Generated JSON is untrusted text; sanitizer transforms strings only |
| CLI operator → DB writes | humanize_content mutates stored content rows |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-fzx-01 | Tampering | humanize_text quote rule | mitigate | Conservative rule: never convert U+201D when U+201E present, preventing corruption of Polish brand quotes |
| T-fzx-02 | Denial of Service | run_weekly_research per-string regex | accept | Inputs are bounded LLM outputs (max_tokens=8000); regex are linear, no catastrophic backtracking |
| T-fzx-03 | Tampering | humanize_content unintended writes | mitigate | --dry-run preview before commit; update_fields scoped to only changed fields; skip null formatted_json |
</threat_model>

<verification>
- `.venv/bin/python manage.py test content.tests.test_humanize` → all tests pass.
- run_weekly_research.py parses, contains HUMANIZE_ADDENDUM, appends it to prompt, and applies
  humanize_json(parsed) before save; verbatim prompt bodies unchanged.
- `manage.py humanize_content --dry-run` runs clean and reports per-model counts without writing.
- Numeric ranges ("10–15", "6–7") survive; Polish „…" survives; idempotence verified by test.
</verification>

<success_criteria>
- Deterministic sanitizer exists, fully tested, idempotent, conservative on Polish typography.
- Generation pipeline cleans output and nudges the model away from AI tells via addendum.
- Backfill command can preview (--dry-run) and apply cleanup to existing WeeklyResearch / BlogPost
  / StorySlide rows, saving only changed fields.
- No push to main (executor commits locally only).
</success_criteria>

<output>
After completion, create `.planning/quick/260616-fzx-usun-slady-ai-z-generowanego-contentu-sa/260616-fzx-SUMMARY.md`
</output>
