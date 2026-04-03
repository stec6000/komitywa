from django.contrib import admin
from django.utils.html import format_html

from .models import Order, Product, ProductCategory


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "category",
        "type",
        "price",
        "is_active",
        "created_at",
        "image_preview",
    ]
    list_filter = ["category", "type", "is_active"]
    search_fields = ["title", "description"]
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


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "email",
        "name",
        "status",
        "total",
        "p24_session_id",
        "created_at",
    ]
    list_filter = ["status"]
    search_fields = ["email", "name"]
    readonly_fields = ["cart_snapshot", "p24_session_id", "created_at"]
