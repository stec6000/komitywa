from django import forms
from django.contrib import admin
from django.forms.models import BaseInlineFormSet
from django.utils.html import format_html

from .models import Order, OrderEdition, Product, ProductCategory, RzutItem


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


class RzutItemInlineForm(forms.ModelForm):
    class Meta:
        model = RzutItem
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["price"].required = False
        self.fields["price"].help_text = (
            "Pozostaw puste, aby użyć domyślnej ceny Produktu."
        )
        self.fields["portion"].required = False
        self.fields["portion"].help_text = (
            "Pozostaw puste, aby użyć domyślnej Porcji Produktu."
        )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("DELETE"):
            return cleaned_data

        product = cleaned_data.get("product")
        if product is None:
            return cleaned_data

        if cleaned_data.get("price") is None:
            cleaned_data["price"] = product.price
        if not cleaned_data.get("portion"):
            cleaned_data["portion"] = product.default_portion
        if not cleaned_data["portion"]:
            self.add_error(
                "portion",
                "Podaj Porcję albo uzupełnij domyślną Porcję Produktu.",
            )

        return cleaned_data


class RzutItemInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        if self.instance.status != OrderEdition.Status.PUBLISHED:
            return

        active_items = []
        for form in self.forms:
            cleaned_data = form.cleaned_data
            if (
                not cleaned_data
                or cleaned_data.get("DELETE")
                or not cleaned_data.get("is_active")
            ):
                continue
            item = form.instance
            if item.product.type == "physical":
                active_items.append(item)

        errors = []
        if not active_items:
            errors.append("Dodaj co najmniej jedną aktywną Pozycję Rzutu.")
        for item in active_items:
            errors.extend(item.publication_errors())
        if errors:
            raise forms.ValidationError(errors)


class RzutItemInline(admin.TabularInline):
    model = RzutItem
    form = RzutItemInlineForm
    formset = RzutItemInlineFormSet
    extra = 0
    fields = [
        "sort_order",
        "product",
        "price",
        "portion",
        "pool",
        "per_customer_limit",
        "is_active",
        "production_note",
    ]
    ordering = ["sort_order", "product__title"]
    autocomplete_fields = ["product"]
    show_change_link = True


@admin.register(OrderEdition)
class OrderEditionAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "status",
        "phase_display",
        "opens_at",
        "closes_at",
        "show_in_archive",
        "item_count",
        "updated_at",
    ]
    list_filter = ["status", "show_in_archive"]
    search_fields = [
        "title",
        "description",
        "pickup_place_name",
        "pickup_address",
        "pickup_instructions",
    ]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["image_preview", "created_at", "updated_at"]
    inlines = [RzutItemInline]
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
                    "pickup_date",
                    "pickup_place_name",
                    "pickup_address",
                    "pickup_starts_at",
                    "pickup_ends_at",
                    "pickup_instructions",
                    "payment_details",
                )
            },
        ),
        (
            "Publikacja",
            {
                "fields": (
                    "show_upcoming_menu",
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

    @admin.display(description="Pozycje Rzutu")
    def item_count(self, obj):
        return obj.items.count()

    @admin.display(description="Faza")
    def phase_display(self, obj):
        phase = obj.phase_at()
        return OrderEdition.Phase(phase).label if phase else "—"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "category",
        "type",
        "price",
        "default_portion",
        "sort_order",
        "is_available_in_shop",
        "is_archived",
        "created_at",
        "image_preview",
    ]
    list_filter = [
        "category",
        "type",
        "is_available_in_shop",
        "is_archived",
    ]
    list_editable = [
        "sort_order",
        "is_available_in_shop",
        "is_archived",
    ]
    list_select_related = ["category"]
    search_fields = [
        "title",
        "description",
        "ingredients",
        "allergens",
    ]
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["category"]
    readonly_fields = ["image_preview", "created_at", "updated_at"]
    fieldsets = [
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "category",
                    "type",
                    "description",
                    "full_description",
                )
            },
        ),
        (
            "Oferta domyślna",
            {"fields": ("price", "default_portion")},
        ),
        (
            "Informacje o produkcie",
            {"fields": ("ingredients", "allergens", "image", "image_preview")},
        ),
        (
            "Pliki cyfrowe",
            {"fields": ("ebook_file",)},
        ),
        (
            "Publikacja",
            {
                "fields": (
                    "is_available_in_shop",
                    "is_archived",
                    "sort_order",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    ]

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
