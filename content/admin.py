from pathlib import Path

from django.conf import settings
from django.contrib import admin, messages
from django.urls import reverse

from content.services.ai_prompts import AI_IMAGE_BRAND_SUFFIX
from content.services.story_renderer import StoryRenderer

from .models import BlogPost, WeeklyResearch


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


@admin.register(WeeklyResearch)
class WeeklyResearchAdmin(admin.ModelAdmin):
    change_form_template = "admin/content/weeklyresearch/change_form.html"
    list_display = ("week_label", "date_from", "date_to", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("week_label",)
    readonly_fields = ("raw_research", "formatted_json", "created_at", "updated_at")
    ordering = ("-date_to",)
    actions = [promote_to_blogpost, generate_story_images_action]

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
