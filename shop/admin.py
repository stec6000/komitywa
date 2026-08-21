import uuid

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import F
from django.forms.models import BaseInlineFormSet
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from .emails import (
    deliver_rzut_order_notifications,
)
from .fulfillment import (
    FulfillmentAllocationError,
    PickupDetails,
    RefundOutcome,
    TERMINAL_FULFILLMENT_STAGES,
    cancel_rzut_order,
    deliver_pickup_notification,
    deliver_ready_notification,
    is_rzut_order_refundable,
    refund_rzut_order,
)
from .forms import (
    CancellationDecisionForm,
    ManualRzutOrderAdminForm,
    RzutOrderFulfillmentAdminForm,
)
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
    PickupSlot,
    Product,
    ProductCategory,
    Reservation,
    RzutEvent,
    RzutItem,
    RzutOrder,
    RzutOrderEvent,
    RzutOrderItem,
    RzutPickupChange,
    RzutPickupNotification,
)


class ArchiveOrDeleteAdminMixin:
    def get_deleted_objects(self, objs, request):
        objects = list(objs)
        if objects:
            return (
                [str(obj) for obj in objects],
                {self.model._meta.verbose_name_plural: len(objects)},
                set(),
                [],
            )
        return super().get_deleted_objects(objects, request)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self.delete_model(request, obj)


def record_rzut_change(request, rzut, kind, before, after):
    RzutEvent.objects.create(
        rzut=rzut,
        actor=request.user,
        actor_email=request.user.email,
        kind=kind,
        context={"before": before, "after": after},
    )


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


@admin.register(DiscountCode)
class DiscountCodeAdmin(ArchiveOrDeleteAdminMixin, admin.ModelAdmin):
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

    @staticmethod
    def _is_used(obj):
        return obj.reservations.exists() or obj.rzut_orders.exists()

    def delete_model(self, request, obj):
        if self._is_used(obj):
            obj.is_active = False
            obj.save(update_fields=["is_active", "updated_at"])
            return
        super().delete_model(request, obj)

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
        for form in self.forms:
            cleaned_data = form.cleaned_data
            item = form.instance
            if (
                cleaned_data.get("DELETE")
                and item.pk
                and (
                    item.reservation_items.exists()
                    or item.order_items.exists()
                )
            ):
                cleaned_data["DELETE"] = False
                cleaned_data["is_active"] = False
                item.is_active = False

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
        "allocated_quantity",
        "withdrawn_quantity",
        "per_customer_limit",
        "is_active",
        "production_note",
    ]
    ordering = ["sort_order", "product__title"]
    autocomplete_fields = ["product"]
    readonly_fields = ["allocated_quantity", "withdrawn_quantity"]
    show_change_link = True


@admin.register(OrderEdition)
class OrderEditionAdmin(ArchiveOrDeleteAdminMixin, admin.ModelAdmin):
    actions = ["copy_as_draft"]
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

    @admin.action(description="Skopiuj jako ukryty szkic")
    def copy_as_draft(self, request, queryset):
        copied = 0
        with transaction.atomic():
            for source in queryset.prefetch_related("items"):
                draft = OrderEdition.objects.create(
                    title=f"Kopia – {source.title}",
                    description=source.description,
                    image=source.image,
                    image_alt=source.image_alt,
                    status=OrderEdition.Status.DRAFT,
                    pickup_place_name=source.pickup_place_name,
                    pickup_address=source.pickup_address,
                    pickup_instructions=source.pickup_instructions,
                    payment_details=source.payment_details,
                    show_in_archive=False,
                    show_upcoming_menu=False,
                )
                RzutItem.objects.bulk_create(
                    [
                        RzutItem(
                            rzut=draft,
                            product=item.product,
                            price=item.price,
                            portion=item.portion,
                            pool=item.pool,
                            per_customer_limit=item.per_customer_limit,
                            sort_order=item.sort_order,
                            is_active=item.is_active,
                            production_note=item.production_note,
                        )
                        for item in source.items.all()
                    ]
                )
                copied += 1
        self.message_user(
            request,
            f"Utworzono {copied} ukrytych szkiców Rzutu.",
            messages.SUCCESS,
        )

    @staticmethod
    def _has_history(obj):
        return obj.reservations.exists() or obj.rzut_orders.exists()

    def delete_model(self, request, obj):
        if self._has_history(obj) or obj.status != OrderEdition.Status.DRAFT:
            previous_status = obj.status
            was_shown_in_archive = obj.show_in_archive
            obj.status = OrderEdition.Status.CLOSED
            obj.show_in_archive = False
            obj.save(update_fields=["status", "show_in_archive", "updated_at"])
            if previous_status != obj.status:
                record_rzut_change(
                    request,
                    obj,
                    RzutEvent.Kind.STATUS_CHANGED,
                    previous_status,
                    obj.status,
                )
            if was_shown_in_archive:
                record_rzut_change(
                    request,
                    obj,
                    RzutEvent.Kind.ARCHIVE_VISIBILITY_CHANGED,
                    True,
                    False,
                )
            return
        obj.discount_codes.all().delete()
        obj.items.all().delete()
        super().delete_model(request, obj)

    def get_urls(self):
        custom_urls = [
            path(
                "<path:object_id>/pickup-changes/<int:change_id>/notify/",
                self.admin_site.admin_view(self.pickup_notification_view),
                name="shop_orderedition_pickup_notify",
            )
        ]
        return custom_urls + super().get_urls()

    def changeform_view(
        self,
        request,
        object_id=None,
        form_url="",
        extra_context=None,
    ):
        if request.method != "POST" or object_id is None:
            return super().changeform_view(
                request,
                object_id=object_id,
                form_url=form_url,
                extra_context=extra_context,
            )
        with transaction.atomic():
            OrderEdition.objects.filter(pk=object_id).update(
                allocation_revision=F("allocation_revision") + 1
            )
            return super().changeform_view(
                request,
                object_id=object_id,
                form_url=form_url,
                extra_context=extra_context,
            )

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

    def change_view(
        self,
        request,
        object_id,
        form_url="",
        extra_context=None,
    ):
        rzut = self.get_object(request, object_id)
        if rzut is not None and not self.has_change_permission(request, rzut):
            return super().change_view(
                request,
                object_id,
                form_url=form_url,
                extra_context=extra_context,
            )
        affected_orders = (
            rzut.rzut_orders.exclude(
                fulfillment_stage__in=TERMINAL_FULFILLMENT_STAGES
            )
            if rzut is not None
            else RzutOrder.objects.none()
        )
        if request.method == "POST" and rzut is not None and affected_orders.exists():
            try:
                proposed = PickupDetails(
                    date=forms.DateField().clean(
                        request.POST.get("pickup_date")
                    ),
                    place=request.POST.get("pickup_place_name", ""),
                    address=request.POST.get("pickup_address", ""),
                    starts_at=forms.TimeField().clean(
                        request.POST.get("pickup_starts_at")
                    ),
                    ends_at=forms.TimeField().clean(
                        request.POST.get("pickup_ends_at")
                    ),
                    instructions=request.POST.get("pickup_instructions", ""),
                )
            except forms.ValidationError:
                proposed = None
            current = PickupDetails.from_source(rzut)
            if proposed is not None and proposed != current:
                conflicting_orders = []
                for order in affected_orders:
                    try:
                        proposed.map_slot_from(
                            current,
                            PickupSlot(
                                order.pickup_starts_at,
                                order.pickup_ends_at,
                            ),
                        )
                    except FulfillmentAllocationError:
                        conflicting_orders.append(order)
                context = {
                    **self.admin_site.each_context(request),
                    "opts": self.model._meta,
                    "title": "Potwierdź zmianę danych odbioru",
                    "rzut": rzut,
                    "current_pickup": current,
                    "proposed_pickup": proposed,
                    "affected_count": affected_orders.count(),
                    "conflicting_orders": conflicting_orders,
                    "post_data": [
                        (key, value)
                        for key in request.POST
                        if key != "csrfmiddlewaretoken"
                        for value in request.POST.getlist(key)
                    ],
                }
                if (
                    conflicting_orders
                    or not request.POST.get("confirm_pickup_change")
                ):
                    return TemplateResponse(
                        request,
                        "admin/shop/orderedition/confirm_pickup_change.html",
                        context,
                    )
        return super().change_view(
            request,
            object_id,
            form_url=form_url,
            extra_context=extra_context,
        )

    def save_model(self, request, obj, form, change):
        before = None
        previous_status = None
        previous_archive_visibility = None
        if change:
            persisted = OrderEdition.objects.get(pk=obj.pk)
            before = PickupDetails.from_source(persisted)
            previous_status = persisted.status
            previous_archive_visibility = persisted.show_in_archive
        super().save_model(request, obj, form, change)
        if previous_status is not None and previous_status != obj.status:
            record_rzut_change(
                request,
                obj,
                RzutEvent.Kind.STATUS_CHANGED,
                previous_status,
                obj.status,
            )
        if (
            previous_archive_visibility is not None
            and previous_archive_visibility != obj.show_in_archive
        ):
            record_rzut_change(
                request,
                obj,
                RzutEvent.Kind.ARCHIVE_VISIBILITY_CHANGED,
                previous_archive_visibility,
                obj.show_in_archive,
            )
        after = PickupDetails.from_source(obj)
        if before is None or before == after:
            return

        orders = list(
            obj.rzut_orders.exclude(
                fulfillment_stage__in=TERMINAL_FULFILLMENT_STAGES
            )
        )
        if not orders:
            return

        updated_at = timezone.now()
        for order in orders:
            mapped_slot = after.map_slot_from(
                before,
                PickupSlot(
                    order.pickup_starts_at,
                    order.pickup_ends_at,
                ),
            )
            order.pickup_starts_at = mapped_slot.starts_at
            order.pickup_ends_at = mapped_slot.ends_at
            order.updated_at = updated_at
        RzutOrder.objects.bulk_update(
            orders,
            ["pickup_starts_at", "pickup_ends_at", "updated_at"],
        )

        pickup_change = RzutPickupChange.objects.create(
            rzut=obj,
            actor=request.user,
            actor_email=request.user.email,
            before=before.to_json(),
            after=after.to_json(),
        )
        RzutPickupNotification.objects.bulk_create(
            [
                RzutPickupNotification(change=pickup_change, order=order)
                for order in orders
            ]
        )
        RzutOrderEvent.objects.bulk_create(
            [
                RzutOrderEvent(
                    order=order,
                    actor=request.user,
                    actor_email=request.user.email,
                    kind=RzutOrderEvent.Kind.PICKUP_CHANGED,
                    context={
                        "pickup_change_id": pickup_change.pk,
                        "before": before.to_json(),
                        "after": after.to_json(),
                        "pickup_starts_at": order.pickup_starts_at.isoformat(),
                        "pickup_ends_at": order.pickup_ends_at.isoformat(),
                    },
                )
                for order in orders
            ]
        )
        request._rzut_pickup_change_id = pickup_change.pk

    def save_formset(self, request, form, formset, change):
        if formset.model is not RzutItem:
            return super().save_formset(request, form, formset, change)
        previous_pools = {
            item.pk: item.pool
            for item in RzutItem.objects.filter(rzut=form.instance)
        }
        super().save_formset(request, form, formset, change)
        events = []
        for item in RzutItem.objects.filter(rzut=form.instance):
            previous_pool = previous_pools.get(item.pk)
            if previous_pool is None or previous_pool == item.pool:
                continue
            events.append(
                RzutEvent(
                    rzut=form.instance,
                    actor=request.user,
                    actor_email=request.user.email,
                    kind=RzutEvent.Kind.POOL_CHANGED,
                    context={
                        "rzut_item_id": item.pk,
                        "product_id": item.product_id,
                        "before": previous_pool,
                        "after": item.pool,
                    },
                )
            )
        RzutEvent.objects.bulk_create(events)

    def response_change(self, request, obj):
        pickup_change_id = getattr(request, "_rzut_pickup_change_id", None)
        if pickup_change_id is not None:
            return redirect(
                reverse(
                    "admin:shop_orderedition_pickup_notify",
                    args=[obj.pk, pickup_change_id],
                )
            )
        return super().response_change(request, obj)

    def pickup_notification_view(self, request, object_id, change_id):
        rzut = get_object_or_404(OrderEdition, pk=object_id)
        if not self.has_change_permission(request, rzut):
            raise PermissionDenied
        pickup_change = get_object_or_404(
            RzutPickupChange,
            pk=change_id,
            rzut=rzut,
        )
        notifications = list(
            pickup_change.notifications.select_related(
                "order", "change", "change__rzut"
            ).order_by("order__created_at")
        )
        pending_notifications = [
            notification
            for notification in notifications
            if notification.sent_at is None
            and notification.order.fulfillment_stage
            not in TERMINAL_FULFILLMENT_STAGES
        ]
        if request.method == "POST" and request.POST.get(
            "confirm_pickup_notification"
        ):
            sent = 0
            failed = 0
            for notification in pending_notifications:
                result = deliver_pickup_notification(
                    notification=notification,
                    actor=request.user,
                )
                if not result.sent:
                    failed += 1
                    continue
                sent += 1
            if sent:
                messages.success(
                    request,
                    f"Wysłano wiadomość o zmianie odbioru do {sent} "
                    f"{'Klienta' if sent == 1 else 'Klientów'}.",
                )
            if failed:
                messages.error(
                    request,
                    f"Nie udało się wysłać wiadomości do {failed} "
                    f"{'Klienta' if failed == 1 else 'Klientów'}. "
                    "Ponów wysyłkę po usunięciu problemu z pocztą.",
                )
            return redirect(request.path)
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Wyślij wiadomość o zmianie odbioru",
            "rzut": rzut,
            "pickup_change": pickup_change,
            "pickup": PickupDetails.from_source(rzut),
            "notifications": notifications,
            "pending_notifications": pending_notifications,
            "recipient_count": len(pending_notifications),
        }
        return TemplateResponse(
            request,
            "admin/shop/orderedition/pickup_notification.html",
            context,
        )


@admin.register(RzutEvent)
class RzutEventAdmin(admin.ModelAdmin):
    actions = None
    list_select_related = ["rzut", "actor"]
    list_display = ["created_at", "rzut", "kind", "actor_email"]
    list_filter = ["kind", "rzut"]
    search_fields = ["rzut__title", "actor_email"]
    readonly_fields = [
        "rzut",
        "created_at",
        "kind",
        "actor",
        "actor_email",
        "context",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


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


class RzutOrderEventReadonlyInline(admin.TabularInline):
    model = RzutOrderEvent
    extra = 0
    can_delete = False
    fields = ["created_at", "kind", "actor_email", "context"]
    readonly_fields = fields
    ordering = ["-created_at", "-pk"]
    verbose_name_plural = "Historia istotnych działań"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(RzutOrder)
class RzutOrderAdmin(admin.ModelAdmin):
    add_form_template = "admin/shop/rzutorder/add_form.html"
    form = RzutOrderFulfillmentAdminForm
    actions = ["send_ready_notifications", "refund_p24_payment"]
    inlines = [RzutOrderItemReadonlyInline, RzutOrderEventReadonlyInline]
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
        "pickup_starts_at",
        "pickup_ends_at",
        "subtotal",
        "discount_amount",
        "discount_code",
        "discount_code_snapshot",
        "total",
        "payment_method",
        "payment_method_details",
        "p24_session_id",
        "p24_order_id",
        "p24_refund_request_id",
        "p24_refunds_uuid",
        "p24_refunded_at",
        "p24_refund_error",
        "p24_refund_result",
        "cancelled_quantity_restored",
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
        "ready_notification_sent_at",
        "ready_notification_error",
        "ready_notification_status",
        "created_at",
        "updated_at",
    ]

    fieldsets = [
        (
            "Realizacja",
            {
                "fields": (
                    "fulfillment_stage",
                    "internal_note",
                    "ready_notification_status",
                    "cancelled_quantity_restored",
                )
            },
        ),
        (
            "Klient i odbiór",
            {
                "fields": (
                    "customer_name",
                    "customer_email",
                    "customer_phone",
                    "customer_notes",
                    "pickup_slot",
                )
            },
        ),
        (
            "Rozliczenie",
            {
                "fields": (
                    "payment_status",
                    "payment_method",
                    "payment_method_details",
                )
            },
        ),
        (
            "Pełny zwrot Przelewy24",
            {
                "fields": (
                    "p24_refund_request_id",
                    "p24_refunds_uuid",
                    "p24_refunded_at",
                    "p24_refund_error",
                    "p24_refund_result",
                )
            },
        ),
        (
            "Niezmienna historia Zamówienia Rzutu",
            {
                "fields": (
                    "number",
                    "reservation",
                    "is_manual",
                    "manual_creation_token",
                    "rzut",
                    "subtotal",
                    "discount_amount",
                    "discount_code",
                    "discount_code_snapshot",
                    "total",
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
                )
            },
        ),
    ]

    def change_view(
        self,
        request,
        object_id,
        form_url="",
        extra_context=None,
    ):
        order = self.get_object(request, object_id)
        is_cancellation = (
            request.method == "POST"
            and order is not None
            and self.has_change_permission(request, order)
            and request.POST.get("fulfillment_stage")
            == RzutOrder.FulfillmentStage.CANCELLED
            and order.fulfillment_stage
            != RzutOrder.FulfillmentStage.CANCELLED
        )
        if is_cancellation:
            confirmed = bool(request.POST.get("confirm_cancellation"))
            cancellation_form = CancellationDecisionForm(
                request.POST if confirmed else None
            )
            if confirmed and cancellation_form.is_valid():
                request._restore_cancelled_quantity = (
                    cancellation_form.cleaned_data["restore_pool"]
                )
            else:
                context = {
                    **self.admin_site.each_context(request),
                    "opts": self.model._meta,
                    "title": "Potwierdź anulowanie Zamówienia Rzutu",
                    "order": order,
                    "cancellation_form": cancellation_form,
                    "post_data": [
                        (key, value)
                        for key in request.POST
                        if key not in {
                            "csrfmiddlewaretoken",
                            "confirm_cancellation",
                            "restore_pool",
                        }
                        for value in request.POST.getlist(key)
                    ],
                }
                return TemplateResponse(
                    request,
                    "admin/shop/rzutorder/confirm_cancellation.html",
                    context,
                )
        return super().change_view(
            request,
            object_id,
            form_url=form_url,
            extra_context=extra_context,
        )

    def save_model(self, request, obj, form, change):
        original = form.original_values
        target_stage = obj.fulfillment_stage
        is_cancellation = (
            original["fulfillment_stage"] != target_stage
            and target_stage == RzutOrder.FulfillmentStage.CANCELLED
        )
        if is_cancellation:
            obj.fulfillment_stage = original["fulfillment_stage"]
        super().save_model(request, obj, form, change)
        if is_cancellation:
            cancelled = cancel_rzut_order(
                order_id=obj.pk,
                actor=request.user,
                restore_pool=request._restore_cancelled_quantity,
            )
            obj.fulfillment_stage = cancelled.fulfillment_stage
        data_fields = [
            "customer_name",
            "customer_email",
            "customer_phone",
            "customer_notes",
            "internal_note",
            "pickup_starts_at",
            "pickup_ends_at",
        ]
        data_changes = {
            field: {
                "from": str(original[field]),
                "to": str(getattr(obj, field)),
            }
            for field in data_fields
            if original[field] != getattr(obj, field)
        }
        if data_changes:
            RzutOrderEvent.objects.create(
                order=obj,
                actor=request.user,
                actor_email=request.user.email,
                kind=RzutOrderEvent.Kind.CUSTOMER_DATA_CHANGED,
                context={"changes": data_changes},
            )
        if (
            not is_cancellation
            and original["fulfillment_stage"] != obj.fulfillment_stage
        ):
            RzutOrderEvent.objects.create(
                order=obj,
                actor=request.user,
                actor_email=request.user.email,
                kind=RzutOrderEvent.Kind.FULFILLMENT_STAGE_CHANGED,
                context={
                    "from": original["fulfillment_stage"],
                    "to": obj.fulfillment_stage,
                },
            )
        if original["payment_status"] != obj.payment_status:
            RzutOrderEvent.objects.create(
                order=obj,
                actor=request.user,
                actor_email=request.user.email,
                kind=RzutOrderEvent.Kind.PAYMENT_STATUS_CHANGED,
                context={
                    "from": original["payment_status"],
                    "to": obj.payment_status,
                },
            )

    @admin.action(description="Zwróć pełną płatność Przelewy24")
    def refund_p24_payment(self, request, queryset):
        orders = list(queryset)
        if len(orders) != 1:
            self.message_user(
                request,
                "Wybierz dokładnie jedno Zamówienie Rzutu do zwrotu.",
                level=messages.ERROR,
            )
            return None
        order = orders[0]
        if not is_rzut_order_refundable(order):
            self.message_user(
                request,
                "To Zamówienie Rzutu nie kwalifikuje się do pełnego "
                "zwrotu Przelewy24.",
                level=messages.ERROR,
            )
            return None
        refund_form = CancellationDecisionForm(
            request.POST if request.POST.get("confirm_refund") else None
        )
        if request.POST.get("confirm_refund") and refund_form.is_valid():
            result = refund_rzut_order(
                order_id=order.pk,
                actor=request.user,
                restore_pool=refund_form.cleaned_data["restore_pool"],
            )
            if result.outcome == RefundOutcome.COMPLETED:
                self.message_user(
                    request,
                    "Pełny zwrot Przelewy24 został przyjęty, a Zamówienie "
                    "Rzutu anulowane.",
                    level=messages.SUCCESS,
                )
            elif result.outcome == RefundOutcome.COMPLETED_WITH_WARNING:
                self.message_user(
                    request,
                    "Pełny zwrot Przelewy24 został potwierdzony, ale "
                    "rozliczenie Puli i anulowanie realizacji wymaga pilnej "
                    "uwagi: "
                    f"{result.error}",
                    level=messages.WARNING,
                )
            elif result.outcome == RefundOutcome.REQUESTED:
                self.message_user(
                    request,
                    "Zlecenie pełnego zwrotu zostało przyjęte. Zwrot "
                    "oczekuje na zakończenie w Przelewy24; ponów akcję, "
                    "aby odświeżyć wynik.",
                    level=messages.WARNING,
                )
            else:
                self.message_user(
                    request,
                    f"Zwrot Przelewy24 nie powiódł się: {result.error}",
                    level=messages.ERROR,
                )
            return redirect(
                reverse("admin:shop_rzutorder_change", args=[order.pk])
            )
        return TemplateResponse(
            request,
            "admin/shop/rzutorder/confirm_refund.html",
            {
                **self.admin_site.each_context(request),
                "opts": self.model._meta,
                "title": "Potwierdź pełny zwrot Przelewy24",
                "order": order,
                "refund_form": refund_form,
                "action_name": "refund_p24_payment",
            },
        )

    @admin.action(description="Wyślij wiadomość „gotowe do odbioru”")
    def send_ready_notifications(self, request, queryset):
        orders = list(queryset.select_related("rzut").order_by("created_at"))
        if request.POST.get("confirm_ready"):
            sent = 0
            failed = 0
            for order in orders:
                is_preparing = (
                    order.fulfillment_stage
                    == RzutOrder.FulfillmentStage.PREPARING
                )
                is_retry = (
                    order.fulfillment_stage
                    == RzutOrder.FulfillmentStage.READY
                    and bool(order.ready_notification_error)
                )
                if not (is_preparing or is_retry):
                    continue
                result = deliver_ready_notification(
                    order=order,
                    actor=request.user,
                )
                if not result.sent:
                    failed += 1
                    continue
                sent += 1
            if sent:
                messages.success(
                    request,
                    f"Wysłano wiadomość „gotowe” do {sent} "
                    f"{'Klienta' if sent == 1 else 'Klientów'}.",
                )
            if failed:
                messages.error(
                    request,
                    f"Nie udało się wysłać wiadomości do {failed} "
                    f"{'Klienta' if failed == 1 else 'Klientów'}. "
                    "Etap Realizacji pozostał zapisany; ponów akcję po "
                    "usunięciu problemu z pocztą.",
                )
            return redirect(reverse("admin:shop_rzutorder_changelist"))
        eligible_orders = [
            order
            for order in orders
            if order.fulfillment_stage == RzutOrder.FulfillmentStage.PREPARING
            or (
                order.fulfillment_stage == RzutOrder.FulfillmentStage.READY
                and bool(order.ready_notification_error)
            )
        ]
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Potwierdź wiadomość „gotowe do odbioru”",
            "orders": orders,
            "eligible_orders": eligible_orders,
            "recipient_count": len(eligible_orders),
        }
        return TemplateResponse(
            request,
            "admin/shop/rzutorder/confirm_ready_notifications.html",
            context,
        )

    @admin.display(description="Wiadomość „gotowe do odbioru”")
    def ready_notification_status(self, obj):
        if not obj:
            return "—"
        if obj.ready_notification_error:
            return format_html(
                'Błąd: {} — <a href="{}?q={}">ponów wysyłkę</a>',
                obj.ready_notification_error,
                reverse("admin:shop_rzutorder_changelist"),
                obj.number,
            )
        if obj.ready_notification_sent_at:
            sent_at = timezone.localtime(obj.ready_notification_sent_at)
            return f"Wysłano {sent_at:%d.%m.%Y o %H:%M}"
        return "Nie wysłano"

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
        return super().has_change_permission(request, obj)

    @staticmethod
    def _redirect_to_change(order):
        return redirect(
            reverse("admin:shop_rzutorder_change", args=[order.pk])
        )


@admin.register(Product)
class ProductAdmin(ArchiveOrDeleteAdminMixin, admin.ModelAdmin):
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

    def delete_model(self, request, obj):
        if obj.rzut_items.exists():
            obj.is_archived = True
            obj.is_available_in_shop = False
            obj.save(
                update_fields=["is_archived", "is_available_in_shop", "updated_at"]
            )
            obj.rzut_items.update(is_active=False)
            return
        super().delete_model(request, obj)

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
