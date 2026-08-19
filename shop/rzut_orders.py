from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Q, Sum

from .models import (
    Reservation,
    ReservationItem,
    RzutItem,
    RzutOrder,
    RzutOrderItem,
)


@dataclass(frozen=True)
class RzutOrderLineSource:
    rzut_item: RzutItem
    unit_price: Decimal
    quantity: int


def customer_allocated_quantity(*, rzut_item_id, customer_email):
    reservation_quantity = (
        ReservationItem.objects.filter(
            rzut_item_id=rzut_item_id,
            reservation__customer_email=customer_email,
        )
        .filter(
            Q(reservation__status=Reservation.Status.ACTIVE)
            | Q(
                reservation__status=Reservation.Status.CONFIRMED,
                reservation__rzut_order__isnull=True,
            )
        )
        .aggregate(total=Sum("quantity"))["total"]
        or 0
    )
    order_quantity = (
        RzutOrderItem.objects.filter(
            rzut_item_id=rzut_item_id,
            order__customer_email=customer_email,
        )
        .exclude(order__fulfillment_stage=RzutOrder.FulfillmentStage.CANCELLED)
        .aggregate(total=Sum("quantity"))["total"]
        or 0
    )
    return reservation_quantity + order_quantity


def materialize_rzut_order_items(*, order, lines):
    RzutOrderItem.objects.bulk_create([
        RzutOrderItem(
            order=order,
            rzut_item=line.rzut_item,
            product_name=line.rzut_item.product.title,
            portion=line.rzut_item.portion,
            unit_price=line.unit_price,
            quantity=line.quantity,
            line_total=line.unit_price * line.quantity,
        )
        for line in lines
    ])
