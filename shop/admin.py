import uuid

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.forms.models import BaseInlineFormSet
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html

from .emails import deliver_rzut_order_notifications
from .forms import ManualRzutOrderAdminForm
from .manual_orders import (
    ManualOrderData,
    ManualOrderError,
    ManualOrderLineRequest,
    create_manual_order,
)
from .models import (
    DiscountCode,
    Order,
    OrderEdition,
    Product,
    ProductCategory,
    Reservation,
    RzutItem,
    RzutOrder,
    RzutOrderItem,
)


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "discount_type",
        "value",
        "rzut",
        "is_active",
        "allocated_uses",
        "usage_limit",
        "valid_until",
    ]
    list_filter = ["discount_type", "is_active", "rzut"]
    search_fields = ["code", "rzut__title"]
    readonly_fields = ["allocated_uses", "created_at", "updated_at"]


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


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    actions = None
    list_select_related = ["rzut", "rzut_order"]
    list_display = [
        "id",
        "rzut",
        "customer_email",
        "status",
        "requires_attention",
        "expires_at",
        "updated_at",
    ]
    list_filter = ["status", "rzut"]
    search_fields = [
        "customer_name",
        "customer_email",
        "p24_session_id",
        "rzut__title",
    ]
    readonly_fields = [
        "rzut",
        "status",
        "customer_name",
        "customer_email",
        "customer_phone",
        "customer_notes",
        "pickup_starts_at",
        "pickup_ends_at",
        "subtotal",
        "discount_amount",
        "discount_code",
        "discount_code_snapshot",
        "total",
        "p24_session_id",
        "data_processing_accepted_at",
        "terms_accepted_at",
        "terms_version",
        "expires_at",
        "created_at",
        "updated_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(boolean=True, description="Pilna uwaga")
    def requires_attention(self, obj):
        order = getattr(obj, "rzut_order", None)
        return bool(order and order.requires_attention)


class RzutOrderItemReadonlyInline(admin.TabularInline):
    model = RzutOrderItem
    extra = 0
    can_delete = False
    fields = [
        "product_name",
        "portion",
        "unit_price",
        "quantity",
        "line_total",
        "rzut_item",
    ]
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(RzutOrder)
class RzutOrderAdmin(admin.ModelAdmin):
    add_form_template = "admin/shop/rzutorder/add_form.html"
    actions = None
    inlines = [RzutOrderItemReadonlyInline]
    list_select_related = ["rzut", "discount_code"]
    list_display = [
        "number",
        "is_manual",
        "rzut",
        "customer_email",
        "payment_status",
        "payment_method",
        "fulfillment_stage",
        "total",
        "created_at",
    ]
    list_filter = [
        "is_manual",
        "payment_status",
        "payment_method",
        "fulfillment_stage",
        "rzut",
    ]
    search_fields = [
        "number",
        "customer_name",
        "customer_email",
        "rzut__title",
    ]
    readonly_fields = [
        "number",
        "reservation",
        "is_manual",
        "manual_creation_token",
        "rzut",
        "customer_name",
        "customer_email",
        "customer_phone",
        "customer_notes",
        "pickup_starts_at",
        "pickup_ends_at",
        "subtotal",
        "discount_amount",
        "discount_code",
        "discount_code_snapshot",
        "total",
        "payment_status",
        "payment_method",
        "payment_method_details",
        "fulfillment_stage",
        "p24_session_id",
        "p24_order_id",
        "data_processing_accepted_at",
        "terms_accepted_at",
        "terms_version",
        "payment_confirmed_at",
        "customer_confirmation_sent_at",
        "customer_confirmation_error",
        "owner_notification_sent_at",
        "owner_notification_error",
        "requires_attention",
        "attention_message",
        "attention_notification_sent_at",
        "attention_notification_error",
        "created_at",
        "updated_at",
    ]

    def add_view(self, request, form_url="", extra_context=None):
        if not self.has_add_permission(request):
            raise PermissionDenied
        initial = {"creation_token": uuid.uuid4()}
        if request.method == "GET" and request.GET.get("rzut"):
            initial["rzut"] = request.GET["rzut"]
        form = ManualRzutOrderAdminForm(
            request.POST or None,
            initial=initial,
        )
        if request.method == "POST" and form.is_valid():
            slot = form.cleaned_data["pickup_slot"]
            try:
                order = create_manual_order(
                    data=ManualOrderData(
                        rzut_id=form.cleaned_data["rzut"].pk,
                        customer_name=form.cleaned_data["customer_name"],
                        customer_email=form.cleaned_data["customer_email"],
                        customer_phone=form.cleaned_data["customer_phone"],
                        customer_notes=form.cleaned_data["customer_notes"],
                        pickup_slot=slot,
                        payment_status=form.cleaned_data["payment_status"],
                        payment_method=form.cleaned_data["payment_method"],
                        payment_method_details=form.cleaned_data[
                            "payment_method_details"
                        ],
                        discount_code=form.cleaned_data["discount_code"],
                        creation_token=form.cleaned_data["creation_token"],
                    ),
                    lines=[
                        ManualOrderLineRequest(item_id, quantity)
                        for item_id, quantity in form.cleaned_lines
                    ],
                )
            except ManualOrderError as exc:
                form.add_error(None, exc.user_message)
            else:
                deliver_rzut_order_notifications(order)
                messages.success(
                    request,
                    f"Zamówienie Ręczne {order.number} zostało utworzone.",
                )
                return self._redirect_to_change(order)

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Dodaj Zamówienie Ręczne",
            "form": form,
            "media": form.media,
            "has_view_permission": self.has_view_permission(request),
            "has_add_permission": self.has_add_permission(request),
            "extra_context": extra_context or {},
        }
        return TemplateResponse(request, self.add_form_template, context)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            return False
        return super().has_change_permission(request, obj)

    @staticmethod
    def _redirect_to_change(order):
        return redirect(
            reverse("admin:shop_rzutorder_change", args=[order.pk])
        )


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
