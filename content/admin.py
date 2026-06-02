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
        # Po publikacji slug staje się read-only (kanoniczna URL — nie wolno breakować)
        if obj and obj.status == "published":
            ro.append("slug")
        return ro
