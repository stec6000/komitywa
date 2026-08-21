import uuid
from dataclasses import dataclass
from datetime import date, datetime, time
from enum import Enum
from typing import Callable

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from requests import RequestException

from .emails import (
    send_rzut_order_ready_notification,
    send_rzut_pickup_change_notification,
)
from .models import (
    OrderEdition,
    PickupSlot,
    RzutItem,
    RzutOrder,
    RzutOrderEvent,
)
from .payment import (
    P24RefundError,
    P24RefundRequest,
    get_rzut_refund,
    refund_rzut_transaction,
)


TERMINAL_FULFILLMENT_STAGES = {
    RzutOrder.FulfillmentStage.PICKED_UP,
    RzutOrder.FulfillmentStage.CANCELLED,
}


class FulfillmentAllocationError(RuntimeError):
    pass


@dataclass(frozen=True)
class PickupDetails:
    date: date
    place: str
    address: str
    starts_at: time
    ends_at: time
    instructions: str

    @classmethod
    def from_source(cls, source):
        return cls(
            date=source.pickup_date,
            place=source.pickup_place_name,
            address=source.pickup_address,
            starts_at=source.pickup_starts_at,
            ends_at=source.pickup_ends_at,
            instructions=source.pickup_instructions,
        )

    @classmethod
    def from_json(cls, values):
        return cls(
            date=date.fromisoformat(values["date"]),
            place=values["place"],
            address=values["address"],
            starts_at=time.fromisoformat(values["starts_at"]),
            ends_at=time.fromisoformat(values["ends_at"]),
            instructions=values["instructions"],
        )

    def to_json(self):
        return {
            "date": self.date.isoformat(),
            "place": self.place,
            "address": self.address,
            "starts_at": self.starts_at.isoformat(),
            "ends_at": self.ends_at.isoformat(),
            "instructions": self.instructions,
        }

    def map_slot_from(self, previous, slot):
        anchor = date.min
        shift = datetime.combine(anchor, self.starts_at) - datetime.combine(
            anchor, previous.starts_at
        )
        mapped_start = datetime.combine(anchor, slot.starts_at) + shift
        mapped_end = datetime.combine(anchor, slot.ends_at) + shift
        window_start = datetime.combine(anchor, self.starts_at)
        window_end = datetime.combine(anchor, self.ends_at)
        if mapped_start < window_start or mapped_end > window_end:
            raise FulfillmentAllocationError(
                "Przedział Odbioru Zamówienia nie mieści się w nowych "
                "godzinach odbioru Rzutu."
            )
        return PickupSlot(mapped_start.time(), mapped_end.time())

    def as_email_text(self):
        return (
            f"{self.date:%d.%m.%Y}, "
            f"{self.starts_at:%H:%M}–{self.ends_at:%H:%M}\n"
            f"{self.place}, {self.address}\n"
            f"Instrukcja: {self.instructions}"
        )


@dataclass(frozen=True)
class DeliveryResult:
    sent: bool
    error: str = ""


@dataclass(frozen=True)
class RefundResult:
    outcome: "RefundOutcome"
    order: RzutOrder
    error: str = ""

    @property
    def completed(self):
        return self.outcome in {
            RefundOutcome.COMPLETED,
            RefundOutcome.COMPLETED_WITH_WARNING,
        }


class RefundOutcome(Enum):
    REQUESTED = "requested"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNING = "completed_with_warning"
    FAILED = "failed"


@dataclass(frozen=True)
class PreparedRefund:
    order: RzutOrder
    request: P24RefundRequest
    was_previously_requested: bool


def _actor_values(actor):
    return {"actor": actor, "actor_email": actor.email}


def _deliver_with_audit(
    *,
    order,
    actor,
    send: Callable[[], None],
    mark_sent: Callable[[datetime], None],
    mark_failed: Callable[[str], None],
    sent_kind,
    failed_kind,
    context,
):
    try:
        send()
    except Exception as exc:
        error = str(exc)
        mark_failed(error)
        RzutOrderEvent.objects.create(
            order=order,
            kind=failed_kind,
            context={**context, "error": error},
            **_actor_values(actor),
        )
        return DeliveryResult(sent=False, error=error)
    sent_at = timezone.now()
    mark_sent(sent_at)
    RzutOrderEvent.objects.create(
        order=order,
        kind=sent_kind,
        context=context,
        **_actor_values(actor),
    )
    return DeliveryResult(sent=True)


def _recorded_pool_decision(order):
    if order.cancelled_quantity_restored is not None:
        return order.cancelled_quantity_restored
    event = order.events.filter(
        kind=RzutOrderEvent.Kind.FULFILLMENT_STAGE_CHANGED,
        context__to=RzutOrder.FulfillmentStage.CANCELLED,
    ).first()
    if event is None:
        return None
    return event.context.get("pool_restored")


def _change_cancelled_pool_decision(*, order, restore_pool):
    previous_decision = _recorded_pool_decision(order)
    if previous_decision is None:
        raise FulfillmentAllocationError(
            "Nie można ustalić wcześniejszej decyzji o Puli anulowanego "
            "Zamówienia Rzutu."
        )
    if previous_decision == restore_pool:
        return previous_decision
    for line in order.items.order_by("rzut_item_id"):
        rzut_item = RzutItem.objects.filter(pk=line.rzut_item_id)
        if restore_pool:
            changed = rzut_item.filter(
                withdrawn_quantity__gte=line.quantity
            ).update(
                withdrawn_quantity=F("withdrawn_quantity") - line.quantity
            )
        else:
            changed = rzut_item.filter(
                pool__gte=(
                    F("allocated_quantity")
                    + F("withdrawn_quantity")
                    + line.quantity
                )
            ).update(
                withdrawn_quantity=F("withdrawn_quantity") + line.quantity
            )
        if not changed:
            raise FulfillmentAllocationError(
                "Nie można zmienić decyzji o Puli anulowanego Zamówienia Rzutu."
            )
    order.cancelled_quantity_restored = restore_pool
    order.save(update_fields=["cancelled_quantity_restored", "updated_at"])
    return restore_pool


def _cancel_locked_order(*, order, actor, restore_pool, allow_picked_up=False):
    if order.fulfillment_stage == RzutOrder.FulfillmentStage.CANCELLED:
        actual_pool_decision = _change_cancelled_pool_decision(
            order=order,
            restore_pool=restore_pool,
        )
        return order, actual_pool_decision
    if (
        order.fulfillment_stage == RzutOrder.FulfillmentStage.PICKED_UP
        and not allow_picked_up
    ):
        raise FulfillmentAllocationError(
            "Nie można anulować odebranego Zamówienia Rzutu."
        )
    previous_stage = order.fulfillment_stage
    for line in order.items.order_by("rzut_item_id"):
        available_line = RzutItem.objects.filter(
            pk=line.rzut_item_id,
            allocated_quantity__gte=line.quantity,
        )
        updates = {
            "allocated_quantity": F("allocated_quantity") - line.quantity
        }
        if not restore_pool:
            updates["withdrawn_quantity"] = (
                F("withdrawn_quantity") + line.quantity
            )
        released = available_line.update(**updates)
        if not released:
            raise FulfillmentAllocationError(
                "Nie można zwolnić Puli anulowanego Zamówienia Rzutu."
            )
    order.fulfillment_stage = RzutOrder.FulfillmentStage.CANCELLED
    order.cancelled_quantity_restored = restore_pool
    order.save(
        update_fields=[
            "fulfillment_stage",
            "cancelled_quantity_restored",
            "updated_at",
        ]
    )
    RzutOrderEvent.objects.create(
        order=order,
        kind=RzutOrderEvent.Kind.FULFILLMENT_STAGE_CHANGED,
        context={
            "from": previous_stage,
            "to": RzutOrder.FulfillmentStage.CANCELLED,
            "pool_restored": restore_pool,
        },
        **_actor_values(actor),
    )
    return order, restore_pool


@transaction.atomic
def cancel_rzut_order(*, order_id, actor, restore_pool):
    order = RzutOrder.objects.select_for_update().get(pk=order_id)
    OrderEdition.objects.filter(pk=order.rzut_id).update(
        allocation_revision=F("allocation_revision") + 1
    )
    order, _ = _cancel_locked_order(
        order=order,
        actor=actor,
        restore_pool=restore_pool,
    )
    return order


def is_rzut_order_refundable(order):
    return (
        order.payment_status == RzutOrder.PaymentStatus.PAID
        and order.payment_method == RzutOrder.PaymentMethod.P24
        and order.p24_order_id is not None
        and bool(order.p24_session_id)
        and order.total > 0
    )


@transaction.atomic
def _prepare_refund(order_id):
    order = RzutOrder.objects.select_for_update().get(pk=order_id)
    if not is_rzut_order_refundable(order):
        raise P24RefundError(
            "To Zamówienie Rzutu nie kwalifikuje się do pełnego zwrotu Przelewy24."
        )
    was_previously_requested = bool(
        order.p24_refund_request_id and order.p24_refunds_uuid
    )
    fields = []
    if not order.p24_refund_request_id:
        order.p24_refund_request_id = f"refund-{uuid.uuid4().hex}"
        fields.append("p24_refund_request_id")
    if not order.p24_refunds_uuid:
        order.p24_refunds_uuid = uuid.uuid4().hex
        fields.append("p24_refunds_uuid")
    if fields:
        order.save(update_fields=[*fields, "updated_at"])
    refund_request = P24RefundRequest(
        p24_order_id=order.p24_order_id,
        p24_session_id=order.p24_session_id,
        amount=order.total,
        request_id=order.p24_refund_request_id,
        refunds_uuid=order.p24_refunds_uuid,
        description=f"Zwrot KK {order.number}"[:35],
    )
    return PreparedRefund(
        order=order,
        request=refund_request,
        was_previously_requested=was_previously_requested,
    )


@transaction.atomic
def _record_refund_failure(*, order_id, actor, error, restore_pool):
    order = RzutOrder.objects.select_for_update().get(pk=order_id)
    if order.payment_status == RzutOrder.PaymentStatus.REFUNDED:
        return RefundResult(outcome=RefundOutcome.COMPLETED, order=order)
    order.p24_refund_error = error
    order.save(update_fields=["p24_refund_error", "updated_at"])
    RzutOrderEvent.objects.create(
        order=order,
        kind=RzutOrderEvent.Kind.REFUND_FAILED,
        context={
            "amount": str(order.total),
            "requested_pool_restore": restore_pool,
            "pool_restored": None,
            "error": error,
            "request_id": order.p24_refund_request_id,
        },
        **_actor_values(actor),
    )
    return RefundResult(
        outcome=RefundOutcome.FAILED,
        order=order,
        error=error,
    )


@transaction.atomic
def _record_refund_requested(*, order_id, actor, provider_result, restore_pool):
    order = RzutOrder.objects.select_for_update().get(pk=order_id)
    if order.payment_status == RzutOrder.PaymentStatus.REFUNDED:
        return RefundResult(outcome=RefundOutcome.COMPLETED, order=order)
    order.p24_refund_error = ""
    order.p24_refund_result = provider_result
    order.save(
        update_fields=[
            "p24_refund_error",
            "p24_refund_result",
            "updated_at",
        ]
    )
    RzutOrderEvent.objects.create(
        order=order,
        kind=RzutOrderEvent.Kind.REFUND_REQUESTED,
        context={
            "amount": str(order.total),
            "requested_pool_restore": restore_pool,
            "provider_result": provider_result,
            "request_id": order.p24_refund_request_id,
        },
        **_actor_values(actor),
    )
    return RefundResult(outcome=RefundOutcome.REQUESTED, order=order)


@transaction.atomic
def _complete_refund(*, order_id, actor, restore_pool, provider_result):
    order = RzutOrder.objects.select_for_update().get(pk=order_id)
    if order.payment_status == RzutOrder.PaymentStatus.REFUNDED:
        return RefundResult(outcome=RefundOutcome.COMPLETED, order=order)
    OrderEdition.objects.filter(pk=order.rzut_id).update(
        allocation_revision=F("allocation_revision") + 1
    )
    previous_payment_status = order.payment_status
    allocation_error = ""
    actual_pool_decision = None
    try:
        with transaction.atomic():
            order, actual_pool_decision = _cancel_locked_order(
                order=order,
                actor=actor,
                restore_pool=restore_pool,
                allow_picked_up=True,
            )
    except FulfillmentAllocationError as exc:
        allocation_error = str(exc)
        order.refresh_from_db()
        order.requires_attention = True
        order.attention_message = (
            "Przelewy24 potwierdziło pełny zwrot, ale nie udało się "
            "rozliczyć Puli ani anulować Etapu Realizacji: "
            f"{allocation_error}"
        )
    order.payment_status = RzutOrder.PaymentStatus.REFUNDED
    order.p24_refunded_at = timezone.now()
    order.p24_refund_error = ""
    order.p24_refund_result = provider_result
    order.save(
        update_fields=[
            "payment_status",
            "p24_refunded_at",
            "p24_refund_error",
            "p24_refund_result",
            "fulfillment_stage",
            "requires_attention",
            "attention_message",
            "updated_at",
        ]
    )
    RzutOrderEvent.objects.create(
        order=order,
        kind=RzutOrderEvent.Kind.REFUND_SUCCEEDED,
        context={
            "amount": str(order.total),
            "payment_status_from": previous_payment_status,
            "payment_status_to": RzutOrder.PaymentStatus.REFUNDED,
            "requested_pool_restore": restore_pool,
            "pool_restored": actual_pool_decision,
            "allocation_error": allocation_error,
            "fulfillment_stage": order.fulfillment_stage,
            "request_id": order.p24_refund_request_id,
        },
        **_actor_values(actor),
    )
    outcome = (
        RefundOutcome.COMPLETED_WITH_WARNING
        if allocation_error
        else RefundOutcome.COMPLETED
    )
    return RefundResult(
        outcome=outcome,
        order=order,
        error=allocation_error,
    )


def refund_rzut_order(*, order_id, actor, restore_pool):
    try:
        prepared = _prepare_refund(order_id)
    except P24RefundError as exc:
        return RefundResult(
            outcome=RefundOutcome.FAILED,
            order=RzutOrder.objects.get(pk=order_id),
            error=str(exc),
        )
    if prepared.was_previously_requested:
        try:
            existing_refund = get_rzut_refund(prepared.request)
        except (P24RefundError, RequestException) as exc:
            return _record_refund_failure(
                order_id=order_id,
                actor=actor,
                error=str(exc),
                restore_pool=restore_pool,
            )
        if existing_refund is not None:
            if existing_refund["completed"]:
                return _complete_refund(
                    order_id=order_id,
                    actor=actor,
                    restore_pool=restore_pool,
                    provider_result=existing_refund,
                )
            return _record_refund_requested(
                order_id=order_id,
                actor=actor,
                provider_result=existing_refund,
                restore_pool=restore_pool,
            )
    try:
        provider_result = refund_rzut_transaction(prepared.request)
    except (P24RefundError, RequestException) as exc:
        return _record_refund_failure(
            order_id=order_id,
            actor=actor,
            error=str(exc),
            restore_pool=restore_pool,
        )
    return _record_refund_requested(
        order_id=order_id,
        actor=actor,
        provider_result=provider_result,
        restore_pool=restore_pool,
    )


def deliver_ready_notification(*, order, actor):
    if order.fulfillment_stage == RzutOrder.FulfillmentStage.PREPARING:
        order.fulfillment_stage = RzutOrder.FulfillmentStage.READY
        order.save(update_fields=["fulfillment_stage", "updated_at"])
        RzutOrderEvent.objects.create(
            order=order,
            kind=RzutOrderEvent.Kind.FULFILLMENT_STAGE_CHANGED,
            context={
                "from": RzutOrder.FulfillmentStage.PREPARING,
                "to": RzutOrder.FulfillmentStage.READY,
            },
            **_actor_values(actor),
        )

    def mark_failed(error):
        order.ready_notification_error = error
        order.save(update_fields=["ready_notification_error", "updated_at"])

    def mark_sent(sent_at):
        order.ready_notification_sent_at = sent_at
        order.ready_notification_error = ""
        order.save(
            update_fields=[
                "ready_notification_sent_at",
                "ready_notification_error",
                "updated_at",
            ]
        )

    return _deliver_with_audit(
        order=order,
        actor=actor,
        send=lambda: send_rzut_order_ready_notification(order),
        mark_sent=mark_sent,
        mark_failed=mark_failed,
        sent_kind=RzutOrderEvent.Kind.READY_NOTIFICATION_SENT,
        failed_kind=RzutOrderEvent.Kind.READY_NOTIFICATION_FAILED,
        context={"recipient": order.customer_email},
    )


def deliver_pickup_notification(*, notification, actor):
    order = notification.order

    def mark_failed(error):
        notification.error = error
        notification.save(update_fields=["error"])

    def mark_sent(sent_at):
        notification.sent_at = sent_at
        notification.error = ""
        notification.save(update_fields=["sent_at", "error"])

    return _deliver_with_audit(
        order=order,
        actor=actor,
        send=lambda: send_rzut_pickup_change_notification(notification),
        mark_sent=mark_sent,
        mark_failed=mark_failed,
        sent_kind=RzutOrderEvent.Kind.PICKUP_NOTIFICATION_SENT,
        failed_kind=RzutOrderEvent.Kind.PICKUP_NOTIFICATION_FAILED,
        context={
            "pickup_change_id": notification.change_id,
            "recipient": order.customer_email,
        },
    )
