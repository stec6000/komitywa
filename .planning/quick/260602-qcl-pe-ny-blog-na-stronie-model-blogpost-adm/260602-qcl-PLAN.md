---
phase: 260602-qcl
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - requirements.txt
  - content/models.py
  - content/migrations/0002_blogpost.py
  - content/admin.py
  - content/views.py
  - content/urls.py
  - content/templates/content/blog_list.html
  - content/templates/content/blog_detail.html
  - backend/urls.py
  - templates/includes/_navbar.html
  - static/css/main.css
autonomous: true
requirements:
  - QUICK-260602-qcl
must_haves:
  truths:
    - "Model BlogPost istnieje w content/models.py z polami: title, slug (unique), excerpt, body (markdown), tags (CSV), status (draft/published), published_at, source_research (FK -> WeeklyResearch, nullable), created_at, updated_at"
    - "BlogPost.objects.published() filtruje status='published' AND published_at__lte=timezone.now()"
    - "save() override: auto-slug z title (tylko gdy pusty), auto-published_at = timezone.now() (tylko gdy status='published' i published_at is None)"
    - "Property body_html zwraca mark_safe(markdown.markdown(body, extensions=['extra', 'smarty']))"
    - "Property tags_list zwraca [t.strip() for t in tags.split(',') if t.strip()]"
    - "get_absolute_url() zwraca reverse('content:blog_detail', args=[slug])"
    - "Migracja 0002_blogpost.py utworzona przez makemigrations i applied przez migrate (lokalnie + remote)"
    - "Admin /admin/content/blogpost/ pokazuje list view z kolumnami title, status, published_at, source_research, akcje 'Publikuj'/'Cofnij do draft'"
    - "Admin /admin/content/blogpost/<id>/change/ ma prepopulated slug, fieldsets (Treść / Publikacja / Powiązania / Metadane), readonly created_at/updated_at"
    - "Akcja w WeeklyResearchAdmin 'Promuj do BlogPost' tworzy BlogPost(source_research=obj, title=blog['title'], body=blog['body'], excerpt=blog['excerpt'], tags=','.join(blog['hashtags' lub 'tags']), status='draft'); idempotentna (jeśli BlogPost(source_research=obj) istnieje -> messages.info skip)"
    - "Strona /blog/ renderuje listę BlogPost.objects.published() z paginacją 10/stronę, brand-styled grid kart"
    - "Strona /blog/<slug>/ renderuje pojedynczy post: title, published_at, excerpt, body_html, tags jako #tag pills, link 'wróć do bloga'"
    - "Nav w _navbar.html ma link 'blog' wskazujący na {% url 'content:blog_list' %} z aktywnym stanem gdy app_name == 'content'"
    - "requirements.txt zawiera `markdown>=3.5,<4`, zainstalowane w lokalnym .venv (lub user venv)"
    - "Deploy: kod na origin/main, panel84.mydevil.net zaktualizowany przez deploy.sh, remote `python manage.py check` zielony"
    - "Remote curl https://kuchennakomitywa.pl/blog/ zwraca HTTP 200"
    - "Remote curl -I https://kuchennakomitywa.pl/admin/content/blogpost/ zwraca 302 (redirect to login)"
  artifacts:
    - path: "requirements.txt"
      provides: "Pinned markdown dependency"
      contains: "markdown>=3.5,<4"
    - path: "content/models.py"
      provides: "BlogPost model + BlogPostManager + Meta + save override + properties + get_absolute_url"
      contains: "class BlogPost"
      min_lines: 60
    - path: "content/migrations/0002_blogpost.py"
      provides: "Auto-generated migration tworząca tabelę content_blogpost"
      contains: "name='BlogPost'"
    - path: "content/admin.py"
      provides: "BlogPostAdmin (full set: list_display, list_filter, search_fields, prepopulated_fields, fieldsets, akcje make_published/make_draft) + akcja promote_to_blogpost w WeeklyResearchAdmin"
      contains: "class BlogPostAdmin"
    - path: "content/views.py"
      provides: "BlogListView (paginator 10) + BlogDetailView (slug lookup, published only)"
      contains: "class BlogListView"
    - path: "content/urls.py"
      provides: "app_name='content' + 2 patterns: '' -> blog_list, '<slug>/' -> blog_detail"
      contains: "app_name = \"content\""
    - path: "content/templates/content/blog_list.html"
      provides: "Lista postów z paginacją, brand-styled grid, extends base.html"
      contains: "{% extends \"base.html\" %}"
    - path: "content/templates/content/blog_detail.html"
      provides: "Pojedynczy post: title, meta, body_html (autoescape off), tags pills, link wróć"
      contains: "{% extends \"base.html\" %}"
    - path: "backend/urls.py"
      provides: "Routing zawiera path('blog/', include('content.urls', namespace='content'))"
      contains: "content.urls"
    - path: "templates/includes/_navbar.html"
      provides: "Nav link 'blog' przed/po 'sklep' z aktywnym stanem"
      contains: "content:blog_list"
    - path: "static/css/main.css"
      provides: "(opcjonalne) sekcja /* blog */ — TYLKO jeśli istniejące klasy nie wystarczają. Wykorzystać .recipe-grid / .recipe-card / .kk-section / .kk-empty-state / .tag-row jako reuse."
  key_links:
    - from: "content/admin.py (promote_to_blogpost)"
      to: "content/models.py (BlogPost)"
      via: "BlogPost.objects.create(source_research=obj, ...)"
      pattern: "BlogPost\\.objects\\.create.*source_research"
    - from: "content/models.py (BlogPost.save)"
      to: "django.utils.text.slugify"
      via: "auto-slug gdy self.slug pusty"
      pattern: "slugify\\(self\\.title\\)"
    - from: "content/models.py (BlogPost.body_html)"
      to: "markdown package + django.utils.safestring.mark_safe"
      via: "markdown.markdown(body, extensions=['extra', 'smarty'])"
      pattern: "markdown\\.markdown.*extensions"
    - from: "content/views.py"
      to: "content/models.py (BlogPost.objects.published)"
      via: "queryset w BlogListView.get_queryset() i BlogDetailView.get_queryset()"
      pattern: "BlogPost\\.objects\\.published\\(\\)"
    - from: "content/templates/content/blog_detail.html"
      to: "BlogPost.body_html"
      via: "{% autoescape off %}{{ post.body_html }}{% endautoescape %}"
      pattern: "body_html"
    - from: "backend/urls.py"
      to: "content/urls.py"
      via: "path('blog/', include('content.urls', namespace='content'))"
      pattern: "content\\.urls"
    - from: "templates/includes/_navbar.html"
      to: "content:blog_list"
      via: "{% url 'content:blog_list' %}"
      pattern: "content:blog_list"
---

<objective>
Pełny blog na stronie kuchennakomitywa.pl — model `BlogPost`, admin z dropdown akcjami draft/publish, akcja "Promuj do BlogPost" startująca z istniejącego `WeeklyResearch.formatted_json['blog']`, frontend `/blog/` (lista paginowana) + `/blog/<slug>/` (post w brand stylu), link w nav. Wszystko po polsku, na Django templates, brand palette (paper/ink/olive/terracotta/mustard).

Purpose: Domknięcie pipeline'u contentowego. Po `run_weekly_research` user ma research → admin preview (już istnieje) → jeden klik "Promuj do BlogPost" → edycja w admin (slug, body markdown, tagi CSV) → publikacja → live na `/blog/<slug>/`. Bez SPA, bez RSS, bez kategorii — tylko czysty czytelny blog.

Output: 11 zmodyfikowanych/nowych plików (1 dep, 1 model, 1 migracja, 1 admin, 1 views, 1 urls, 2 templates frontend, 1 backend urls, 1 nav, opcj. 1 css). Po deploy działający `/blog/` na produkcji, admin gotowy do tworzenia postów z `WeeklyResearch` lub od zera.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md

# Existing model (referencja stylu — BlogPost idzie OBOK, nie zamiast)
@content/models.py

# Existing admin (rozszerzamy — DODAJEMY BlogPostAdmin + akcję w WeeklyResearchAdmin)
@content/admin.py

# Initial migration (do referencji formy — nowa migracja będzie 0002_blogpost.py)
@content/migrations/0001_initial.py

# Routing (rozszerzamy o path("blog/", include("content.urls", namespace="content")))
@backend/urls.py

# Settings (potwierdzone: TEMPLATES APP_DIRS=True, LANGUAGE_CODE='pl', TIME_ZONE='Europe/Warsaw', USE_TZ=True)
@backend/settings.py

# Existing requirements (dodajemy markdown>=3.5,<4)
@requirements.txt

# Base template (extends base.html, blok content + title; blok extra_css/extra_js optional)
@templates/base.html

# Nav (rozszerzamy o link 'blog')
@templates/includes/_navbar.html

# Brand palette + reusable classes (.kk-section, .wrap, .recipe-grid, .recipe-card, .tag-row, .kk-empty-state)
@static/css/main.css

# Reference styling — templates/recipes/list.html i detail.html używają tych klas
@templates/recipes/list.html
@templates/recipes/detail.html

# Deploy script — odpalany na serwerze (git pull, pip install, migrate, collectstatic, restart)
@deploy.sh

<interfaces>
<!-- Kluczowe sygnatury, których executor potrzebuje. -->

From content/models.py (istniejące):
```python
class WeeklyResearch(models.Model):
    STATUS_CHOICES = [("pending", ...), ("research_done", ...), ("formatted", ...), ("failed", ...)]
    week_label = CharField(max_length=16, unique=True, db_index=True)
    formatted_json = JSONField(null=True, blank=True)  # {"blog": {"title": ..., "body": ..., "excerpt": ..., "hashtags": [...]}, "posts": [...], "stories": [...]}
    status = CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    # ...
```

From content/admin.py (istniejące):
```python
@admin.register(WeeklyResearch)
class WeeklyResearchAdmin(admin.ModelAdmin):
    change_form_template = "admin/content/weeklyresearch/change_form.html"
    list_display = ("week_label", "date_from", "date_to", "status", "created_at")
    # ...
```

From content/urls.py — będzie utworzony (analogia do recipes/urls.py):
```python
app_name = "content"
urlpatterns = [
    path("", views.BlogListView.as_view(), name="blog_list"),
    path("<slug:slug>/", views.BlogDetailView.as_view(), name="blog_detail"),
]
```

From backend/urls.py — będzie rozszerzony o:
```python
path("blog/", include("content.urls", namespace="content")),
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Dodaj markdown do requirements.txt i zainstaluj w aktywnym venv</name>
  <files>requirements.txt</files>
  <action>
Dopisz na końcu pliku `requirements.txt` linię:
```
markdown>=3.5,<4
```
NIE zmieniaj kolejności istniejących pakietów. Po zapisie pliku zainstaluj lokalnie:
```bash
cd /home/tomo/workspace/komitywa
. .venv/bin/activate 2>/dev/null || python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```
Jeśli `.venv` nie istnieje i pip nie ma uprawnień systemowych, użyj `python3 -m venv .venv`, potem `source .venv/bin/activate`, potem `pip install -r requirements.txt`. NIE używaj `--break-system-packages` na systemowym pythonie.

Cel: mieć `import markdown` działający w środowisku, którego używasz w kolejnych taskach do `manage.py shell` / `manage.py check`.
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; grep -q "^markdown&gt;=3.5,&lt;4$" requirements.txt &amp;&amp; (. .venv/bin/activate 2&gt;/dev/null; python3 -c "import markdown; print(markdown.__version__)") &amp;&amp; echo "markdown OK"</automated>
  </verify>
  <done>requirements.txt zawiera dokładnie linię `markdown>=3.5,<4` na końcu; lokalne venv pozwala `import markdown` bez błędu (markdown 3.5+).</done>
</task>

<task type="auto">
  <name>Task 2: Dodaj model BlogPost + BlogPostManager do content/models.py</name>
  <files>content/models.py</files>
  <action>
Rozszerz istniejący `content/models.py` o klasę `BlogPost` (NIE usuwaj `WeeklyResearch`, NIE modyfikuj jego pól). Dodaj na początku pliku imports:
```python
import markdown as md
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.text import slugify
```
(zachowaj istniejący `from django.db import models`).

Na końcu pliku (po klasie `WeeklyResearch`) dopisz dwie nowe klasy:

```python
class BlogPostManager(models.Manager):
    def published(self):
        return self.filter(
            status="published",
            published_at__lte=timezone.now(),
        )


class BlogPost(models.Model):
    STATUS_CHOICES = [
        ("draft", "draft"),
        ("published", "published"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    excerpt = models.TextField(
        blank=True,
        default="",
        help_text="Krótki lead 1-2 zdania (max 300 znaków).",
    )
    body = models.TextField(
        help_text="Markdown. Wspierane rozszerzenia: extra, smarty.",
    )
    tags = models.CharField(
        max_length=300,
        blank=True,
        default="",
        help_text="Tagi rozdzielone przecinkami, np. 'wegan, brownie, sezon'.",
    )
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default="draft",
        db_index=True,
    )
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    source_research = models.ForeignKey(
        WeeklyResearch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blog_posts",
        help_text="Źródłowy WeeklyResearch, jeśli post powstał z 'Promuj do BlogPost'.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = BlogPostManager()

    class Meta:
        verbose_name = "Blog post"
        verbose_name_plural = "Blog posts"
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "-published_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.status})"

    def save(self, *args, **kwargs):
        # Auto-slug TYLKO jeśli pusty (user może sam wpisać własny w admin)
        if not self.slug and self.title:
            base = slugify(self.title)[:200] or "post"
            slug = base
            i = 2
            # Kolizje: BlogPost o tym slugu (ale nie my sami)
            qs = BlogPost.objects.filter(slug=slug).exclude(pk=self.pk)
            while qs.exists():
                slug = f"{base}-{i}"
                i += 1
                qs = BlogPost.objects.filter(slug=slug).exclude(pk=self.pk)
            self.slug = slug
        # Auto-published_at TYLKO jeśli status='published' i published_at jest None
        # (nigdy nie nadpisuj historii — gdy user cofa do draft a potem publikuje
        #  ponownie, zachowujemy pierwotną datę publikacji.)
        if self.status == "published" and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("content:blog_detail", args=[self.slug])

    @property
    def tags_list(self):
        return [t.strip() for t in (self.tags or "").split(",") if t.strip()]

    @property
    def body_html(self):
        html = md.markdown(self.body or "", extensions=["extra", "smarty"])
        return mark_safe(html)
```

Uwagi:
- Import `markdown as md` (alias) bo `markdown` jako nazwa modułu kolidowała w przeszłości w innych projektach z lokalnymi nazwami; alias jest defensywny.
- `db_index=True` na `status` i `published_at` bo będą używane w `.published()` queryset (filter + ordering).
- `ordering = ["-published_at", "-created_at"]` zapewnia, że posty bez `published_at` (drafty) lecą na koniec, a opublikowane sortują się po dacie publikacji.
- `related_name="blog_posts"` na FK — pozwoli z `WeeklyResearchAdmin.promote_to_blogpost` sprawdzić idempotencję przez `obj.blog_posts.exists()`.

NIE modyfikuj klasy `WeeklyResearch`. NIE dodawaj `@admin.action` decoratorów tutaj — admin idzie do Task 4.
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; (. .venv/bin/activate 2&gt;/dev/null; python3 -c "
import django, os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()
from content.models import BlogPost, BlogPostManager, WeeklyResearch
assert isinstance(BlogPost.objects, BlogPostManager)
fields = {f.name for f in BlogPost._meta.get_fields()}
required = {'title','slug','excerpt','body','tags','status','published_at','source_research','created_at','updated_at'}
missing = required - fields
assert not missing, f'missing fields: {missing}'
assert hasattr(BlogPost, 'body_html')
assert hasattr(BlogPost, 'tags_list')
assert hasattr(BlogPost, 'get_absolute_url')
print('BlogPost model OK')
")</automated>
  </verify>
  <done>`content/models.py` zawiera klasy `BlogPostManager` i `BlogPost` z wszystkimi polami, properties (tags_list, body_html), save() override, get_absolute_url(). `WeeklyResearch` nietknięty. Verify script kończy się "BlogPost model OK".</done>
</task>

<task type="auto">
  <name>Task 3: Wygeneruj migrację 0002_blogpost.py i zaaplikuj lokalnie</name>
  <files>content/migrations/0002_blogpost.py</files>
  <action>
Wygeneruj migrację automatycznie i zaaplikuj:
```bash
cd /home/tomo/workspace/komitywa
. .venv/bin/activate
python manage.py makemigrations content
python manage.py migrate content
```

Oczekiwany output `makemigrations`:
```
Migrations for 'content':
  content/migrations/0002_blogpost.py
    + Create model BlogPost
```

Oczekiwany output `migrate`:
```
Operations to perform:
  Apply all migrations: ... content
Running migrations:
  Applying content.0002_blogpost... OK
```

NIE modyfikuj ręcznie wygenerowanego pliku migracji. Jeśli Django chce zmienić nazwę z `0002_blogpost.py` na coś innego (np. `0002_blogpost_alter_*`) — zaakceptuj, ale upewnij się że jedynym `operation` w pliku jest `CreateModel` na `BlogPost` (bez przypadkowych alter na WeeklyResearch). Jeśli widzisz inne operacje — zatrzymaj się, zbadaj dlaczego (prawdopodobnie zostawiłeś przypadkową zmianę w modelu WeeklyResearch).

Po migracji sprawdź że tabela istnieje:
```bash
python manage.py shell -c "
from content.models import BlogPost
from django.utils import timezone
p = BlogPost(title='Test post', body='Hello **world**', status='draft')
p.save()
assert p.slug == 'test-post', f'unexpected slug: {p.slug}'
assert p.published_at is None, 'draft should not have published_at'
p.status = 'published'
p.save()
assert p.published_at is not None, 'publish should auto-set published_at'
assert '<p>Hello <strong>world</strong></p>' in p.body_html, f'unexpected body_html: {p.body_html}'
assert p.tags_list == [], 'empty tags_list'
p.tags = 'wegan, brownie ,  sezon  '
assert p.tags_list == ['wegan', 'brownie', 'sezon'], f'tags_list: {p.tags_list}'
p.delete()
print('sanity OK')
"
```

NIE commituj jeszcze (commit idzie w Task 10).
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; test -f content/migrations/0002_blogpost.py &amp;&amp; (. .venv/bin/activate 2&gt;/dev/null; python manage.py migrate content --check 2&gt;&amp;1 | grep -qE "(No planned migration|is consistent|0 unapplied)") &amp;&amp; echo "migration applied" || (. .venv/bin/activate 2&gt;/dev/null; python manage.py showmigrations content | grep -q "\[X\] 0002_blogpost") &amp;&amp; echo "migration applied (via showmigrations)"</automated>
  </verify>
  <done>Plik `content/migrations/0002_blogpost.py` istnieje, zawiera operation `CreateModel(name='BlogPost', ...)`, jest applied (showmigrations pokazuje [X]); sanity shell test przeszedł (slug, published_at, body_html, tags_list).</done>
</task>

<task type="auto">
  <name>Task 4: Rozszerz content/admin.py — BlogPostAdmin + akcja promote_to_blogpost w WeeklyResearchAdmin</name>
  <files>content/admin.py</files>
  <action>
Rozszerz `content/admin.py`. NIE usuwaj `change_form_template`, `list_display` etc. z `WeeklyResearchAdmin` — DODAJ tylko `actions` z `promote_to_blogpost`.

Wersja docelowa:

```python
from django.contrib import admin, messages

from .models import BlogPost, WeeklyResearch


@admin.action(description="Promuj zaznaczone researche do BlogPost (draft)")
def promote_to_blogpost(modeladmin, request, queryset):
    created = 0
    skipped = 0
    failed = 0
    for research in queryset:
        # Idempotencja: jeśli już istnieje BlogPost z source_research=research, skip
        if research.blog_posts.exists():
            skipped += 1
            continue
        data = research.formatted_json or {}
        blog = data.get("blog") or {}
        title = (blog.get("title") or "").strip()
        body = (blog.get("body") or "").strip()
        excerpt = (blog.get("excerpt") or "").strip()
        # tagi mogą być w "tags" lub "hashtags" — bierzemy co jest
        raw_tags = blog.get("tags") or blog.get("hashtags") or []
        if isinstance(raw_tags, str):
            tags = raw_tags
        else:
            # lista — może mieć "#" na początku, usuń
            tags = ", ".join(str(t).lstrip("#").strip() for t in raw_tags if str(t).strip())
        if not title or not body:
            failed += 1
            continue
        BlogPost.objects.create(
            title=title[:200],
            body=body,
            excerpt=excerpt[:300] if excerpt else "",
            tags=tags[:300] if tags else "",
            status="draft",
            source_research=research,
        )
        created += 1
    if created:
        messages.success(request, f"Utworzono {created} BlogPost (draft).")
    if skipped:
        messages.info(request, f"Pominięto {skipped} — BlogPost już istnieje dla tego researchu.")
    if failed:
        messages.warning(request, f"Pominięto {failed} — brak title/body w formatted_json.blog.")


@admin.register(WeeklyResearch)
class WeeklyResearchAdmin(admin.ModelAdmin):
    change_form_template = "admin/content/weeklyresearch/change_form.html"
    list_display = ("week_label", "date_from", "date_to", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("week_label",)
    readonly_fields = ("raw_research", "formatted_json", "created_at", "updated_at")
    ordering = ("-date_to",)
    actions = [promote_to_blogpost]


@admin.action(description="Opublikuj zaznaczone posty")
def make_published(modeladmin, request, queryset):
    count = 0
    for post in queryset:
        if post.status != "published":
            post.status = "published"
            post.save()  # save() ustawi published_at jeśli None
            count += 1
    messages.success(request, f"Opublikowano {count} post(ów).")


@admin.action(description="Cofnij do draft")
def make_draft(modeladmin, request, queryset):
    updated = queryset.update(status="draft")
    messages.success(request, f"Cofnięto do draft: {updated} post(ów).")


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "published_at", "source_research", "updated_at")
    list_filter = ("status", "published_at")
    search_fields = ("title", "slug", "body", "tags")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("source_research",)
    date_hierarchy = "published_at"
    ordering = ("-published_at", "-created_at")
    actions = [make_published, make_draft]
    fieldsets = (
        ("Treść", {
            "fields": ("title", "slug", "excerpt", "body", "tags"),
            "description": "Body w Markdown (extensions: extra, smarty). Tagi po przecinku.",
        }),
        ("Publikacja", {
            "fields": ("status", "published_at"),
            "description": "Status=published auto-ustawia published_at (jeśli puste). Nigdy nie nadpisuje istniejącej daty.",
        }),
        ("Powiązania", {
            "fields": ("source_research",),
            "classes": ("collapse",),
        }),
        ("Metadane", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        ro = ["created_at", "updated_at"]
        # Po publikacji slug staje się read-only (kanonzina URL — nie wolno breakować)
        if obj and obj.status == "published":
            ro.append("slug")
        return ro
```

Uwagi:
- `WeeklyResearchAdmin` ma teraz `search_fields = ("week_label",)` — to było WYMAGANE wcześniej, ale też pozwoli `autocomplete_fields=("source_research",)` w `BlogPostAdmin` zadziałać (autocomplete wymaga search_fields na target modelu).
- `prepopulated_fields` działa TYLKO w add-form; na edit-form slug można edytować ręcznie (dopóki status != published).
- `make_draft` używa `queryset.update()` zamiast `.save()` w pętli — bo cofając do draft NIE chcemy clear'ować `published_at` (zachowujemy historię publikacji). To celowe.
- `make_published` używa `.save()` w pętli żeby uruchomić logikę auto-published_at z modelu.

NIE zmieniaj importów ani sygnatur w `change_form.html` (admin preview WeeklyResearch z prf-quick task — zostaje 1:1).
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; (. .venv/bin/activate 2&gt;/dev/null; python manage.py check 2&gt;&amp;1 | tee /tmp/check.out | grep -q "System check identified no issues") &amp;&amp; python3 -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend.settings')
django.setup()
from django.contrib import admin
from content.models import BlogPost, WeeklyResearch
assert BlogPost in admin.site._registry, 'BlogPost not registered'
bp_admin = admin.site._registry[BlogPost]
assert 'title' in bp_admin.list_display
assert any('make_published' in (getattr(a, '__name__', '') or '') for a in (bp_admin.actions or [])), f'make_published not in actions: {bp_admin.actions}'
wr_admin = admin.site._registry[WeeklyResearch]
assert any('promote_to_blogpost' in (getattr(a, '__name__', '') or '') for a in (wr_admin.actions or [])), f'promote_to_blogpost not in actions: {wr_admin.actions}'
print('admin OK')
"</automated>
  </verify>
  <done>`content/admin.py` rejestruje `BlogPost` z `BlogPostAdmin` (list_display, list_filter, prepopulated_fields, fieldsets, akcje make_published/make_draft). `WeeklyResearchAdmin` ma dodaną akcję `promote_to_blogpost` z idempotencją. `manage.py check` zielony.</done>
</task>

<task type="auto">
  <name>Task 5: Utwórz content/views.py + content/urls.py + dodaj include w backend/urls.py</name>
  <files>content/views.py, content/urls.py, backend/urls.py</files>
  <action>

**5a. content/views.py** (utworz nowy plik):
```python
from django.views.generic import DetailView, ListView

from .models import BlogPost


class BlogListView(ListView):
    model = BlogPost
    template_name = "content/blog_list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        return BlogPost.objects.published().select_related("source_research")


class BlogDetailView(DetailView):
    model = BlogPost
    template_name = "content/blog_detail.html"
    context_object_name = "post"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        # Tylko opublikowane są dostępne publicznie
        return BlogPost.objects.published()
```

**5b. content/urls.py** (utwórz nowy plik):
```python
from django.urls import path

from . import views


app_name = "content"

urlpatterns = [
    path("", views.BlogListView.as_view(), name="blog_list"),
    path("<slug:slug>/", views.BlogDetailView.as_view(), name="blog_detail"),
]
```

**5c. backend/urls.py** (zmodyfikuj — dodaj jedną linię):
W liście `urlpatterns`, po linii `path("przepisy/", include("recipes.urls", namespace="recipes")),` dodaj:
```python
    path("blog/", include("content.urls", namespace="content")),
```

Wersja docelowa fragmentu:
```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    path("przepisy/", include("recipes.urls", namespace="recipes")),
    path("blog/", include("content.urls", namespace="content")),
    path("", include("newsletter.urls")),
    path("", include("core.urls")),
    path("", include("shop.urls")),
]
```

NIE ruszaj `if settings.DEBUG: urlpatterns += ...` na końcu pliku.

Uwaga na kolejność: `blog/` musi być PRZED `path("", include("..."))` bo te ostatnie matchują puste prefix. (Tu nie ma kolizji, bo żaden z core/newsletter/shop nie ma URL'a zaczynającego się od `blog/`, ale konwencja: prefixed paths przed catch-all).
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; (. .venv/bin/activate 2&gt;/dev/null; python manage.py shell -c "
from django.urls import reverse
assert reverse('content:blog_list') == '/blog/', f\"unexpected: {reverse('content:blog_list')}\"
assert reverse('content:blog_detail', args=['test-post']) == '/blog/test-post/', f\"unexpected: {reverse('content:blog_detail', args=['test-post'])}\"
print('urls OK')
")</automated>
  </verify>
  <done>`content/views.py` z `BlogListView` (paginate_by=10, .published()) i `BlogDetailView` (slug lookup, .published() queryset). `content/urls.py` z `app_name='content'` + 2 patterns. `backend/urls.py` zawiera `path("blog/", include("content.urls", namespace="content"))` PRZED catch-all includes. `reverse('content:blog_list')` zwraca `/blog/`.</done>
</task>

<task type="auto">
  <name>Task 6: Utwórz templates frontendowe — blog_list.html + blog_detail.html w content/templates/content/</name>
  <files>content/templates/content/blog_list.html, content/templates/content/blog_detail.html</files>
  <action>

**6a. content/templates/content/blog_list.html** (utwórz nowy plik):
```html
{% extends "base.html" %}
{% load static %}

{% block title %}Blog — Kuchenna Komitywa{% endblock %}

{% block content %}
<section class="kk-section" aria-label="Blog">
    <div class="wrap">
        <div class="section-head">
            <div>
                <div class="section-number">· blog</div>
                <h2 class="section-title">Z notatnika kuchni<span class="section-annotation">— co się dzieje w roślinnej piekarni</span></h2>
            </div>
            <div class="section-meta">
                {{ page_obj.paginator.count }} wpis{{ page_obj.paginator.count|pluralize:"y,ów" }}
            </div>
        </div>

        {% if posts %}
        <div class="recipe-grid" aria-label="Lista wpisów">
            {% for post in posts %}
            <a class="recipe-card" href="{{ post.get_absolute_url }}" aria-label="Otwórz wpis: {{ post.title }}">
                <div class="recipe-img">
                    <div class="num-stamp">{{ forloop.counter|stringformat:"02d" }}</div>
                    {% if post.published_at %}
                    <div class="time-stamp">{{ post.published_at|date:"j.m.Y" }}</div>
                    {% endif %}
                </div>
                <div class="recipe-body">
                    <div class="recipe-kicker">wpis</div>
                    <div class="recipe-name">{{ post.title }}</div>
                    {% if post.excerpt %}
                    <p class="recipe-meta" style="display:block; font-style: italic;">{{ post.excerpt|truncatechars:160 }}</p>
                    {% endif %}
                    {% with tag_items=post.tags_list %}
                    {% if tag_items %}
                    <div class="recipe-meta" aria-label="Tagi">
                        {% for t in tag_items %}<span>#{{ t }}</span>{% endfor %}
                    </div>
                    {% endif %}
                    {% endwith %}
                </div>
            </a>
            {% endfor %}
        </div>

        {% if page_obj.has_other_pages %}
        <nav aria-label="Paginacja bloga">
            <ul class="kk-pagination">
                {% if page_obj.has_previous %}
                <li class="page-item">
                    <a class="page-link" href="?page={{ page_obj.previous_page_number }}" aria-label="Poprzednia strona">«</a>
                </li>
                {% endif %}
                {% for num in page_obj.paginator.page_range %}
                <li class="page-item {% if page_obj.number == num %}active{% endif %}">
                    <a class="page-link" href="?page={{ num }}">{{ num }}</a>
                </li>
                {% endfor %}
                {% if page_obj.has_next %}
                <li class="page-item">
                    <a class="page-link" href="?page={{ page_obj.next_page_number }}" aria-label="Następna strona">»</a>
                </li>
                {% endif %}
            </ul>
        </nav>
        {% endif %}

        {% else %}
        <div class="kk-empty-state">
            <h2>Jeszcze nic nie ma</h2>
            <p>Pierwszy wpis już wkrótce. W międzyczasie zajrzyj do <a href="{% url 'recipes:list' %}">przepiśnika</a>.</p>
        </div>
        {% endif %}
    </div>
</section>
{% endblock %}
```

**6b. content/templates/content/blog_detail.html** (utwórz nowy plik):
```html
{% extends "base.html" %}
{% load static %}

{% block title %}{{ post.title }} — Kuchenna Komitywa{% endblock %}

{% block content %}
<section class="kk-section" aria-label="Wpis blogowy">
    <div class="wrap-narrow">
        <div class="hero-eyebrow">blog</div>
        <h1>{{ post.title }}</h1>

        <div class="d-flex flex-wrap gap-2 mb-4" style="align-items: center; margin-bottom: 24px;">
            {% if post.published_at %}
            <span style="font-family: var(--font-body); font-style: italic; color: var(--ink-faded); font-size: 15px;">
                {{ post.published_at|date:"j E Y" }}
            </span>
            {% endif %}
            {% with tag_items=post.tags_list %}
            {% if tag_items %}
            <span style="color: var(--ink-faded);">·</span>
            <div class="tag-row" style="margin-bottom: 0; display: inline-flex;">
                {% for t in tag_items %}<span class="tag">#{{ t }}</span>{% endfor %}
            </div>
            {% endif %}
            {% endwith %}
        </div>

        {% if post.excerpt %}
        <p class="lead" style="font-style: italic;">{{ post.excerpt }}</p>
        {% endif %}

        <article class="kk-blog-body">
            {% autoescape off %}{{ post.body_html }}{% endautoescape %}
        </article>

        <p style="margin-top: 32px; padding-top: 16px; border-top: 1px dashed var(--ink-soft);">
            <a href="{% url 'content:blog_list' %}" class="kk-link-arrow">← wróć do bloga</a>
        </p>
    </div>
</section>
{% endblock %}
```

Uwagi:
- Klasy `.kk-section`, `.wrap`, `.wrap-narrow`, `.recipe-grid`, `.recipe-card`, `.recipe-body`, `.recipe-name`, `.recipe-meta`, `.recipe-kicker`, `.recipe-img`, `.num-stamp`, `.time-stamp`, `.section-head`, `.section-number`, `.section-title`, `.section-annotation`, `.section-meta`, `.tag-row`, `.tag`, `.kk-pagination`, `.kk-empty-state`, `.hero-eyebrow`, `.kk-link-arrow`, `.lead` — WSZYSTKIE są już w main.css. NIE duplikuj.
- `.kk-blog-body` — JEDYNA nowa klasa, dla typografii treści posta (akapity, h2/h3, listy). Stylizacja w Task 7.
- `autoescape off` na `body_html` jest bezpieczne bo `mark_safe` w property + tylko admin może wprowadzać body (markdown trusted source).
- Empty state linkuje do przepiśnika (cross-promotion).
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; (. .venv/bin/activate 2&gt;/dev/null; python manage.py shell -c "
from django.template.loader import get_template
get_template('content/blog_list.html')
get_template('content/blog_detail.html')
print('templates OK')
")</automated>
  </verify>
  <done>Pliki `content/templates/content/blog_list.html` i `blog_detail.html` istnieją, extendują `base.html`, używają `{% block title %}` i `{% block content %}`, `get_template()` ładuje je bez błędu. Detail renderuje `body_html` w `autoescape off`. List ma paginację + empty state.</done>
</task>

<task type="auto">
  <name>Task 7: Dodaj sekcję /* blog */ do static/css/main.css (typografia treści posta)</name>
  <files>static/css/main.css</files>
  <action>
Dopisz na końcu pliku `static/css/main.css` (po ostatnim media query) nową sekcję:

```css

/* --------- Blog body typography (kk-blog-body) --------- */
.kk-blog-body {
    font-family: var(--font-body);
    font-size: 18px;
    line-height: 1.75;
    color: var(--ink);
    margin-top: 24px;
}
.kk-blog-body p {
    margin: 0 0 18px;
}
.kk-blog-body h2 {
    font-family: var(--font-display);
    font-size: 30px;
    line-height: 1.2;
    color: var(--ink);
    margin: 36px 0 14px;
}
.kk-blog-body h3 {
    font-family: var(--font-display);
    font-size: 24px;
    line-height: 1.25;
    color: var(--ink-soft);
    margin: 28px 0 10px;
}
.kk-blog-body ul,
.kk-blog-body ol {
    margin: 0 0 18px 24px;
    padding: 0;
}
.kk-blog-body li {
    margin-bottom: 8px;
}
.kk-blog-body a {
    color: var(--accent-2);
    text-decoration: underline;
    text-underline-offset: 3px;
}
.kk-blog-body a:hover {
    color: var(--ink);
}
.kk-blog-body blockquote {
    border-left: 3px solid var(--accent-3);
    padding: 8px 18px;
    margin: 18px 0;
    background: var(--paper-2);
    color: var(--ink-soft);
    font-style: italic;
}
.kk-blog-body code {
    font-family: var(--font-mono);
    font-size: 0.92em;
    background: var(--paper-2);
    padding: 1px 6px;
    border-radius: 3px;
}
.kk-blog-body pre {
    font-family: var(--font-mono);
    font-size: 14px;
    background: var(--paper-2);
    padding: 14px 18px;
    border-radius: 4px;
    overflow-x: auto;
    margin: 18px 0;
}
.kk-blog-body pre code {
    background: transparent;
    padding: 0;
}
.kk-blog-body hr {
    border: none;
    border-top: 1px dashed var(--ink-soft);
    margin: 32px 0;
}
.kk-blog-body strong { color: var(--ink); }
.kk-blog-body em { font-style: italic; }
@media (max-width: 768px) {
    .kk-blog-body { font-size: 17px; }
    .kk-blog-body h2 { font-size: 26px; }
    .kk-blog-body h3 { font-size: 21px; }
}
```

Uwagi:
- Reuse zmiennych CSS (`--paper-2`, `--ink`, `--accent-2`, `--accent-3`, `--font-display`, `--font-body`, `--font-mono`) — żadnych hardcodowanych kolorów.
- Tylko `.kk-blog-body` scope — żadne global tags, żeby nie wpływać na inne strony.
- Responsive breakpoint zgodny z resztą main.css (768px).
- NIE duplikuj klas `.tag`, `.tag-row`, `.recipe-card` itd. — istnieją.
- Po edycji NIE rób `collectstatic` lokalnie (zrobi to deploy.sh na serwerze).
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; grep -q "kk-blog-body" static/css/main.css &amp;&amp; grep -q "kk-blog-body blockquote" static/css/main.css &amp;&amp; grep -q "kk-blog-body pre" static/css/main.css &amp;&amp; echo "css OK"</automated>
  </verify>
  <done>`static/css/main.css` zawiera sekcję `/* --------- Blog body typography (kk-blog-body) --------- */` ze stylami dla p, h2, h3, ul/ol, a, blockquote, code, pre, hr + responsive @media. Wszystkie kolory przez CSS variables. NIE duplikuje istniejących klas.</done>
</task>

<task type="auto">
  <name>Task 8: Dodaj link 'blog' do nav w templates/includes/_navbar.html</name>
  <files>templates/includes/_navbar.html</files>
  <action>
Zmodyfikuj `templates/includes/_navbar.html`. Dodaj link 'blog' POMIĘDZY linkiem 'sklep' a 'o nas' — żeby kolejność była: przepiśnik → sklep → blog → o nas → kontakt.

Wersja docelowa `.nav-links`:
```html
        <div class="nav-links" id="mainNav">
            <a class="{% if request.resolver_match.app_name == 'recipes' %}active{% endif %}" href="{% url 'recipes:list' %}">przepiśnik</a>
            <a class="{% if request.resolver_match.app_name == 'shop' %}active{% endif %}" href="{% url 'shop:list' %}">sklep</a>
            <a class="{% if request.resolver_match.app_name == 'content' %}active{% endif %}" href="{% url 'content:blog_list' %}">blog</a>
            <a class="{% if request.resolver_match.url_name == 'about' %}active{% endif %}" href="{% url 'about' %}">o nas</a>
            <a class="{% if request.resolver_match.url_name == 'contact' %}active{% endif %}" href="{% url 'contact' %}">kontakt</a>
        </div>
```

NIE zmieniaj reszty navbara (brand, toggle, cart, struktury .nav-inner).

Uwagi:
- `app_name == 'content'` — bo `content/urls.py` ma `app_name = "content"`, więc na obu stronach (list i detail) aktywny stan się włączy.
- Kolejność: blog idzie po sklepie bo tematycznie jest "treściowy" obok przepiśnika; o nas / kontakt zawsze na końcu (konwencja).
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; grep -q "url 'content:blog_list'" templates/includes/_navbar.html &amp;&amp; grep -q "app_name == 'content'" templates/includes/_navbar.html &amp;&amp; (. .venv/bin/activate 2&gt;/dev/null; python manage.py shell -c "
from django.template.loader import get_template
from django.template import Context
t = get_template('includes/_navbar.html')
out = t.render({'cart_count': 0})
assert 'blog' in out.lower(), 'blog link missing in rendered nav'
assert '/blog/' in out, '/blog/ URL missing in rendered nav'
print('nav OK')
")</automated>
  </verify>
  <done>`templates/includes/_navbar.html` zawiera nowy link `<a ... href="{% url 'content:blog_list' %}">blog</a>` między 'sklep' a 'o nas', z aktywnym stanem przy `app_name == 'content'`. Render templatki zawiera `/blog/`.</done>
</task>

<task type="auto">
  <name>Task 9: Sanity end-to-end z formatted_json (test akcji promote_to_blogpost + render strony)</name>
  <files>(no file edits — sanity test only)</files>
  <action>
Uruchom kompleksowy sanity test lokalnie. CEL: zweryfikować że pipeline WeeklyResearch.formatted_json → BlogPost → /blog/ → /blog/<slug>/ działa od początku do końca, bez deploy'u.

```bash
cd /home/tomo/workspace/komitywa
. .venv/bin/activate
python manage.py check  # MUSI być "System check identified no issues"

python manage.py shell -c "
from datetime import date, timedelta
from django.test import Client
from django.utils import timezone
from content.models import WeeklyResearch, BlogPost
from content.admin import promote_to_blogpost

# 1. Cleanup poprzedniego sanity stanu
BlogPost.objects.filter(slug__startswith='sanity-').delete()
WeeklyResearch.objects.filter(week_label='2099-W01').delete()

# 2. Utwórz WeeklyResearch z formatted_json zawierającym blog
wr = WeeklyResearch.objects.create(
    week_label='2099-W01',
    date_from=date.today() - timedelta(days=7),
    date_to=date.today(),
    status='formatted',
    formatted_json={
        'blog': {
            'title': 'Sanity Test Post',
            'body': 'To jest **sanity** test. Lista:\n\n- jeden\n- dwa\n\n## Sekcja\n\nTreść sekcji.',
            'excerpt': 'Krótki lead testowy.',
            'hashtags': ['#wegan', '#test', 'sanity']
        }
    }
)

# 3. Wywołaj akcję promote_to_blogpost
class FakeRequest: pass
class FakeMessages:
    msgs = []
    def __getattr__(self, name): return lambda req, msg: self.msgs.append((name, msg))
# bezpieczniej: użyj admin.messages bezpośrednio przez Client
# ale dla sanity wystarczy bezpośrednie wywołanie funkcji z prawdziwym requestem
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
rf = RequestFactory()
req = rf.get('/admin/')
req.session = {}
req._messages = FallbackStorage(req)

qs = WeeklyResearch.objects.filter(pk=wr.pk)
promote_to_blogpost(None, req, qs)

# 4. Sprawdź że BlogPost powstał
post = BlogPost.objects.filter(source_research=wr).first()
assert post is not None, 'BlogPost not created'
assert post.title == 'Sanity Test Post'
assert post.status == 'draft', f'status: {post.status}'
assert 'sanity' in post.tags or 'wegan' in post.tags, f'tags: {post.tags}'
assert post.slug == 'sanity-test-post', f'slug: {post.slug}'
# Sanity: idempotencja — druga akcja NIE powinna stworzyć drugiego BlogPost
promote_to_blogpost(None, req, qs)
assert BlogPost.objects.filter(source_research=wr).count() == 1, 'idempotency broken'

# 5. Publikuj posta
post.status = 'published'
post.save()
assert post.published_at is not None
assert '<p>To jest <strong>sanity</strong> test.' in post.body_html
assert '<ul>' in post.body_html
assert '<h2>Sekcja</h2>' in post.body_html or '<h2>Sekcja</h2>' in post.body_html.replace(' id=\"sekcja\"', '')

# 6. Test view'ów przez Client
c = Client()
r = c.get('/blog/')
assert r.status_code == 200, f'/blog/ -> {r.status_code}'
assert b'Sanity Test Post' in r.content, 'post title not in /blog/'

r = c.get(f'/blog/{post.slug}/')
assert r.status_code == 200, f'/blog/{post.slug}/ -> {r.status_code}'
assert b'<strong>sanity</strong>' in r.content, 'markdown bold not rendered'
assert b'wr\xc3\xb3\xc4\x87 do bloga' in r.content or b'wróć do bloga'.encode() in r.content, 'back-link missing'

# 7. Cleanup
post.delete()
wr.delete()
print('SANITY OK — pipeline WeeklyResearch -> promote -> publish -> /blog/ -> /blog/<slug>/')
"
```

Jeśli którykolwiek assert fail — diagnoza:
- `BlogPost not created`: sprawdź akcję `promote_to_blogpost` (mapping pól z formatted_json.blog)
- `idempotency broken`: sprawdź `if research.blog_posts.exists()` w akcji
- `/blog/ -> 404`: sprawdź `backend/urls.py` (include na blog/)
- `markdown bold not rendered`: sprawdź `body_html` property + `autoescape off` w templatce

NIE commituj jeszcze (commit w Task 10).
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; (. .venv/bin/activate 2&gt;/dev/null; python manage.py check 2&gt;&amp;1 | grep -q "System check identified no issues") &amp;&amp; echo "check OK"</automated>
  </verify>
  <done>`manage.py check` zielony lokalnie; sanity shell test zakończył się "SANITY OK" — pełny pipeline z formatted_json przez akcję promote do BlogPost do rendera HTML działa. Idempotencja akcji potwierdzona. Markdown renderuje się (bold, lista, h2). Cleanup wykonany (no rezydualnych rekordów).</done>
</task>

<task type="auto">
  <name>Task 10: Atomic commit + push + paramiko deploy + remote smoke (HTTP 200 na /blog/)</name>
  <files>(git + remote — no file edits)</files>
  <action>

**10a. Commit lokalnie:**
```bash
cd /home/tomo/workspace/komitywa
git add requirements.txt content/models.py content/migrations/0002_blogpost.py content/admin.py content/views.py content/urls.py content/templates/content/blog_list.html content/templates/content/blog_detail.html backend/urls.py templates/includes/_navbar.html static/css/main.css
git status --short  # weryfikacja co dodajesz
git commit -m "feat(content): pełny blog — model BlogPost, admin draft/publish, /blog/ + /blog/<slug>/, akcja Promuj z WeeklyResearch

- Model BlogPost (title, slug, excerpt, body markdown, tags CSV, status, published_at, source_research FK)
- BlogPostManager.published() + save() z auto-slug + auto-published_at (idempotent, nie nadpisuje historii)
- Property body_html (markdown extensions: extra, smarty) + tags_list
- Migracja 0002_blogpost
- Admin: BlogPostAdmin (fieldsets, prepopulated slug, akcje make_published/make_draft, slug RO po publikacji)
- Admin: akcja promote_to_blogpost w WeeklyResearchAdmin (idempotentna, czyta formatted_json.blog)
- Views: BlogListView (paginate 10, .published()) + BlogDetailView (slug, .published())
- URLs: /blog/ + /blog/<slug>/ pod namespace 'content'
- Templates: blog_list (recipe-grid reuse), blog_detail (wrap-narrow, kk-blog-body) — extends base.html
- CSS: sekcja /* blog */ — typografia treści posta (p/h2/h3/ul/blockquote/code/pre/hr), brand vars
- Nav: link 'blog' między sklepem a 'o nas', aktywny dla app_name=='content'
- Dep: markdown>=3.5,<4"
```

**10b. Push:**
```bash
git push origin main
```

**10c. Deploy przez paramiko (systemowy python3):**
```bash
/usr/bin/python3 -c "
import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('panel84.mydevil.net', username='jem3pizze', password='Tak12toto.', timeout=30)
cmd = 'cd /usr/home/jem3pizze/domains/kuchennakomitywa.pl/public_python/ && bash ./deploy.sh 2>&1'
stdin, stdout, stderr = client.exec_command(cmd, timeout=600)
out = stdout.read().decode()
err = stderr.read().decode()
rc = stdout.channel.recv_exit_status()
print('=== STDOUT ===')
print(out[-4000:])
print('=== STDERR ===')
print(err[-1000:])
print('=== EXIT', rc, '===')
client.close()
assert rc == 0, f'deploy.sh failed with rc={rc}'
"
```

Deploy.sh wykonuje: git pull, pip install (zainstaluje markdown), migrate (zaaplikuje 0002_blogpost), collectstatic (nowe CSS), restart Passenger.

**10d. Remote smoke test:**
```bash
/usr/bin/python3 -c "
import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('panel84.mydevil.net', username='jem3pizze', password='Tak12toto.', timeout=30)
cmd = '''cd /usr/home/jem3pizze/domains/kuchennakomitywa.pl/public_python/ && source ~/.virtualenvs/komitywa/bin/activate && python manage.py check 2>&1; echo ---SHOWMIGRATIONS---; python manage.py showmigrations content 2>&1; echo ---CURL-BLOG---; curl -sk -o /dev/null -w \"HTTP %{http_code}\" https://kuchennakomitywa.pl/blog/; echo; echo ---CURL-ADMIN-BLOGPOST---; curl -sk -o /dev/null -w \"HTTP %{http_code}\" https://kuchennakomitywa.pl/admin/content/blogpost/; echo'''
stdin, stdout, stderr = client.exec_command(cmd, timeout=120)
out = stdout.read().decode()
err = stderr.read().decode()
print(out)
print('---STDERR---')
print(err[-500:])
client.close()
assert 'System check identified no issues' in out or 'no issues' in out, 'remote check failed'
assert '[X] 0002_blogpost' in out, 'migration 0002 not applied on remote'
assert 'HTTP 200' in out.split('---CURL-BLOG---')[1].split('---')[0], 'remote /blog/ NOT 200'
# /admin/content/blogpost/ powinno zwrócić 302 (redirect to login) lub 200
admin_section = out.split('---CURL-ADMIN-BLOGPOST---')[1]
assert 'HTTP 302' in admin_section or 'HTTP 200' in admin_section, f'remote /admin/content/blogpost/ unexpected: {admin_section}'
print('REMOTE SMOKE OK')
"
```

Oczekiwane wyniki:
- `python manage.py check` na remote → "no issues"
- `showmigrations content` → `[X] 0001_initial` i `[X] 0002_blogpost` (oba zaaplikowane)
- `curl /blog/` → HTTP 200 (pusta strona z empty state, ale renderuje się)
- `curl /admin/content/blogpost/` → HTTP 302 (redirect to login — bo nie zalogowany)

Jeśli `curl /blog/` zwraca 500: zdebuguj remote logs przez paramiko:
```python
cmd = 'tail -100 /usr/home/jem3pizze/domains/kuchennakomitywa.pl/public_python/logs/django.log'
```

Najczęstsze przyczyny błędu 500:
- `markdown` nie zainstalowany (deploy.sh `pip install` powinien to ogarnąć)
- Migracja nie zaaplikowała się (brak tabeli content_blogpost)
- Templates nie znalezione (sprawdź `APP_DIRS=True` + lokalizację plików w `content/templates/content/`)
- Static files cache (cmd+shift+R w przeglądarce; collectstatic robił to)

NIE rób force-push, NIE rollback bez ustalenia z userem. Jeśli coś nie działa — zwróć tail logu jako findings i czekaj na decyzję.
  </action>
  <verify>
    <automated>cd /home/tomo/workspace/komitywa &amp;&amp; git log -1 --pretty=format:"%s" | grep -q "feat(content): pełny blog" &amp;&amp; git status --porcelain | grep -v "^?? " | wc -l | tr -d '[:space:]' | grep -q "^0$" &amp;&amp; git rev-parse HEAD &amp;&amp; git rev-parse origin/main &amp;&amp; test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" &amp;&amp; echo "commit + push + clean OK"</automated>
  </verify>
  <done>Atomic commit z message `feat(content): pełny blog ...` istnieje na HEAD; tree czysty (poza ?? files w .claude/worktrees/); push do origin/main OK; deploy.sh exit 0 na MyDevil; remote `manage.py check` zielony; `showmigrations content` pokazuje `[X] 0002_blogpost`; curl `https://kuchennakomitywa.pl/blog/` zwraca HTTP 200; curl `/admin/content/blogpost/` zwraca HTTP 302 lub 200.</done>
</task>

</tasks>

<verification>
Po wszystkich tasks (10 łącznie):

1. **Code-level (lokalnie):**
   - `pip show markdown` → ≥3.5,<4
   - `manage.py check` → 0 issues
   - `manage.py showmigrations content` → `[X] 0001_initial`, `[X] 0002_blogpost`
   - `reverse('content:blog_list')` → `/blog/`
   - `reverse('content:blog_detail', args=['x'])` → `/blog/x/`
   - `get_template('content/blog_list.html')` i `blog_detail.html` ładują się
   - Sanity Client test: GET `/blog/` → 200, GET `/blog/<slug>/` → 200, body renderuje `<strong>` z markdown

2. **Admin-level (lokalnie):**
   - Akcja `promote_to_blogpost` zarejestrowana na WeeklyResearchAdmin
   - Akcja idempotentna (sanity test potwierdził)
   - BlogPostAdmin ma fieldsets, prepopulated_fields, autocomplete_fields, actions

3. **Deploy-level (remote):**
   - deploy.sh exit 0
   - Remote `manage.py check` 0 issues
   - Remote migracja 0002_blogpost zaaplikowana
   - Curl `https://kuchennakomitywa.pl/blog/` → HTTP 200
   - Curl `https://kuchennakomitywa.pl/admin/content/blogpost/` → HTTP 302 (login) lub 200

4. **Manual smoke (user, post-deploy — w SUMMARY jako rekomendacja, nie blocker):**
   - Login do /admin/ na produkcji
   - Otwórz dowolny WeeklyResearch ze statusem `formatted`, użyj akcji "Promuj do BlogPost"
   - Sprawdź że draft BlogPost powstał z wypełnionymi polami
   - Edytuj body, zmień status na "published", zapisz
   - Otwórz /blog/ — post widoczny; otwórz /blog/<slug>/ — renderuje się z brand stylem

Out of scope dla weryfikacji:
- Sitemap (NIE konfigurujemy; `django.contrib.sitemaps` NIE jest w INSTALLED_APPS — zostawić notatkę w SUMMARY: "Sitemap dla bloga — osobny phase, dopiero gdy będzie ≥5 postów + cel SEO")
- RSS feed (out of scope, decyzja w `<output>` user'a)
- Comments / search / categories (out of scope)
</verification>

<success_criteria>
- Pełny pipeline live: WeeklyResearch (formatted) → "Promuj do BlogPost" w admin → edycja draft → publish → /blog/<slug>/ HTTP 200 z brand-styled rendererem markdown
- `/blog/` HTTP 200 na produkcji (nawet pusty, z empty state linkującym do przepiśnika)
- Nav link "blog" widoczny i klikalny na wszystkich podstronach
- Admin: BlogPostAdmin pozwala tworzyć post od zera (bez WeeklyResearch) — pełen CRUD
- Brand palette zachowana (paper/ink/olive/terracotta/mustard), brak hardcoded kolorów
- Atomic commit `feat(content): pełny blog ...` na origin/main, deploy.sh sukces, zero regresji (manage.py check zielony lokalnie + remote)
</success_criteria>

<output>
After completion, create `.planning/quick/260602-qcl-pe-ny-blog-na-stronie-model-blogpost-adm/260602-qcl-SUMMARY.md` zawierający:

1. **Co zostało dostarczone** (per task — 10 sekcji)
2. **Decyzje techniczne**:
   - Slug auto-fill TYLKO gdy pusty (user może override w admin)
   - published_at NIGDY nie nadpisuje historii (cofnięcie do draft + repub zachowuje pierwotną datę)
   - Idempotencja `promote_to_blogpost` przez `research.blog_posts.exists()`
   - Markdown extensions: `extra`, `smarty` (NIE codehilite — nie chcemy zależności od Pygments)
   - Tags jako CSV (NIE M2M — celowo prosto; jeśli user kiedyś będzie chciał filtry per-tag, dorobimy)
   - `.kk-blog-body` jako jedyna nowa CSS klasa — reszta to reuse istniejących
3. **Deviations od planu** (jeśli były — np. base.html używa innego bloku niż założono)
4. **Sitemap status**: NIE skonfigurowane (brak `django.contrib.sitemaps` w INSTALLED_APPS). Rekomendacja: osobny quick task gdy będzie ≥5 postów + jasny cel SEO.
5. **Manual smoke checklist dla usera** (post-deploy):
   - [ ] Login do /admin/ na produkcji
   - [ ] Otwórz WeeklyResearch formatted → akcja "Promuj do BlogPost" → sprawdź message "Utworzono 1 BlogPost (draft)"
   - [ ] Edytuj BlogPost, zmień status na published, sprawdź że published_at się ustawił
   - [ ] Wejdź na /blog/ → post widoczny; klik → /blog/<slug>/ → renderuje się z markdown
   - [ ] Wróć i sprawdź że akcja drugi raz dla tego samego researchu daje "Pominięto 1"
6. **Files changed** (lista z `git diff --stat HEAD~1 HEAD`)
7. **Out of scope (zachowane)**: comments, likes, search, per-tag pages, RSS, featured image, edit-from-frontend
</output>
