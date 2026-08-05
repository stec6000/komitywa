from django.contrib import admin
from django.utils.html import format_html

from .models import Order, OrderEdition, Product, ProductCategory


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


class ProductInline(admin.TabularInline):
    model = Product
    extra = 0
    fields = [
        "sort_order",
        "title",
        "category",
        "type",
        "price",
        "is_active",
    ]
    ordering = ["sort_order", "title"]
    autocomplete_fields = ["category"]
    show_change_link = True


@admin.register(OrderEdition)
class OrderEditionAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "status",
        "opens_at",
        "closes_at",
        "show_in_archive",
        "product_count",
        "updated_at",
    ]
    list_filter = ["status", "show_in_archive"]
    search_fields = ["title", "description", "pickup_details"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["image_preview", "created_at", "updated_at"]
    inlines = [ProductInline]
    fieldsets = [
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "status",
                    "description",
                )
            },
        ),
        (
            "Zdjęcie",
            {"fields": ("image", "image_alt", "image_preview")},
        ),
        (
            "Zamówienia i odbiór",
            {
                "fields": (
                    "opens_at",
                    "closes_at",
                    "pickup_details",
                    "payment_details",
                )
            },
        ),
        (
            "Publikacja",
            {
                "fields": (
                    "show_in_archive",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    ]

    @admin.display(description="Podgląd")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" alt="{}" style="max-height:120px; '
                'max-width:240px; object-fit:cover;">',
                obj.image.url,
                obj.image_alt,
            )
        return "---"

    @admin.display(description="Produkty")
    def product_count(self, obj):
        return obj.products.count()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "edition",
        "category",
        "type",
        "price",
        "sort_order",
        "is_active",
        "created_at",
        "image_preview",
    ]
    list_filter = ["edition", "category", "type", "is_active"]
    list_editable = ["sort_order", "is_active"]
    list_select_related = ["edition", "category"]
    search_fields = [
        "title",
        "description",
        "ingredients",
        "allergens",
    ]
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["edition", "category"]
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
