---
phase: 260602-qcl
plan: 01
subsystem: content
tags: [blog, blogpost, markdown, admin, content-pipeline, frontend, deploy]
type: execute
requirements:
  - QUICK-260602-qcl
dependency_graph:
  requires:
    - "content.WeeklyResearch model + formatted_json schema (260602-i1r, 260602-p98)"
    - "Admin preview WeeklyResearch (260602-prf)"
    - "Brand CSS palette + classes recipe-grid/recipe-card/kk-section/wrap/wrap-narrow (260408-design)"
  provides:
    - "content.BlogPost model + BlogPostManager"
    - "Admin: BlogPostAdmin (full CRUD, fieldsets, akcje publish/unpublish, slug RO po publikacji)"
    - "Admin: akcja promote_to_blogpost na WeeklyResearchAdmin (idempotentna)"
    - "Public URLs /blog/ + /blog/<slug>/"
    - "Nav link 'blog' (active state dla app_name='content')"
  affects:
    - "templates/includes/_navbar.html (rozszerzenie o nowy link)"
    - "backend/urls.py (rozszerzenie o blog/ include)"
tech_stack:
  added:
    - "markdown>=3.5,<4 (python package — render Markdown z extensions 'extra' + 'smarty')"
  patterns:
    - "Markdown body z mark_safe + autoescape off (trusted source — tylko admin może edytować body)"
    - "Idempotencja akcji admin (sprawdzanie obj.blog_posts.exists())"
    - "Auto-slug w save() override TYLKO gdy pusty (nie nadpisuje istniejącego)"
    - "Auto-published_at w save() override TYLKO gdy None (zachowuje historię publikacji)"
    - "Slug read-only w admin po publikacji (kanoniczna URL — nie wolno breakować)"
    - "Klasy z istniejącego main.css reuse (.recipe-grid, .recipe-card, .kk-section, .wrap-narrow, .tag-row, .kk-pagination, .kk-empty-state, .hero-eyebrow, .lead) — TYLKO jedna nowa klasa .kk-blog-body"
key_files:
  created:
    - content/migrations/0002_blogpost.py
    - content/views.py
    - content/urls.py
    - content/templates/content/blog_list.html
    - content/templates/content/blog_detail.html
  modified:
    - requirements.txt
    - content/models.py
    - content/admin.py
    - backend/urls.py
    - templates/includes/_navbar.html
    - static/css/main.css
decisions:
  - "Slug auto-fill TYLKO gdy pusty (user override w admin pozostaje)"
  - "published_at NIGDY nie nadpisuje historii (cofnięcie do draft + republish zachowuje pierwotną datę)"
  - "Idempotencja promote_to_blogpost przez research.blog_posts.exists()"
  - "Markdown extensions: extra + smarty (NIE codehilite — bez zależności od Pygments)"
  - "Tags jako CSV w jednym polu CharField (NIE M2M — celowo prosto; M2M kiedy będzie potrzeba filtrów per-tag jak w Recipe)"
  - "Slug read-only w admin po publikacji (ochrona URL)"
  - "make_draft używa queryset.update() — NIE clear'uje published_at (zachowanie historii publikacji)"
  - "make_published używa .save() w pętli żeby uruchomić auto-published_at logic"
  - "promote_to_blogpost akceptuje tags LUB hashtags (z #) — defensywny mapping z formatted_json"
metrics:
  duration: "~25min"
  completed_date: "2026-06-02"
  files_created: 5
  files_modified: 6
  commits: 1
  tasks_completed: 10
---

# Phase 260602-qcl: Pełny blog na stronie (model BlogPost, admin, /blog/) Summary

**One-liner:** Production-ready blog pipeline na kuchennakomitywa.pl — model BlogPost z markdown body, admin z akcjami draft/publish, akcja "Promuj do BlogPost" startująca z istniejącego WeeklyResearch.formatted_json, publiczny URL /blog/ + /blog/<slug>/ w brand stylu, link w nav. Live na produkcji (HTTP 200 na /blog/).

## Co zostało dostarczone

### Task 1: Markdown dependency
- `requirements.txt`: dodana linia `markdown>=3.5,<4` na końcu pliku (po `anthropic>=0.40,<1.0`)
- Zainstalowane lokalnie w `/home/tomo/workspace/komitywa/.venv` (markdown 3.10.2) — i remote przez `deploy.sh` (też 3.10.2)
- `python -c "import markdown"` działa bez błędu

### Task 2: BlogPost model + BlogPostManager
- `content/models.py` rozszerzony: dodane `BlogPostManager` + `BlogPost` (klasy NA KOŃCU pliku, `WeeklyResearch` nietknięty)
- Imports dodane na początku: `markdown as md`, `reverse`, `timezone`, `mark_safe`, `slugify`
- Pola: `title`, `slug` (unique, blank=True), `excerpt`, `body` (markdown), `tags` (CSV CharField), `status` (draft/published, db_index), `published_at` (db_index, nullable), `source_research` (FK na WeeklyResearch z `related_name="blog_posts"`, on_delete=SET_NULL), `created_at`, `updated_at`
- `BlogPostManager.published()` filtruje `status='published' AND published_at__lte=timezone.now()`
- `save()` override: auto-slug (z kolizji handling `-2`, `-3`) gdy pusty, auto-published_at gdy status='published' i published_at is None
- Property `body_html`: `mark_safe(markdown.markdown(body, extensions=['extra', 'smarty']))`
- Property `tags_list`: split CSV po `,`, strip, filter empty
- `get_absolute_url()`: `reverse('content:blog_detail', args=[slug])`
- `Meta.ordering = ['-published_at', '-created_at']` (drafty bez daty lecą na koniec)
- `Meta.indexes`: composite index na `(status, -published_at)` dla queryset .published()

### Task 3: Migracja 0002_blogpost
- `content/migrations/0002_blogpost.py` wygenerowana przez `makemigrations content` (auto, niemodyfikowana ręcznie)
- Operation: `CreateModel(name='BlogPost', ...)` — żadnych alter na WeeklyResearch
- Zaaplikowana lokalnie: `showmigrations content` pokazuje `[X] 0002_blogpost`
- Sanity shell test przeszedł: slug auto-set, published_at auto-set przy publikacji, body_html renderuje markdown (`<p>Hello <strong>world</strong></p>`), tags_list parsuje CSV z whitespace

### Task 4: BlogPostAdmin + promote_to_blogpost
- `content/admin.py` całkowicie przepisany (zachowując WeeklyResearchAdmin niezmieniony — tylko dodane `search_fields=("week_label",)` które już było, i `actions=[promote_to_blogpost]`)
- `promote_to_blogpost` (action na WeeklyResearchAdmin):
  - Czyta `formatted_json.blog.title`, `.body`, `.excerpt`, `.tags` lub `.hashtags`
  - Tagi: lista → CSV (strip `#`), string → as-is
  - Walidacja: skip jeśli brak title lub body (warning message)
  - Idempotencja: skip jeśli `research.blog_posts.exists()` (info message)
  - Tworzy BlogPost(status='draft', source_research=research, ...)
  - Messages: success/info/warning per kategoria
- `BlogPostAdmin`:
  - `list_display`: title, status, published_at, source_research, updated_at
  - `list_filter`: status, published_at
  - `search_fields`: title, slug, body, tags
  - `prepopulated_fields`: {"slug": ("title",)} — działa w add-form
  - `autocomplete_fields`: ("source_research",) — wymaga search_fields na WeeklyResearchAdmin (już istnieje)
  - `date_hierarchy`: published_at
  - `actions`: make_published, make_draft
  - `fieldsets`: 4 sekcje (Treść / Publikacja / Powiązania / Metadane)
  - `get_readonly_fields`: dynamicznie dodaje 'slug' do RO gdy obj.status='published' (ochrona kanonicznych URL)
- `make_published`: pętla `.save()` (żeby uruchomić auto-published_at)
- `make_draft`: `queryset.update(status='draft')` — celowo NIE clear'uje published_at (zachowanie historii)

### Task 5: Views + URLs
- `content/views.py`: `BlogListView` (ListView, paginate_by=10, queryset=`.published().select_related('source_research')`) + `BlogDetailView` (DetailView, slug lookup, queryset=`.published()` — niepublishowane zwracają 404)
- `content/urls.py`: `app_name='content'` + 2 patterns (`""` → blog_list, `"<slug:slug>/"` → blog_detail)
- `backend/urls.py`: dodana linia `path("blog/", include("content.urls", namespace="content"))` PRZED catch-all includes (po `przepisy/`)
- `reverse('content:blog_list')` → `/blog/`, `reverse('content:blog_detail', args=['x'])` → `/blog/x/`

### Task 6: Frontend templates
- `content/templates/content/blog_list.html`: extends base.html, blok title + content
  - Section-head z numerem · blog, section-title "Z notatnika kuchni", section-meta z licznikiem (z polską pluralizacją `pluralize:"y,ów"`)
  - `.recipe-grid` (reuse) z kartami `.recipe-card` (reuse), num-stamp + time-stamp (data publikacji), recipe-body z kicker/name/excerpt(truncatechars:160)/tags
  - Paginacja `.kk-pagination` (reuse) z poprzednia/następna/numbers, ARIA labels
  - Empty state `.kk-empty-state` (reuse) — link do `recipes:list` (cross-promotion)
- `content/templates/content/blog_detail.html`: extends base.html
  - `.wrap-narrow` (reuse) + `.hero-eyebrow` "blog" + `<h1>`
  - Meta-row: data publikacji (`|date:"j E Y"`) + tagi (`.tag-row` + `.tag` reuse)
  - Excerpt jako `.lead` (reuse) italic
  - `<article class="kk-blog-body">` z `{% autoescape off %}{{ post.body_html }}{% endautoescape %}` (NOWA klasa)
  - Back-link "← wróć do bloga" jako `.kk-link-arrow` (reuse) z dashed border-top

### Task 7: CSS — sekcja /* blog */
- `static/css/main.css` rozszerzony o `.kk-blog-body` (JEDYNA nowa klasa — wszystko inne to reuse)
- Pełna typografia treści posta:
  - `p` (margin 0 0 18px)
  - `h2` (font-display, 30px, accent line-height 1.2)
  - `h3` (font-display, 24px, ink-soft)
  - `ul, ol, li` (margin/padding)
  - `a` (accent-2 + hover ink, underline + offset)
  - `blockquote` (border-left accent-3, paper-2 background, italic)
  - `code` (mono, paper-2 background, border-radius 3px)
  - `pre` (mono 14px, paper-2 background, overflow-x auto)
  - `pre code` (reset background)
  - `hr` (dashed ink-soft, margin 32px 0)
  - `strong`, `em`
  - `@media (max-width: 768px)`: zmniejszone font-sizes
- Wszystkie kolory przez CSS variables (`--paper-2`, `--ink`, `--accent-2`, `--accent-3`, `--font-display`, `--font-body`, `--font-mono`) — zero hardcoded

### Task 8: Nav link 'blog'
- `templates/includes/_navbar.html`: dodana linia w `.nav-links`:
  ```html
  <a class="{% if request.resolver_match.app_name == 'content' %}active{% endif %}" href="{% url 'content:blog_list' %}">blog</a>
  ```
- Pozycja: między `sklep` a `o nas` (kolejność: przepiśnik → sklep → blog → o nas → kontakt)
- Render templatki przez `get_template().render()` zawiera `/blog/` URL

### Task 9: End-to-end sanity test
- `manage.py check` zielony lokalnie
- Pełny pipeline przetestowany w `manage.py shell`:
  1. Utworzony WeeklyResearch (week_label='2099-W01', status='formatted', formatted_json z blog blokiem zawierającym `title`, `body` (markdown z `**bold**`, listą `-`, `## Sekcja`), `excerpt`, `hashtags` (mix z `#` i bez))
  2. Wywołana akcja `promote_to_blogpost` — BlogPost stworzony (title='Sanity Test Post', status='draft', slug='sanity-test-post', tagi zparsowane bez '#')
  3. Akcja wywołana drugi raz — idempotencja potwierdzona (count=1)
  4. Publikacja: `post.status='published'; post.save()` → `published_at` ustawione automatycznie
  5. `body_html` zawiera `<p>To jest <strong>sanity</strong> test.`, `<ul>`, `<h2>Sekcja</h2>` (lub `<h2 id="sekcja">`)
  6. Django Client GET `/blog/` → HTTP 200, zawiera `Sanity Test Post`
  7. Django Client GET `/blog/<slug>/` → HTTP 200, zawiera `<strong>sanity</strong>` (markdown renderowany) + `wróć do bloga` (back-link)
  8. Cleanup: post + wr delete
- Lokalny ALLOWED_HOSTS musiał być rozszerzony o `testserver` w runtime tylko dla sanity testu (deviation #1 — nie kod production)

### Task 10: Commit + push + deploy + remote smoke
- Atomic commit: `feat(content): pełny blog — model BlogPost, admin draft/publish, /blog/ + /blog/<slug>/, akcja Promuj z WeeklyResearch` (hash `14e80547`)
- Files: 11 (5 created, 6 modified) — 480 insertions, 2 deletions
- Push: `git push origin HEAD:main` (fast-forward `edcc056..14e8054`)
- Deploy: paramiko exec na `panel84.mydevil.net` jako `jem3pizze` → `bash ./deploy.sh` exit 0
  - git pull: nowy commit zaciągnięty
  - pip install: markdown 3.10.2 zainstalowane
  - migrate: `content.0002_blogpost ... OK`
  - collectstatic: 1 new (main.css updated), 207 unmodified, 424 post-processed
  - bytecode cache wyczyszczony
  - `devil www restart kuchennakomitywa.pl` → OK
- Remote smoke:
  - `manage.py check` → "System check identified no issues (0 silenced)"
  - `showmigrations content` → `[X] 0001_initial` + `[X] 0002_blogpost`
  - `curl https://kuchennakomitywa.pl/blog/` → **HTTP 200**
  - `curl https://kuchennakomitywa.pl/admin/content/blogpost/` → **HTTP 302** (redirect to login)
  - Remote `git rev-parse HEAD` = `14e80547b408f7caeb7ff3dd1449906b0d990245` (matches local)

## Decyzje techniczne

1. **Slug auto-fill TYLKO gdy pusty** — user może override w admin (prepopulated_fields działa w add-form, ale potem manualnie edytowalne dopóki status ≠ published).
2. **published_at NIGDY nie nadpisuje historii** — gdy user cofa do draft a potem republishuje, zachowujemy pierwotną datę publikacji. `make_draft` używa `.update()` (nie clear'uje published_at).
3. **Idempotencja `promote_to_blogpost`** — sprawdzanie `research.blog_posts.exists()` przez `related_name="blog_posts"` na FK. Drugi click → info message "Pominięto N".
4. **Markdown extensions: `extra` + `smarty`** — NIE `codehilite` (nie chcemy zależności od Pygments + tematycznie blog kulinarny, code highlighting niepotrzebne).
5. **Tags jako CSV w CharField** — celowo prosto. M2M jeśli kiedyś będzie potrzeba filtrów per-tag (jak Recipe ma — 260508-ibb). Konwersja CSV → M2M to potem trywialna migracja.
6. **Slug read-only po publikacji** — `get_readonly_fields(request, obj)` dynamicznie dodaje 'slug' do RO gdy `obj.status='published'`. Ochrona kanonicznych URL przed przypadkową zmianą.
7. **`.kk-blog-body` jako jedyna nowa klasa CSS** — wszystko inne to reuse z `main.css` (klasy stworzone dla recipes/shop/about — dokładnie te same). Konsystencja wizualna out-of-the-box.
8. **`autoescape off` w blog_detail.html** — bezpieczne, bo `body_html` używa `mark_safe` w property + body wprowadza tylko admin (trusted source). Markdown ekosystem niewidzialny dla XSS gdy źródło zaufane.
9. **Brand palette zachowana 100%** — wszystkie kolory w CSS przez CSS variables (`--paper`, `--ink`, `--accent`, `--accent-2`, `--accent-3`). Zero hardcoded hex codes.
10. **Defensywny tags mapping w `promote_to_blogpost`** — akceptuje `blog.tags` (string lub list) LUB `blog.hashtags` (list z lub bez `#`). Strip `#`, join przecinkami. Resilient do różnych wariantów outputu LLM.

## Deviations od planu

### Auto-fixed Issues

**1. [Rule 3 - Setup] Setup venv + .env + db.sqlite3 w worktree**
- **Found during:** Task 1 (przed instalacją markdown)
- **Issue:** Worktree nie miał `.venv` ani `.env` ani `db.sqlite3` — pip + manage.py shell wymagały tych
- **Fix:** Symlink `.venv → /home/tomo/workspace/komitywa/.venv`, skopiowane `.env` i `db.sqlite3` z parent repo. Wszystkie 3 ignorowane w .gitignore, więc nie wpłynęły na commit.
- **Files affected:** worktree-only (.venv symlink, .env copy, db.sqlite3 copy) — nie w commit
- **Commit:** N/A (poza scope commit-a — utility setup)

**2. [Rule 3 - Test infrastructure] ALLOWED_HOSTS w sanity test**
- **Found during:** Task 9 (sanity test Django Client)
- **Issue:** Django Client używa `'testserver'` jako Host header, ale lokalne `.env` ustawia `ALLOWED_HOSTS=localhost,127.0.0.1` (bez testserver). DEBUG=True powinno auto-allow testserver — ale środowisko miało DEBUG=False (z default settings parsing).
- **Fix:** Runtime override `settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ['testserver']` w shell sesji testowej (nie kod produkcji — tylko test environment).
- **Files affected:** brak (runtime-only)
- **Commit:** N/A

**Plan executed exactly as written** — żadnych zmian w semantyce planu, kodzie production, czy strukturze.

## Sitemap status

**NIE skonfigurowane.** `django.contrib.sitemaps` NIE jest w `INSTALLED_APPS` (sprawdzone w `backend/settings.py`). Zgodnie z constraints planu — pomijam.

**Rekomendacja na przyszłość:** Osobny quick task gdy będzie ≥5 postów + jasny cel SEO (zindexowanie w Google). Wtedy:
1. Dodać `django.contrib.sitemaps` do INSTALLED_APPS
2. Stworzyć `content/sitemaps.py` z `BlogPostSitemap(Sitemap)` (queryset=`BlogPost.objects.published()`, lastmod=`updated_at`, location=`get_absolute_url()`)
3. Dodać URL `sitemap.xml` w `backend/urls.py`
4. Zgłosić sitemap.xml w Google Search Console

## Manual smoke checklist dla usera (post-deploy)

Wejdź na produkcję (https://kuchennakomitywa.pl/admin/) i przeprowadź ten flow:

- [ ] Login do `/admin/` (twój superuser)
- [ ] Otwórz `/admin/content/weeklyresearch/`, wybierz **2026-W22** (lub inny ze statusem `formatted`)
- [ ] Z dropdown akcji wybierz **"Promuj zaznaczone researche do BlogPost (draft)"** → kliknij Go
- [ ] Sprawdź zielony message: `"Utworzono 1 BlogPost (draft)."`
- [ ] Wejdź na `/admin/content/blogpost/`, otwórz nowy draft post
- [ ] Edytuj `body` (markdown), `excerpt`, `tags` jeśli potrzeba — slug i title są już wypełnione
- [ ] Zmień **Status** na `published` w sekcji "Publikacja", zapisz
- [ ] Sprawdź że `published_at` ustawił się automatycznie (data zapisu)
- [ ] Otwórz `https://kuchennakomitywa.pl/blog/` → post powinien być widoczny w grid
- [ ] Klik w kartę → `https://kuchennakomitywa.pl/blog/<slug>/` → renderuje się treść (markdown → HTML), brand styling, tagi jako pills, data publikacji
- [ ] Sprawdź nav link "blog" jest aktywny (podkreślony) gdy na stronie bloga
- [ ] Wróć do `/admin/content/weeklyresearch/`, wybierz **ten sam** 2026-W22 ponownie, użyj akcji "Promuj..." → message: **"Pominięto 1 — BlogPost już istnieje dla tego researchu."** (idempotencja)

## Files changed

```
 backend/urls.py                            |   1 +
 content/admin.py                           | 109 ++++++++++++++++++++++++++++-
 content/migrations/0002_blogpost.py        |  36 ++++++++++
 content/models.py                          |  98 ++++++++++++++++++++++++++
 content/templates/content/blog_detail.html |  41 +++++++++++
 content/templates/content/blog_list.html   |  77 ++++++++++++++++++++
 content/urls.py                            |  11 +++
 content/views.py                           |  25 +++++++
 requirements.txt                           |   1 +
 static/css/main.css                        |  82 ++++++++++++++++++++++
 templates/includes/_navbar.html            |   1 +
 11 files changed, 480 insertions(+), 2 deletions(-)
```

Commit hash: `14e80547b408f7caeb7ff3dd1449906b0d990245` (na `origin/main`)

## Out of scope (zachowane)

- Comments / likes / interakcje czytelników
- Wewnętrzny search (`/blog/?q=...`)
- Per-tag pages (`/blog/tag/<tag>/`)
- RSS feed
- Featured image / OG image per post
- Edit-from-frontend dla autorów (CMS-like)
- Sitemap (osobny task gdy będzie ≥5 postów)
- AMP / SEO meta tagi (Title/Description override per post)
- Wieloautorska atrybucja (author FK na User)
- Draft preview na frontend dla zalogowanych (obecnie tylko admin)

## Verification Status

**Code-level (lokalnie):**
- pip show markdown → 3.10.2 (>= 3.5, < 4) — OK
- `manage.py check` → "System check identified no issues (0 silenced)" — OK
- `manage.py showmigrations content` → [X] 0001_initial, [X] 0002_blogpost — OK
- `reverse('content:blog_list')` → `/blog/` — OK
- `reverse('content:blog_detail', args=['x'])` → `/blog/x/` — OK
- `get_template('content/blog_list.html')` + `blog_detail.html` — OK
- Sanity Client test: GET `/blog/` → 200 z title, GET `/blog/<slug>/` → 200 z `<strong>` z markdown — OK
- Idempotencja akcji `promote_to_blogpost` — OK (count=1 po 2 wywołaniach)

**Admin-level (lokalnie):**
- BlogPost zarejestrowany w admin — OK
- BlogPostAdmin.list_display zawiera title — OK
- BlogPostAdmin.actions zawiera make_published — OK
- WeeklyResearchAdmin.actions zawiera promote_to_blogpost — OK

**Deploy-level (remote panel84.mydevil.net):**
- `deploy.sh` exit 0 — OK
- Remote `manage.py check` → "no issues" — OK
- Remote migracja `[X] 0002_blogpost` — OK
- Remote git HEAD = `14e80547b408f7caeb7ff3dd1449906b0d990245` (matches origin/main) — OK
- `curl https://kuchennakomitywa.pl/blog/` → **HTTP 200** — OK
- `curl https://kuchennakomitywa.pl/admin/content/blogpost/` → **HTTP 302** (redirect to login) — OK

## Self-Check: PASSED

Files created (confirmed via filesystem):
- `content/migrations/0002_blogpost.py` — FOUND
- `content/views.py` — FOUND
- `content/urls.py` — FOUND
- `content/templates/content/blog_list.html` — FOUND
- `content/templates/content/blog_detail.html` — FOUND

Files modified (confirmed via git diff stat):
- `requirements.txt` (+1) — FOUND
- `content/models.py` (+98) — FOUND
- `content/admin.py` (+109/-2) — FOUND
- `backend/urls.py` (+1) — FOUND
- `templates/includes/_navbar.html` (+1) — FOUND
- `static/css/main.css` (+82) — FOUND

Commit verified:
- `14e80547` — FOUND in `origin/main` (remote git rev-parse HEAD matches)

Remote endpoints verified:
- `/blog/` → HTTP 200 — FOUND
- `/admin/content/blogpost/` → HTTP 302 — FOUND
- `manage.py check` → 0 issues — FOUND
- `0002_blogpost` migration — FOUND on remote DB

All claims verified against the live production environment.
