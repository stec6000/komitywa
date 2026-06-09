from pathlib import Path

from django.conf import settings
from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html

from content.services.ai_prompts import (
    AI_IMAGE_BRAND_SUFFIX,
    AI_STORY_BRAND_SUFFIX,
    build_story_image_prompt,
)
from content.services.story_renderer import StoryRenderer

from .models import BlogPost, StorySlide, WeeklyResearch


def _blog_body_from_json(blog):
    """Skladaj Markdown body z intro + sections (schemat FORMAT_PROMPT).

    Format zgodny z _preview.html: intro jako pierwszy akapit, kazda sekcja
    jako "## {heading}\n\n{body}". Title i tagi NIE wchodza do body
    (to osobne pola BlogPosta). Defensywnie pomija nie-dict sekcje.
    """
    parts = []
    intro = (blog.get("intro") or "").strip()
    if intro:
        parts.append(intro)
    for section in blog.get("sections") or []:
        if not isinstance(section, dict):
            continue
        heading = (section.get("heading") or "").strip()
        section_body = (section.get("body") or "").strip()
        chunk = []
        if heading:
            chunk.append(f"## {heading}")
        if section_body:
            chunk.append(section_body)
        if chunk:
            parts.append("\n\n".join(chunk))
    body = "\n\n".join(parts).strip()
    if not body:
        # Fallback kompatybilnosci: gdyby kiedys pojawil sie plaski schemat
        body = (blog.get("body") or "").strip()
    return body


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
        body = _blog_body_from_json(blog)
        excerpt = (
            blog.get("meta_description") or blog.get("excerpt") or ""
        ).strip()
        # tagi mogą być w "tags" lub "hashtags" — bierzemy co jest
        raw_tags = blog.get("tags") or blog.get("hashtags") or []
        if isinstance(raw_tags, str):
            tags = raw_tags
        else:
            # lista — może mieć "#" na początku, usuń
            tags = ", ".join(
                str(t).lstrip("#").strip() for t in raw_tags if str(t).strip()
            )
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
        messages.info(
            request,
            f"Pominięto {skipped} — BlogPost już istnieje dla tego researchu.",
        )
    if failed:
        messages.warning(
            request,
            f"Pominięto {failed} — brak title/body w formatted_json.blog.",
        )


@admin.action(description="Generuj grafiki stories (PNG 1080x1920)")
def generate_story_images_action(modeladmin, request, queryset):
    renderer = StoryRenderer()
    total_gen, total_skip, total_err = 0, 0, 0
    for wr in queryset:
        if not wr.formatted_json:
            messages.warning(
                request,
                f"{wr.week_label}: brak formatted_json — pominieto",
            )
            continue
        stories = wr.formatted_json.get("instagram_stories") or []
        if not stories:
            messages.warning(
                request,
                f"{wr.week_label}: brak instagram_stories — pominieto",
            )
            continue
        out_dir = (
            Path(settings.MEDIA_ROOT)
            / "weekly_research"
            / wr.week_label
            / "stories"
        )
        for idx, slide in enumerate(stories):
            slide_type = (
                (slide.get("slide_type") or f"slide{idx + 1}")
                .lower()
                .replace(" ", "_")
            )
            filename = f"{idx + 1:02d}_{slide_type}.png"
            path = out_dir / filename
            if path.exists():
                total_skip += 1
                continue
            try:
                renderer.render_to_file(slide, path)
                total_gen += 1
            except Exception as exc:  # noqa: BLE001
                total_err += 1
                messages.warning(
                    request,
                    f"{wr.week_label} slajd {idx + 1}: {exc}",
                )
    messages.success(
        request,
        f"Wygenerowano {total_gen} grafik, pominieto {total_skip} istniejacych, "
        f"bledow {total_err}",
    )


@admin.action(description="Promuj stories do StorySlide")
def promote_to_story_slides(modeladmin, request, queryset):
    created = 0
    skipped = 0
    failed = 0
    no_data = 0
    for research in queryset:
        # Idempotencja: jesli juz sa wiersze StorySlide, skip.
        if research.story_slides.exists():
            skipped += 1
            continue
        stories = (research.formatted_json or {}).get("instagram_stories") or []
        if not stories:
            no_data += 1
            continue
        for idx, slide in enumerate(stories, start=1):
            if not isinstance(slide, dict):
                failed += 1
                continue
            # Fallback stary schemat: 'text' -> headline.
            headline = (
                slide.get("headline") or slide.get("text") or ""
            ).strip()[:90]
            if not headline:
                failed += 1
                continue
            subtext = (slide.get("subtext") or "").strip()
            bg_color = (slide.get("bg_color") or "#f3ead7").strip()
            visual_hint = (slide.get("visual_hint") or "").strip()
            slide_type = (slide.get("slide_type") or "").strip()[:20]
            StorySlide.objects.create(
                research=research,
                order=idx,
                slide_type=slide_type,
                headline=headline,
                subtext=subtext,
                bg_color=bg_color[:9],
                visual_hint=visual_hint,
            )
            created += 1
    if created:
        messages.success(request, f"Utworzono {created} StorySlide.")
    if skipped:
        messages.info(
            request,
            f"Pominieto {skipped} — StorySlide juz istnieja dla tego researchu.",
        )
    if no_data:
        messages.warning(
            request,
            f"Pominieto {no_data} — brak instagram_stories w formatted_json.",
        )
    if failed:
        messages.warning(
            request,
            f"Pominieto {failed} slajdow — brak headline / niepoprawny format.",
        )


@admin.action(description="Generuj PNG (1080x1920)")
def generate_story_slide_pngs(modeladmin, request, queryset):
    renderer = StoryRenderer()
    generated, errors = 0, 0
    total = queryset.count()
    for i, slide in enumerate(queryset, start=1):
        slide_type = (
            (slide.slide_type or "slide").lower().replace(" ", "_")
        )
        path = (
            Path(settings.MEDIA_ROOT)
            / "weekly_research"
            / slide.research.week_label
            / "stories"
            / f"{slide.order:02d}_{slide_type}.png"
        )
        try:
            renderer.render_to_file(slide, path, index=i, total=total)
            generated += 1
        except Exception as exc:  # noqa: BLE001
            errors += 1
            messages.warning(
                request,
                f"{slide.research.week_label} #{slide.order}: {exc}",
            )
    if generated:
        messages.success(request, f"Wygenerowano {generated} PNG.")
    if errors:
        messages.warning(request, f"Bledow renderu: {errors}.")


class StorySlideInline(admin.TabularInline):
    model = StorySlide
    extra = 0
    fields = ("order", "slide_type", "headline", "bg_color", "background_image")
    readonly_fields = fields
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(WeeklyResearch)
class WeeklyResearchAdmin(admin.ModelAdmin):
    change_form_template = "admin/content/weeklyresearch/change_form.html"
    list_display = ("week_label", "date_from", "date_to", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("week_label",)
    readonly_fields = ("raw_research", "formatted_json", "created_at", "updated_at")
    ordering = ("-date_to",)
    inlines = [StorySlideInline]
    actions = [
        promote_to_blogpost,
        promote_to_story_slides,
        generate_story_images_action,
    ]

    def get_stories_files(self, obj):
        if obj is None or not obj.week_label:
            return []
        media_root = Path(settings.MEDIA_ROOT)
        stories_dir = media_root / "weekly_research" / obj.week_label / "stories"
        if not stories_dir.exists():
            return []
        files = []
        for png in sorted(stories_dir.glob("*.png")):
            stem = png.stem  # "01_hook"
            try:
                idx_str, slide_type = stem.split("_", 1)
                idx = int(idx_str)
            except ValueError:
                idx = 9999
                slide_type = stem
            try:
                rel = png.relative_to(media_root)
                url = f"{settings.MEDIA_URL.rstrip('/')}/{rel.as_posix()}"
            except ValueError:
                url = ""
            files.append({
                "index": idx,
                "slide_type": slide_type,
                "url": url,
                "filename": png.name,
            })
        files.sort(key=lambda f: f["index"])
        return files

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        try:
            obj = self.get_object(request, object_id)
        except Exception:
            obj = None
        extra_context["ai_image_brand_suffix"] = AI_IMAGE_BRAND_SUFFIX
        extra_context["ai_story_brand_suffix"] = AI_STORY_BRAND_SUFFIX
        if obj is not None:
            stories_files = self.get_stories_files(obj)
            extra_context["stories_files"] = stories_files
            if stories_files:
                extra_context["stories_zip_url"] = reverse(
                    "content:weeklyresearch_stories_zip",
                    kwargs={"pk": obj.pk},
                )
        return super().change_view(
            request, object_id, form_url=form_url, extra_context=extra_context,
        )


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
        # Po publikacji slug staje się read-only (kanoniczna URL — nie wolno breakować)
        if obj and obj.status == "published":
            ro.append("slug")
        return ro


@admin.register(StorySlide)
class StorySlideAdmin(admin.ModelAdmin):
    list_display = ("research", "order", "slide_type", "headline", "has_image")
    list_filter = ("research", "slide_type")
    ordering = ("research", "order")
    fields = (
        "research",
        "order",
        "slide_type",
        "headline",
        "subtext",
        "bg_color",
        "visual_hint",
        "background_image",
        "ai_prompt_display",
        "created_at",
        "updated_at",
    )
    readonly_fields = ("ai_prompt_display", "created_at", "updated_at")
    actions = [generate_story_slide_pngs]

    @admin.display(boolean=True, description="Zdjecie")
    def has_image(self, obj):
        return bool(obj.background_image)

    @admin.display(description="AI-prompt do zdjecia tla")
    def ai_prompt_display(self, obj):
        prompt = build_story_image_prompt(getattr(obj, "visual_hint", "") or "")
        return format_html(
            '<div>'
            '<pre style="white-space:pre-wrap;max-width:700px;'
            'padding:8px;background:#f6f6f6;border:1px solid #ddd;'
            'border-radius:4px;">{}</pre>'
            '<button type="button" '
            'onclick="navigator.clipboard.writeText('
            'this.previousElementSibling.textContent)">'
            'Kopiuj prompt AI</button>'
            '</div>',
            prompt,
        )
