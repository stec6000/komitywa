---
phase: 260602-prf
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - content/templatetags/__init__.py
  - content/templatetags/content_extras.py
  - content/static/content/admin/weekly_research_preview.css
  - content/static/content/admin/weekly_research_preview.js
  - content/templates/admin/content/weeklyresearch/change_form.html
  - content/templates/admin/content/weeklyresearch/_preview.html
  - content/admin.py
autonomous: true
requirements:
  - QUICK-260602-prf
must_haves:
  truths:
    - "Admin /admin/content/weeklyresearch/<id>/change/ pokazuje sekcję 'Gotowy content do skopiowania' pod polami formularza"
    - "Trzy zakładki (Blog / IG Posty / IG Stories) przełączają się bez JS (CSS-only radio)"
    - "Klik 'Skopiuj X' kopiuje treść do clipboard i pokazuje toast 'Skopiowano!' (~1.5s)"
    - "Stories renderują się jako pigułki 9:16 z kolorem tła z bg_color i tekstem w czytelnym kolorze (jasny/ciemny w zależności od tła)"
    - "Brand palette zachowana (#f3ead7 paper, #2a2420 ink, #6b7a3a olive, #b6562e terracotta, #c89a3a mustard)"
    - "Wszystkie posty IG (każdy z hashtagami + visual_hint) renderowane jako karty"
    - "Bulk-copy działa: cały blog jako Markdown, wszystkie posty jako tekst, wszystkie stories jako lista"
    - "Filtr text_color_for_bg poprawnie mapuje wszystkie 5 kolorów brand + default dla nieznanych"
    - "Deploy: kod na origin/main, panel84.mydevil.net zaktualizowany przez deploy.sh, manage.py check zielony"
  artifacts:
    - path: "content/templatetags/__init__.py"
      provides: "Templatetags package init (puste, ale wymagane przez Django)"
    - path: "content/templatetags/content_extras.py"
      provides: "Filter text_color_for_bg z hardcoded mapping brand colors"
      contains: "register.filter"
    - path: "content/static/content/admin/weekly_research_preview.css"
      provides: "Brand-styled preview CSS — tabs, panele, karty, toast, copy buttons"
      min_lines: 150
    - path: "content/static/content/admin/weekly_research_preview.js"
      provides: "Vanilla JS — delegated click handler dla copy buttons + toast"
      max_lines: 50
    - path: "content/templates/admin/content/weeklyresearch/change_form.html"
      provides: "Override Django admin change_form z hookiem na CSS/JS/preview"
    - path: "content/templates/admin/content/weeklyresearch/_preview.html"
      provides: "Partial: trzy panele (Blog/Posts/Stories) z data-copy-text"
      contains: "kk-panel-blog"
    - path: "content/admin.py"
      provides: "WeeklyResearchAdmin z change_form_template wskazującym na custom template"
      contains: "change_form_template"
  key_links:
    - from: "content/admin.py"
      to: "content/templates/admin/content/weeklyresearch/change_form.html"
      via: "change_form_template attribute"
      pattern: "change_form_template.*=.*admin/content/weeklyresearch/change_form.html"
    - from: "change_form.html"
      to: "_preview.html"
      via: "{% include %} w bloku after_field_sets"
      pattern: "include.*_preview.html"
    - from: "_preview.html"
      to: "content_extras.text_color_for_bg"
      via: "{% load content_extras %} + filter |text_color_for_bg"
      pattern: "text_color_for_bg"
    - from: "_preview.html (buttons)"
      to: "weekly_research_preview.js"
      via: "data-copy-text attribute → delegated click listener"
      pattern: "data-copy-text"
    - from: "change_form.html"
      to: "weekly_research_preview.css + .js"
      via: "{% static %} link/script tags"
      pattern: "static.*weekly_research_preview"
---

<objective>
Dodaj tabbed preview UI do Django admin dla modelu WeeklyResearch — trzy zakładki (Blog / IG Posty / IG Stories), każda z Copy-to-clipboard buttons. Stylizacja w brand palette Kuchennej Komitywy (paper/ink/olive/terracotta/mustard). Stories renderują się jako pigułki 9:16 z dynamicznym kontrastem tekstu (filter text_color_for_bg). Bulk-copy dla całych sekcji (cały blog jako Markdown, wszystkie posty, wszystkie stories). Vanilla JS only, CSS-only tab switching (radio + ~ selector).

Purpose: Po wygenerowaniu weekly research przez `run_weekly_research`, admin staje się głównym workflow tool — szybki, ergonomiczny preview + copy-paste do bloga/IG bez kopiowania surowego JSON.

Output: Plik content/admin.py rozszerzony o change_form_template + 6 nowych plików (templatetag, CSS, JS, 2 templates, init). Po deployu admin pokazuje preview dla wszystkich rekordów ze statusem `formatted` (gdzie `formatted_json` nie jest pusty).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md

# Source: WeeklyResearch model (status + formatted_json)
@content/models.py

# Source: current admin (will be modified — add change_form_template only)
@content/admin.py

# Source: Django settings — TEMPLATES (APP_DIRS=True), STATIC_URL=/static/, whitenoise compressed manifest storage
@backend/settings.py

# Brand palette source (lines 8-21)
@static/css/main.css

<interfaces>
<!-- WeeklyResearch.formatted_json shape (from RESEARCH_PROMPT / FORMAT_PROMPT — DO NOT modify) -->
<!-- Template loops over these exact keys. -->

```python
# WeeklyResearch.formatted_json structure (when status="formatted")
{
  "blog": {
    "title": str,
    "intro": str,
    "sections": [{"heading": str, "body": str}, ...],
    "tags": [str, ...],
    "meta_description": str
  },
  "instagram_posts": [
    {
      "caption": str,
      "hashtags": [str, ...],
      "visual_hint": str
    },
    ...
  ],
  "instagram_stories": [
    {
      "slide_type": str,        # e.g. "intro", "tip", "cta"
      "emoji": str,             # 1-2 emoji chars
      "text": str,              # body of slide
      "bg_color": str           # hex e.g. "#6b7a3a"
    },
    ...
  ]
}
```

<!-- Brand palette (from static/css/main.css :root) -->
```css
--paper:        #f3ead7;  /* main bg */
--paper-shadow: #d9c9a3;  /* borders */
--ink:          #2a2420;  /* main text */
--ink-soft:     #5a4a3a;  /* secondary text / inactive tab border */
--accent:       #6b7a3a;  /* olive — active tab */
--accent-2:     #b6562e;  /* terracotta — copy buttons */
--accent-3:     #c89a3a;  /* mustard — focus outline */
--rule:         #c7b48a;
```

<!-- Django admin template override convention -->
<!-- Path: content/templates/admin/<app_label>/<model_name>/change_form.html -->
<!-- Inherits: admin/change_form.html (Django built-in) -->
<!-- Blocks used: extrastyle (CSS), after_field_sets (preview content), admin_change_form_document_ready (JS) -->
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Utwórz templatetags package + filter text_color_for_bg</name>
  <files>content/templatetags/__init__.py, content/templatetags/content_extras.py</files>
  <action>
1. Utwórz `content/templatetags/__init__.py` — pusty plik (wymagany przez Django do rejestracji templatetags).

2. Utwórz `content/templatetags/content_extras.py`:

```python
from django import template

register = template.Library()


# Hardcoded mapping for brand palette colors.
# Returns the text color that should be used on top of the given background.
_BRAND_TEXT_COLOR_MAP = {
    "#2a2420": "#f3ead7",  # ink → paper (jasny tekst)
    "#6b7a3a": "#f3ead7",  # olive → paper
    "#b6562e": "#f3ead7",  # terracotta → paper
    "#c89a3a": "#2a2420",  # mustard → ink (żółty wymaga ciemnego tekstu)
    "#f3ead7": "#2a2420",  # paper → ink
}

_DEFAULT_TEXT_COLOR = "#2a2420"


@register.filter
def text_color_for_bg(value):
    """Return readable text color for a given background hex.

    Case-insensitive. Unknown colors default to ink (#2a2420).
    """
    if not value:
        return _DEFAULT_TEXT_COLOR
    key = str(value).strip().lower()
    return _BRAND_TEXT_COLOR_MAP.get(key, _DEFAULT_TEXT_COLOR)
```

Bez logiki luminance — hardcoded mapping jest świadomym wyborem (5 brand colors, deterministyczne, brak edge cases dla podobnych kolorów).
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; .venv/bin/python -c "import django; import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings'); django.setup(); from content.templatetags.content_extras import text_color_for_bg; assert text_color_for_bg('#2a2420') == '#f3ead7', 'ink failed'; assert text_color_for_bg('#6B7A3A') == '#f3ead7', 'case-insens olive failed'; assert text_color_for_bg('#c89a3a') == '#2a2420', 'mustard failed'; assert text_color_for_bg('#f3ead7') == '#2a2420', 'paper failed'; assert text_color_for_bg('#FFFFFF') == '#2a2420', 'default failed'; assert text_color_for_bg('') == '#2a2420', 'empty failed'; assert text_color_for_bg(None) == '#2a2420', 'None failed'; print('filter OK')"</automated>
  </verify>
  <done>Filter zarejestrowany, mapuje 5 brand colors poprawnie (case-insensitive), default dla unknown/empty/None to #2a2420.</done>
</task>

<task type="auto">
  <name>Task 2: Utwórz CSS — brand-styled preview z tabs, kartami, toast</name>
  <files>content/static/content/admin/weekly_research_preview.css</files>
  <action>
Utwórz `content/static/content/admin/weekly_research_preview.css`. Struktura (~200 linii):

```css
/* Kuchenna Komitywa — Admin Preview dla WeeklyResearch */

.kk-preview {
    --paper: #f3ead7;
    --paper-shadow: #d9c9a3;
    --ink: #2a2420;
    --ink-soft: #5a4a3a;
    --accent: #6b7a3a;
    --accent-2: #b6562e;
    --accent-3: #c89a3a;
    --rule: #c7b48a;

    margin: 24px 0;
    background: var(--paper);
    padding: 24px;
    border-radius: 12px;
    border: 1px solid var(--paper-shadow);
    color: var(--ink);
    font-family: Georgia, "Newsreader", serif;
}

.kk-preview-heading {
    margin: 0 0 16px;
    font-size: 20px;
    color: var(--ink);
}

/* ===== Tabs (CSS-only radio trick) ===== */
.kk-tabs {
    position: relative;
}

.kk-tabs > input[type="radio"] {
    position: absolute;
    opacity: 0;
    pointer-events: none;
}

.kk-tabs > label {
    display: inline-block;
    padding: 10px 20px;
    margin-right: 8px;
    border-radius: 999px;
    background: transparent;
    border: 2px solid var(--ink-soft);
    color: var(--ink-soft);
    cursor: pointer;
    font-weight: 600;
    user-select: none;
    transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.kk-tabs > label:hover {
    background: var(--paper-shadow);
    color: var(--ink);
}

#kk-tab-blog:checked    ~ label[for="kk-tab-blog"],
#kk-tab-posts:checked   ~ label[for="kk-tab-posts"],
#kk-tab-stories:checked ~ label[for="kk-tab-stories"] {
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
}

.kk-tabs > .kk-panel {
    display: none;
    margin-top: 24px;
    padding-top: 24px;
    border-top: 1px solid var(--rule);
}

#kk-tab-blog:checked    ~ .kk-panel-blog,
#kk-tab-posts:checked   ~ .kk-panel-posts,
#kk-tab-stories:checked ~ .kk-panel-stories {
    display: block;
}

/* ===== Blog panel ===== */
.kk-blog-title {
    font-size: 28px;
    line-height: 1.2;
    color: var(--ink);
    margin: 0 0 8px;
    font-family: "DM Serif Display", Georgia, serif;
}

.kk-blog-intro {
    font-size: 17px;
    line-height: 1.5;
    color: var(--ink-soft);
    margin: 12px 0;
}

.kk-blog-section {
    margin: 20px 0;
}

.kk-blog-section h3 {
    font-size: 18px;
    color: var(--accent);
    margin: 0 0 8px;
}

.kk-blog-section p {
    font-size: 15px;
    line-height: 1.6;
    color: var(--ink);
    margin: 0 0 8px;
}

.kk-tags-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin: 16px 0;
}

.kk-chip {
    background: var(--paper-shadow);
    color: var(--ink);
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 12px;
}

.kk-meta-box {
    background: #fff8ea;
    border: 1px dashed var(--rule);
    padding: 10px 14px;
    border-radius: 6px;
    font-family: "JetBrains Mono", monospace;
    font-size: 13px;
    margin: 12px 0;
    color: var(--ink-soft);
}

/* ===== Posts panel ===== */
.kk-post-card {
    background: #fff;
    box-shadow: 0 2px 8px rgba(42, 36, 32, 0.08);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
}

.kk-post-number {
    font-size: 12px;
    color: var(--ink-soft);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 8px;
}

.kk-post-caption {
    white-space: pre-wrap;
    font-size: 15px;
    line-height: 1.5;
    color: var(--ink);
    margin-bottom: 12px;
}

.kk-post-hashtags {
    color: var(--accent);
    font-size: 13px;
    margin-bottom: 12px;
}

.kk-post-visual-hint {
    background: var(--paper);
    border-left: 3px solid var(--accent-3);
    padding: 10px 14px;
    margin: 12px 0;
    font-style: italic;
    color: var(--ink-soft);
    font-size: 13px;
}

.kk-post-visual-hint::before {
    content: "Sugerowany kadr: ";
    font-weight: 600;
    color: var(--ink);
    font-style: normal;
}

.kk-post-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

/* ===== Stories panel ===== */
.kk-stories-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, 140px);
    gap: 16px;
    justify-content: start;
}

.kk-story-wrapper {
    display: flex;
    flex-direction: column;
    gap: 4px;
    align-items: center;
}

.kk-story-card {
    aspect-ratio: 9 / 16;
    width: 140px;
    padding: 16px;
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    position: relative;
    overflow: hidden;
    box-sizing: border-box;
}

.kk-story-emoji {
    font-size: 32px;
    text-align: center;
}

.kk-story-text {
    font-size: 14px;
    line-height: 1.3;
    text-align: center;
    flex-grow: 1;
    display: flex;
    align-items: center;
    justify-content: center;
}

.kk-story-type {
    font-size: 9px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    opacity: 0.7;
    text-align: center;
}

.kk-story-hex {
    font-family: "JetBrains Mono", monospace;
    font-size: 10px;
    opacity: 0.6;
    color: var(--ink-soft);
}

/* ===== Copy buttons ===== */
.kk-copy-btn {
    background: var(--accent-2);
    color: #fff;
    border: none;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
    transition: background 0.15s;
    margin: 4px 4px 4px 0;
    font-weight: 600;
}

.kk-copy-btn:hover {
    background: #9c4724;
}

.kk-copy-btn:focus {
    outline: 2px solid var(--accent-3);
    outline-offset: 2px;
}

.kk-copy-btn.kk-copied {
    background: var(--accent);
}

.kk-copy-btn-primary {
    background: var(--ink);
    padding: 10px 18px;
    font-size: 14px;
}

.kk-copy-btn-primary:hover {
    background: #1a1612;
}

.kk-bulk-actions {
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid var(--rule);
}

/* ===== Toast ===== */
.kk-toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: var(--ink);
    color: #fff;
    padding: 12px 20px;
    border-radius: 8px;
    opacity: 0;
    transform: translateY(10px);
    transition: opacity 0.2s, transform 0.2s;
    z-index: 9999;
    pointer-events: none;
    font-family: Georgia, serif;
    font-size: 14px;
}

.kk-toast.kk-show {
    opacity: 1;
    transform: translateY(0);
}
```

Uwagi:
- `.kk-tabs > input[type="radio"]` jako siblings przed labels i panels (general sibling `~`)
- `box-sizing: border-box` na `.kk-story-card` żeby padding nie wypchnął kafla
- `aspect-ratio: 9/16` + fixed width = stała wysokość story (modern browsers OK, Django admin jest desktop)
- Brak external fonts (zmienne `--font-*` z main.css nie są tu dostępne) — używamy Georgia/system fallback z explicit font-family
  </action>
  <verify>
    <automated>test -f /home/tomo/workspace/komitywa/content/static/content/admin/weekly_research_preview.css &amp;&amp; wc -l /home/tomo/workspace/komitywa/content/static/content/admin/weekly_research_preview.css | awk '{ if ($1 &lt; 150) { print "TOO SHORT:", $1; exit 1 } else { print "lines OK:", $1 } }' &amp;&amp; grep -q "#6b7a3a" /home/tomo/workspace/komitywa/content/static/content/admin/weekly_research_preview.css &amp;&amp; grep -q "#b6562e" /home/tomo/workspace/komitywa/content/static/content/admin/weekly_research_preview.css &amp;&amp; grep -q "kk-panel-stories" /home/tomo/workspace/komitywa/content/static/content/admin/weekly_research_preview.css &amp;&amp; grep -q "aspect-ratio" /home/tomo/workspace/komitywa/content/static/content/admin/weekly_research_preview.css &amp;&amp; echo "CSS structural checks OK"</automated>
  </verify>
  <done>CSS file istnieje (≥150 linii), zawiera brand colors hex (#6b7a3a, #b6562e), klasę kk-panel-stories, aspect-ratio dla story cards.</done>
</task>

<task type="auto">
  <name>Task 3: Utwórz JS — vanilla copy handler + toast</name>
  <files>content/static/content/admin/weekly_research_preview.js</files>
  <action>
Utwórz `content/static/content/admin/weekly_research_preview.js`:

```javascript
(function () {
    "use strict";

    let toastEl = null;
    let toastTimer = null;

    function getToast() {
        if (toastEl) return toastEl;
        toastEl = document.createElement("div");
        toastEl.className = "kk-toast";
        toastEl.setAttribute("role", "status");
        toastEl.setAttribute("aria-live", "polite");
        document.body.appendChild(toastEl);
        return toastEl;
    }

    function showToast(message) {
        const t = getToast();
        t.textContent = message;
        t.classList.add("kk-show");
        if (toastTimer) clearTimeout(toastTimer);
        toastTimer = setTimeout(function () {
            t.classList.remove("kk-show");
        }, 1500);
    }

    function flashButton(btn) {
        btn.classList.add("kk-copied");
        const original = btn.textContent;
        btn.textContent = "Skopiowano!";
        setTimeout(function () {
            btn.classList.remove("kk-copied");
            btn.textContent = original;
        }, 1500);
    }

    document.addEventListener("click", function (e) {
        const btn = e.target.closest("[data-copy-text]");
        if (!btn) return;
        e.preventDefault();
        const text = btn.dataset.copyText || "";
        if (!navigator.clipboard) {
            showToast("Clipboard niedostępny");
            return;
        }
        navigator.clipboard.writeText(text).then(function () {
            flashButton(btn);
            showToast("Skopiowano!");
        }).catch(function () {
            showToast("Błąd kopiowania");
        });
    });
})();
```

Uwagi:
- IIFE — zero global pollution
- `e.target.closest("[data-copy-text]")` — działa też gdy klikamy na child node przycisku
- `e.preventDefault()` — bo przyciski w admin/form mogłyby trigger submit (button bez `type` defaultuje do submit w `<form>`)
- Toast jest re-used, jeden DOM node przez cały czas życia strony
- Brak tab-switching JS — CSS-only (radio + ~ selector)
  </action>
  <verify>
    <automated>test -f /home/tomo/workspace/komitywa/content/static/content/admin/weekly_research_preview.js &amp;&amp; node --check /home/tomo/workspace/komitywa/content/static/content/admin/weekly_research_preview.js &amp;&amp; grep -q "navigator.clipboard.writeText" /home/tomo/workspace/komitywa/content/static/content/admin/weekly_research_preview.js &amp;&amp; grep -q "data-copy-text" /home/tomo/workspace/komitywa/content/static/content/admin/weekly_research_preview.js &amp;&amp; grep -q "preventDefault" /home/tomo/workspace/komitywa/content/static/content/admin/weekly_research_preview.js &amp;&amp; echo "JS syntax + structural checks OK"</automated>
  </verify>
  <done>JS file istnieje, parsuje się jako valid ES, używa navigator.clipboard, delegated click handler, preventDefault.</done>
</task>

<task type="auto">
  <name>Task 4: Utwórz templates — change_form override + _preview partial</name>
  <files>content/templates/admin/content/weeklyresearch/change_form.html, content/templates/admin/content/weeklyresearch/_preview.html</files>
  <action>
1. Utwórz `content/templates/admin/content/weeklyresearch/change_form.html`:

```django
{% extends "admin/change_form.html" %}
{% load static %}

{% block extrastyle %}
  {{ block.super }}
  <link rel="stylesheet" href="{% static 'content/admin/weekly_research_preview.css' %}">
{% endblock %}

{% block after_field_sets %}
  {{ block.super }}
  {% if original.formatted_json %}
    {% include "admin/content/weeklyresearch/_preview.html" with data=original.formatted_json %}
  {% endif %}
{% endblock %}

{% block admin_change_form_document_ready %}
  {{ block.super }}
  <script src="{% static 'content/admin/weekly_research_preview.js' %}"></script>
{% endblock %}
```

2. Utwórz `content/templates/admin/content/weeklyresearch/_preview.html`:

```django
{% load content_extras %}
<div class="kk-preview">
  <h2 class="kk-preview-heading">Gotowy content do skopiowania</h2>
  <div class="kk-tabs">
    <input type="radio" id="kk-tab-blog" name="kk-tab" checked>
    <input type="radio" id="kk-tab-posts" name="kk-tab">
    <input type="radio" id="kk-tab-stories" name="kk-tab">
    <label for="kk-tab-blog">Blog</label>
    <label for="kk-tab-posts">IG Posty ({{ data.instagram_posts|length }})</label>
    <label for="kk-tab-stories">IG Stories ({{ data.instagram_stories|length }})</label>

    {# ===== BLOG ===== #}
    <div class="kk-panel kk-panel-blog">
      {% with b=data.blog %}
        <h1 class="kk-blog-title">{{ b.title }}</h1>
        <button type="button" class="kk-copy-btn" data-copy-text="{{ b.title }}">Skopiuj tytuł</button>

        <p class="kk-blog-intro">{{ b.intro|linebreaksbr }}</p>
        <button type="button" class="kk-copy-btn" data-copy-text="{{ b.intro }}">Skopiuj intro</button>

        {% for s in b.sections %}
          <section class="kk-blog-section">
            <h3>{{ s.heading }}</h3>
            <p>{{ s.body|linebreaksbr }}</p>
            <button type="button" class="kk-copy-btn" data-copy-text="## {{ s.heading }}&#10;&#10;{{ s.body }}">Skopiuj sekcję</button>
          </section>
        {% endfor %}

        <div class="kk-tags-chips">
          {% for t in b.tags %}<span class="kk-chip">{{ t }}</span>{% endfor %}
        </div>

        <div class="kk-meta-box">
          <strong>Meta description:</strong> {{ b.meta_description }}
        </div>
        <button type="button" class="kk-copy-btn" data-copy-text="{{ b.meta_description }}">Skopiuj meta</button>

        <div class="kk-bulk-actions">
          <button type="button" class="kk-copy-btn kk-copy-btn-primary"
                  data-copy-text="# {{ b.title }}&#10;&#10;{{ b.intro }}&#10;&#10;{% for s in b.sections %}## {{ s.heading }}&#10;&#10;{{ s.body }}&#10;&#10;{% endfor %}**Tagi:** {% for t in b.tags %}#{{ t }} {% endfor %}&#10;&#10;_{{ b.meta_description }}_">
            Skopiuj całość bloga (Markdown)
          </button>
        </div>
      {% endwith %}
    </div>

    {# ===== POSTS ===== #}
    <div class="kk-panel kk-panel-posts">
      {% for p in data.instagram_posts %}
        <article class="kk-post-card">
          <div class="kk-post-number">Post {{ forloop.counter }}/{{ data.instagram_posts|length }}</div>
          <div class="kk-post-caption">{{ p.caption }}</div>
          <div class="kk-post-hashtags">
            {% for h in p.hashtags %}<span>#{{ h }}</span> {% endfor %}
          </div>
          <div class="kk-post-visual-hint">{{ p.visual_hint }}</div>
          <div class="kk-post-actions">
            <button type="button" class="kk-copy-btn"
                    data-copy-text="{{ p.caption }}&#10;&#10;{% for h in p.hashtags %}#{{ h }} {% endfor %}">
              Skopiuj post
            </button>
            <button type="button" class="kk-copy-btn" data-copy-text="{{ p.visual_hint }}">Skopiuj wizualkę</button>
          </div>
        </article>
      {% endfor %}
      <div class="kk-bulk-actions">
        <button type="button" class="kk-copy-btn kk-copy-btn-primary"
                data-copy-text="{% for p in data.instagram_posts %}=== POST {{ forloop.counter }} ==={% templatetag openblock %} endcomment {% templatetag closeblock %}{{ p.caption }}&#10;&#10;{% for h in p.hashtags %}#{{ h }} {% endfor %}&#10;&#10;Wizualka: {{ p.visual_hint }}&#10;&#10;{% endfor %}">
          Skopiuj wszystkie posty
        </button>
      </div>
    </div>

    {# ===== STORIES ===== #}
    <div class="kk-panel kk-panel-stories">
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
      <div class="kk-bulk-actions">
        <button type="button" class="kk-copy-btn kk-copy-btn-primary"
                data-copy-text="{% for s in data.instagram_stories %}{{ forloop.counter }}. [{{ s.slide_type }}] {{ s.emoji }} {{ s.text }}&#10;{% endfor %}">
          Skopiuj wszystkie teksty stories
        </button>
      </div>
    </div>
  </div>
</div>
```

**WAŻNE wzorce:**
- `type="button"` na KAŻDYM `<button>` — bez tego button defaultuje do `submit` i klika by trigger save form
- `&#10;` jako HTML entity dla newline w `data-copy-text` — Django auto-escape nie psuje encji numerycznych
- `{{ value }}` w atrybutach HTML → Django auto-escape konwertuje `"`, `<`, `>`, `&`, `'` automatycznie — bezpieczne
- Dla bulk-copy posts, używam `=== POST {{ forloop.counter }} ===` jako separator zamiast newline w treści separatorów (prościej)
- POPRAW separator dla bulk posts: zamiast skomplikowanego `templatetag` zamień na prostszy wzorzec. Skoryguj na:

```django
data-copy-text="{% for p in data.instagram_posts %}{% if not forloop.first %}&#10;&#10;----&#10;&#10;{% endif %}{{ p.caption }}&#10;&#10;{% for h in p.hashtags %}#{{ h }} {% endfor %}&#10;&#10;Wizualka: {{ p.visual_hint }}{% endfor %}"
```

(zaktualizuj treść template — usuń `{% templatetag %}` brzydotę z mojego draftu i użyj wersji z `{% if not forloop.first %}---{% endif %}` jako separator)

- Caption w post bez `|linebreaksbr` — bo `kk-post-caption` ma `white-space: pre-wrap` w CSS (Task 2), więc newline'y się wyrenderują naturalnie
- `b.intro|linebreaksbr` — bo blog intro chce mieć `<br>` w renderze
- `b.sections` body z `|linebreaksbr` analogicznie
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; .venv/bin/python -c "import django; import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings'); django.setup(); from django.template.loader import get_template; t1 = get_template('admin/content/weeklyresearch/change_form.html'); t2 = get_template('admin/content/weeklyresearch/_preview.html'); print('templates OK'); src = open('content/templates/admin/content/weeklyresearch/_preview.html').read(); assert 'text_color_for_bg' in src, 'filter not used'; assert 'kk-panel-blog' in src, 'blog panel missing'; assert 'kk-panel-posts' in src, 'posts panel missing'; assert 'kk-panel-stories' in src, 'stories panel missing'; assert 'data-copy-text' in src, 'copy buttons missing'; assert src.count('type=\"button\"') &gt;= 5, 'type=button missing on buttons'; cf = open('content/templates/admin/content/weeklyresearch/change_form.html').read(); assert 'weekly_research_preview.css' in cf; assert 'weekly_research_preview.js' in cf; assert 'after_field_sets' in cf; print('structural checks OK')"</automated>
  </verify>
  <done>Oba templates loadują się przez Django template engine; _preview.html zawiera 3 panele + filter usage + ≥5 buttonów z type="button" + data-copy-text; change_form.html linkuje CSS+JS.</done>
</task>

<task type="auto">
  <name>Task 5: Update admin.py — change_form_template attribute</name>
  <files>content/admin.py</files>
  <action>
Zmodyfikuj `content/admin.py` — dodaj `change_form_template` atrybut do `WeeklyResearchAdmin`. NIE dodawaj custom `get_formatted_preview` method (preview jest renderowany przez template, nie przez readonly field).

Po zmianie plik wygląda tak:

```python
from django.contrib import admin

from .models import WeeklyResearch


@admin.register(WeeklyResearch)
class WeeklyResearchAdmin(admin.ModelAdmin):
    change_form_template = "admin/content/weeklyresearch/change_form.html"
    list_display = ("week_label", "date_from", "date_to", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("week_label",)
    readonly_fields = ("raw_research", "formatted_json", "created_at", "updated_at")
    ordering = ("-date_to",)
```

Zmiana to jedna linia — `change_form_template = "admin/content/weeklyresearch/change_form.html"` jako pierwszy class attribute. Reszta bez zmian.
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; grep -q 'change_form_template = "admin/content/weeklyresearch/change_form.html"' content/admin.py &amp;&amp; .venv/bin/python manage.py check 2&gt;&amp;1 | grep -q "System check identified no issues" &amp;&amp; echo "admin.py update OK + django check passes"</automated>
  </verify>
  <done>WeeklyResearchAdmin ma change_form_template wskazujący na nowy template; `manage.py check` zielony (0 issues).</done>
</task>

<task type="auto">
  <name>Task 6: Lokalna walidacja end-to-end — collectstatic dry-run + smoke render</name>
  <files></files>
  <action>
Końcowa walidacja przed commitem i deployem:

1. `manage.py check` — musi przejść bez issues:
   ```bash
   cd /home/tomo/workspace/komitywa && .venv/bin/python manage.py check
   ```

2. `collectstatic --dry-run` — musi wymienić nowe pliki CSS i JS:
   ```bash
   cd /home/tomo/workspace/komitywa && .venv/bin/python manage.py collectstatic --noinput --dry-run 2>&1 | grep -E "weekly_research_preview\.(css|js)"
   ```
   Oczekiwane: 2 linie ze ścieżkami `content/admin/weekly_research_preview.css` i `.js`.

3. Smoke render preview partial z fake data:
   ```bash
   cd /home/tomo/workspace/komitywa && .venv/bin/python -c "
   import os, django
   os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
   django.setup()
   from django.template.loader import render_to_string
   fake = {
       'blog': {
           'title': 'Test tytuł',
           'intro': 'Test intro\nlinia 2',
           'sections': [{'heading': 'Sekcja 1', 'body': 'Body 1'}],
           'tags': ['wegan', 'test'],
           'meta_description': 'Meta opis',
       },
       'instagram_posts': [
           {'caption': 'Caption \"z cudzysłowem\"', 'hashtags': ['vegan'], 'visual_hint': 'kadr'},
       ],
       'instagram_stories': [
           {'slide_type': 'intro', 'emoji': '🌱', 'text': 'Tekst story', 'bg_color': '#6b7a3a'},
           {'slide_type': 'tip', 'emoji': '✨', 'text': 'Inny', 'bg_color': '#c89a3a'},
       ],
   }
   html = render_to_string('admin/content/weeklyresearch/_preview.html', {'data': fake})
   assert 'Test tytuł' in html, 'title not rendered'
   assert 'kk-panel-blog' in html, 'blog panel missing'
   assert 'kk-panel-posts' in html, 'posts panel missing'
   assert 'kk-panel-stories' in html, 'stories panel missing'
   # Story 1 (olive #6b7a3a) → jasny tekst #f3ead7
   assert 'background-color: #6b7a3a; color: #f3ead7' in html, 'olive contrast failed'
   # Story 2 (mustard #c89a3a) → ciemny tekst #2a2420
   assert 'background-color: #c89a3a; color: #2a2420' in html, 'mustard contrast failed'
   # Cudzysłów escape
   assert '&quot;z cudzysłowem&quot;' in html, 'quote escape failed'
   # Newline jako HTML entity przepuszczone w data-copy-text
   assert '&amp;#10;' in html or '&#10;' in html, 'newline entity not in data-copy-text'
   print('render smoke OK')
   "
   ```

Jeśli któryś krok fail — zwróć szczegóły i wycofaj zmiany w `_preview.html` (najczęstsze przyczyny: błędny separator w bulk-posts, brak filter import).
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; .venv/bin/python manage.py check 2&gt;&amp;1 | grep -q "no issues" &amp;&amp; .venv/bin/python manage.py collectstatic --noinput --dry-run 2&gt;&amp;1 | grep -q "weekly_research_preview.css" &amp;&amp; .venv/bin/python manage.py collectstatic --noinput --dry-run 2&gt;&amp;1 | grep -q "weekly_research_preview.js" &amp;&amp; echo "validation OK"</automated>
  </verify>
  <done>manage.py check: 0 issues. collectstatic dry-run wymienia oba nowe pliki. Smoke render: preview HTML zawiera wszystkie 3 panele, contrast filter działa dla olive i mustard, cudzysłowy są poprawnie escapeowane.</done>
</task>

<task type="auto">
  <name>Task 7: Commit + push + deploy na MyDevil + remote smoke</name>
  <files></files>
  <action>
1. Atomic commit (jedna feature → jeden commit):

   ```bash
   cd /home/tomo/workspace/komitywa && \
   git add content/templatetags/__init__.py \
           content/templatetags/content_extras.py \
           content/static/content/admin/weekly_research_preview.css \
           content/static/content/admin/weekly_research_preview.js \
           content/templates/admin/content/weeklyresearch/change_form.html \
           content/templates/admin/content/weeklyresearch/_preview.html \
           content/admin.py && \
   git commit -m "feat(content): admin preview WeeklyResearch — tabbed UI z Copy to clipboard

   - Tabbed UI (Blog / IG Posty / IG Stories) jako CSS-only radio + ~ selector
   - Brand-styled (paper/ink/olive/terracotta/mustard) — zgodne z main.css
   - Stories jako pigułki 9:16 z dynamicznym kontrastem tekstu (filter text_color_for_bg)
   - Copy-to-clipboard buttons + bulk copy (cały blog Markdown, wszystkie posty, wszystkie stories)
   - Vanilla JS, zero deps; toast feedback (~1.5s)
   - Filter content_extras.text_color_for_bg z hardcoded mapping dla 5 brand colors"
   ```

2. Push do origin/main:
   ```bash
   git push origin main
   ```

3. Deploy przez SSH (paramiko, systemowy python3 — NIE z .venv żeby uniknąć konfliktu zależności):
   ```bash
   /usr/bin/python3 -c "
   import paramiko
   client = paramiko.SSHClient()
   client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
   client.connect('panel84.mydevil.net', username='jem3pizze', password='Tak12toto.', timeout=30)
   cmd = 'cd /usr/home/jem3pizze/domains/kuchennakomitywa.pl/public_python/ && bash ./deploy.sh 2>&1'
   stdin, stdout, stderr = client.exec_command(cmd, timeout=300)
   out = stdout.read().decode()
   err = stderr.read().decode()
   rc = stdout.channel.recv_exit_status()
   print('=== STDOUT ===')
   print(out[-3000:])
   print('=== STDERR ===')
   print(err[-1000:])
   print('=== EXIT', rc, '===')
   client.close()
   assert rc == 0, f'deploy.sh failed with rc={rc}'
   "
   ```

4. Remote smoke test — sprawdź check + curl admin URL (302 redirect to login = OK, oznacza że view zwraca poprawnie):
   ```bash
   /usr/bin/python3 -c "
   import paramiko
   client = paramiko.SSHClient()
   client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
   client.connect('panel84.mydevil.net', username='jem3pizze', password='Tak12toto.', timeout=30)
   cmd = 'cd /usr/home/jem3pizze/domains/kuchennakomitywa.pl/public_python/ && source venv/bin/activate 2>/dev/null || true; python manage.py check 2>&1; echo ---; curl -sI -o /dev/null -w \"%{http_code}\" https://kuchennakomitywa.pl/admin/content/weeklyresearch/ -L --max-redirs 0 2>&1; echo'
   stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
   out = stdout.read().decode()
   print(out)
   client.close()
   assert 'no issues' in out or 'System check identified no issues' in out, 'remote check failed'
   "
   ```
   Oczekiwane: `System check identified no issues` na remote + curl admin URL zwraca 302 (redirect do login) lub 200.

Jeśli deploy fail z powodu collectstatic / migration / czegokolwiek — zwróć tail logu (`out[-3000:]`). NIE rób force-push, NIE rollback bez ustalenia z userem.
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; git log -1 --pretty=format:"%s" | grep -q "feat(content): admin preview WeeklyResearch" &amp;&amp; git status --porcelain | grep -v "^?? " | wc -l | grep -q "^0$" &amp;&amp; echo "commit + clean tree OK"</automated>
  </verify>
  <done>Atomic commit z message zaczynającym się `feat(content): admin preview WeeklyResearch` istnieje na HEAD; tree czysty (poza ?? files); push do origin/main OK; deploy.sh exit 0 na MyDevil; remote `manage.py check` zielony; curl admin URL zwraca 302/200.</done>
</task>

</tasks>

<verification>
Po wszystkich tasks:

1. **Code-level (lokalnie):**
   - `manage.py check` → 0 issues
   - `collectstatic --dry-run` wymienia `content/admin/weekly_research_preview.css` + `.js`
   - Filter `text_color_for_bg` zwraca poprawne mapowania (Task 1 verify)
   - Templates loadują się przez `get_template()` (Task 4 verify)
   - Smoke render: olive → jasny tekst, mustard → ciemny tekst (Task 6 verify)

2. **Deploy-level (remote):**
   - deploy.sh exit 0
   - Remote `manage.py check` 0 issues
   - Curl `/admin/content/weeklyresearch/` zwraca 302 (login redirect) lub 200

3. **Manual smoke (user, post-deploy):**
   - Login do admin na produkcji
   - Otwórz dowolny rekord WeeklyResearch ze statusem `formatted`
   - Zobacz 3 zakładki, przełączaj między nimi (CSS-only)
   - Klik dowolny "Skopiuj" → tekst w clipboard + toast "Skopiowano!"
   - Stories: każdy story ma kolor tła z `bg_color` + czytelny tekst
</verification>

<success_criteria>
- [ ] `content/templatetags/__init__.py` + `content_extras.py` istnieją, filter `text_color_for_bg` zarejestrowany i zwraca poprawne kolory dla 5 brand hex + default
- [ ] `content/static/content/admin/weekly_research_preview.css` istnieje, ≥150 linii, używa brand palette, definiuje `.kk-panel-blog/posts/stories`, `aspect-ratio: 9/16` dla story cards, `.kk-toast` z transition
- [ ] `content/static/content/admin/weekly_research_preview.js` istnieje, valid JS syntax, IIFE, delegated click handler dla `[data-copy-text]`, używa `navigator.clipboard.writeText`, e.preventDefault
- [ ] `content/templates/admin/content/weeklyresearch/change_form.html` extenduje `admin/change_form.html`, linkuje CSS+JS przez `{% static %}`, includuje `_preview.html` w `after_field_sets` z warunkiem `{% if original.formatted_json %}`
- [ ] `content/templates/admin/content/weeklyresearch/_preview.html` loaduje `content_extras`, ma 3 panele (kk-panel-blog/posts/stories), 3 inputy radio + 3 labels, wszystkie buttony mają `type="button"` i `data-copy-text`, story card używa `|text_color_for_bg`
- [ ] `content/admin.py` ma `change_form_template = "admin/content/weeklyresearch/change_form.html"`, brak innych zmian
- [ ] `manage.py check` lokalnie 0 issues
- [ ] `collectstatic --dry-run` wymienia 2 nowe pliki
- [ ] Smoke render preview partial z fake data: olive bg → jasny tekst (#f3ead7), mustard bg → ciemny tekst (#2a2420), cudzysłowy escape jako `&quot;`
- [ ] Atomic commit `feat(content): admin preview WeeklyResearch — tabbed UI z Copy to clipboard` na origin/main
- [ ] deploy.sh exit 0 na panel84.mydevil.net
- [ ] Remote `manage.py check` 0 issues + admin URL zwraca 302/200
</success_criteria>

<output>
After completion, create `.planning/quick/260602-prf-admin-preview-weeklyresearch-tabbed-ui-b/260602-prf-SUMMARY.md` z:
- Co zostało zbudowane (tabs, copy, brand styling, contrast filter)
- Komendy do verify (lokalnie + remote)
- Manualne kroki dla usera (login do admin, otwórz rekord, sprawdź 3 zakładki + copy)
- Commit hash + deploy timestamp
</output>
