from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Callable

from django.db import transaction
from django.db.models import F
from django.utils import timezone

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


@transaction.atomic
def cancel_rzut_order(*, order_id, actor, restore_pool):
    rzut_id = RzutOrder.objects.values_list("rzut_id", flat=True).get(
        pk=order_id
    )
    OrderEdition.objects.filter(pk=rzut_id).update(
        allocation_revision=F("allocation_revision") + 1
    )
    order = RzutOrder.objects.select_for_update().get(pk=order_id)
    if order.fulfillment_stage == RzutOrder.FulfillmentStage.CANCELLED:
        return order
    if order.fulfillment_stage == RzutOrder.FulfillmentStage.PICKED_UP:
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
    order.save(update_fields=["fulfillment_stage", "updated_at"])
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
    return order


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
