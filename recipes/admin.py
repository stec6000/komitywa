from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Recipe


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "category",
        "prep_time",
        "is_published",
        "created_at",
        "image_preview",
    ]
    list_filter = ["category", "is_published"]
    search_fields = ["title", "ingredients_text"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["image_preview", "created_at", "updated_at"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:60px;">',
                obj.image.url,
            )
        return "---"

    image_preview.short_description = "Podglad"
