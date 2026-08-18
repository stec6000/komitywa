from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import OperationalError, transaction
from django.db.models import F
from django.utils import timezone

from .discounts import DiscountCodeUnavailable, reserve_discount_use
from .models import (
    OrderEdition,
    PickupSlot,
    RzutItem,
    RzutOrder,
)
from .reservations import normalize_customer_email
from .rzut_orders import (
    RzutOrderLineSource,
    customer_allocated_quantity,
    materialize_rzut_order_items,
)


@dataclass(frozen=True)
class ManualOrderLineRequest:
    item_id: int
    quantity: int


@dataclass(frozen=True)
class ManualOrderData:
    rzut_id: int
    customer_name: str
    customer_email: str
    customer_phone: str
    customer_notes: str
    pickup_slot: PickupSlot
    payment_status: str
    payment_method: str
    payment_method_details: str = ""
    discount_code: str = ""
    creation_token: UUID | None = None


class ManualOrderError(Exception):
    def __init__(self, message):
        self.user_message = message
        super().__init__(message)


class ManualOrderUnavailable(ManualOrderError):
    pass


def create_manual_order(*, data, lines, now=None):
    try:
        return _create_manual_order(data=data, lines=lines, now=now)
    except OperationalError as exc:
        raise ManualOrderUnavailable(
            "Inny administrator właśnie tworzy Zamówienie Ręczne dla tego "
            "Rzutu. "
            "Sprawdź Dostępność i spróbuj ponownie."
        ) from exc


def _create_manual_order(*, data, lines, now=None):
    now = now or timezone.now()
    if not data.customer_name.strip():
        raise ManualOrderUnavailable("Podaj imię i nazwisko Klienta.")
    normalized_email = normalize_customer_email(data.customer_email)
    try:
        validate_email(normalized_email)
    except ValidationError as exc:
        raise ManualOrderUnavailable("Podaj prawidłowy e-mail Klienta.") from exc
    if data.payment_status not in RzutOrder.PaymentStatus.values:
        raise ManualOrderUnavailable("Wybierz prawidłowy Status Płatności.")
    if data.payment_method not in RzutOrder.PaymentMethod.values:
        raise ManualOrderUnavailable("Wybierz prawidłową Metodę Płatności.")
    if (
        data.payment_method == RzutOrder.PaymentMethod.OTHER
        and not data.payment_method_details.strip()
    ):
        raise ManualOrderUnavailable("Wyjaśnij inną Metodę Płatności.")
    lines = sorted(lines, key=lambda line: line.item_id)
    if not lines or len({line.item_id for line in lines}) != len(lines):
        raise ManualOrderUnavailable(
            "Dodaj co najmniej jedną prawidłową Pozycję Rzutu."
        )
    if any(
        not isinstance(line.quantity, int)
        or isinstance(line.quantity, bool)
        or line.quantity < 1
        for line in lines
    ):
        raise ManualOrderUnavailable(
            "Każda Pozycja Rzutu musi mieć dodatnią liczbę sztuk."
        )

    with transaction.atomic():
        locked = OrderEdition.objects.filter(pk=data.rzut_id).update(
            allocation_revision=F("allocation_revision") + 1
        )
        if not locked:
            raise ManualOrderUnavailable("Ten Rzut nie istnieje.")
        if data.creation_token is not None:
            existing_order = RzutOrder.objects.filter(
                manual_creation_token=data.creation_token,
            ).first()
            if existing_order is not None:
                return existing_order
        rzut = OrderEdition.objects.get(pk=data.rzut_id)
        if data.pickup_slot not in rzut.pickup_slots():
            raise ManualOrderUnavailable(
                "Wybrany Przedział Odbioru nie jest dostępny w tym Rzucie."
            )

        item_ids = [line.item_id for line in lines]
        items = {
            item.pk: item
            for item in RzutItem.objects.filter(
                pk__in=item_ids,
                rzut_id=rzut.pk,
            ).select_related("product")
        }
        if set(items) != set(item_ids):
            raise ManualOrderUnavailable(
                "Co najmniej jedna Pozycja Rzutu nie należy do wybranego "
                "Rzutu."
            )

        for line in lines:
            item = items[line.item_id]
            if not item.is_active or item.product.type != "physical":
                raise ManualOrderUnavailable(
                    f"Pozycja Rzutu „{item.product.title}” nie jest aktywna."
                )
            if item.per_customer_limit is not None:
                if (
                    customer_allocated_quantity(
                        rzut_item_id=item.pk,
                        customer_email=normalized_email,
                    )
                    + line.quantity
                    > item.per_customer_limit
                ):
                    raise ManualOrderUnavailable(
                        f"Limit Klienta dla Pozycji Rzutu "
                        f"„{item.product.title}” wynosi "
                        f"{item.per_customer_limit} szt. w tym Rzucie."
                    )
            allocated = RzutItem.objects.filter(
                pk=item.pk,
                allocated_quantity__lte=F("pool") - line.quantity,
            ).update(
                allocated_quantity=F("allocated_quantity") + line.quantity
            )
            if not allocated:
                raise ManualOrderUnavailable(
                    f"Brakuje Dostępności dla Pozycji Rzutu "
                    f"„{item.product.title}”. Najpierw jawnie zwiększ jej Pulę."
                )

        subtotal = sum(
            (items[line.item_id].price * line.quantity for line in lines),
            Decimal("0.00"),
        )
        discount_code = None
        discount_amount = Decimal("0.00")
        if data.discount_code:
            try:
                discount_code, discount_amount = reserve_discount_use(
                    code=data.discount_code,
                    rzut_id=rzut.pk,
                    subtotal=subtotal,
                    customer_email=normalized_email,
                    now=now,
                )
            except DiscountCodeUnavailable as exc:
                raise ManualOrderUnavailable(exc.user_message) from exc
        total = subtotal - discount_amount
        no_payment = (
            data.payment_status == RzutOrder.PaymentStatus.NOT_REQUIRED
            and data.payment_method == RzutOrder.PaymentMethod.NONE
        )
        if total == Decimal("0.00") and not no_payment:
            raise ManualOrderUnavailable(
                "Należność 0,00 zł wymaga Statusu Płatności „nie wymaga "
                "płatności” i Metody Płatności „brak płatności”."
            )
        if total > Decimal("0.00") and (
            data.payment_status == RzutOrder.PaymentStatus.NOT_REQUIRED
            or data.payment_method == RzutOrder.PaymentMethod.NONE
        ):
            raise ManualOrderUnavailable(
                "Dodatnia należność wymaga płatnego Statusu i Metody Płatności."
            )
        payment_confirmed_at = (
            None
            if data.payment_status == RzutOrder.PaymentStatus.PENDING
            else now
        )
        order = RzutOrder.objects.create(
            reservation=None,
            is_manual=True,
            manual_creation_token=data.creation_token,
            rzut=rzut,
            customer_name=data.customer_name.strip(),
            customer_email=normalized_email,
            customer_phone=data.customer_phone.strip(),
            customer_notes=data.customer_notes.strip(),
            pickup_starts_at=data.pickup_slot.starts_at,
            pickup_ends_at=data.pickup_slot.ends_at,
            subtotal=subtotal,
            discount_amount=discount_amount,
            discount_code=discount_code,
            discount_code_snapshot=(discount_code.code if discount_code else ""),
            total=total,
            payment_status=data.payment_status,
            payment_method=data.payment_method,
            payment_method_details=data.payment_method_details.strip(),
            fulfillment_stage=RzutOrder.FulfillmentStage.NEW,
            p24_session_id=None,
            p24_order_id=None,
            data_processing_accepted_at=None,
            terms_accepted_at=None,
            payment_confirmed_at=payment_confirmed_at,
        )
        materialize_rzut_order_items(
            order=order,
            lines=[
                RzutOrderLineSource(
                    rzut_item=items[line.item_id],
                    unit_price=items[line.item_id].price,
                    quantity=line.quantity,
                )
                for line in lines
            ],
        )
        return order
