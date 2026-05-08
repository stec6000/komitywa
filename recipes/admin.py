from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Recipe, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "slug"]


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "category",
        "servings",
        "difficulty",
        "prep_time",
        "is_published",
        "created_at",
        "image_preview",
    ]
    list_filter = ["category", "tags", "difficulty", "is_published"]
    search_fields = ["title", "ingredients_text"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["image_preview", "created_at", "updated_at"]
    filter_horizontal = ("tags",)
    fieldsets = (
        (None, {
            "fields": (
                "title",
                "slug",
                "category",
                "tags",
                "description",
                "ingredients_text",
                "steps_text",
            ),
        }),
        ("Metadane", {
            "fields": (
                "prep_time",
                "servings",
                "difficulty",
                "notes",
                "is_published",
            ),
        }),
        ("Zdjecie", {
            "fields": ("image", "image_preview"),
        }),
        ("Czas", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:60px;">',
                obj.image.url,
            )
        return "--"

    image_preview.short_description = "Podglad"
