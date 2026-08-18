import logging
from dataclasses import dataclass
from datetime import time, timedelta
from decimal import Decimal

from django.db import OperationalError, transaction
from django.db.models import F, Sum
from django.utils import timezone

from .models import (
    OrderEdition,
    Reservation,
    ReservationItem,
    RzutItem,
    RzutOrder,
    RzutOrderItem,
)


logger = logging.getLogger(__name__)

RESERVATION_TIME_LIMIT_MINUTES = 15
RESERVATION_LIFETIME = timedelta(minutes=RESERVATION_TIME_LIMIT_MINUTES)
RESERVATION_RETENTION = timedelta(days=30)


@dataclass(frozen=True)
class ReservationLineRequest:
    item_id: int
    quantity: int
    expected_price: Decimal


@dataclass(frozen=True)
class ReservationCheckoutData:
    name: str
    email: str
    phone: str
    notes: str
    pickup_starts_at: time
    pickup_ends_at: time


class ReservationError(Exception):
    def __init__(self, message):
        self.user_message = message
        super().__init__(message)


class ReservationUnavailable(ReservationError):
    pass


class ReservationPriceChanged(ReservationError):
    pass


class ReservationCustomerLimitExceeded(ReservationError):
    pass


class ReservationConfirmationError(ReservationError):
    pass


def normalize_customer_email(email):
    return email.strip().casefold()


def create_reservation(*, rzut_id, lines, checkout, now=None):
    now = now or timezone.now()
    lines = sorted(lines, key=lambda line: line.item_id)
    if not lines or len({line.item_id for line in lines}) != len(lines):
        raise ReservationUnavailable(
            "Koszyk Rzutu jest pusty albo zawiera nieprawidłowe "
            "Pozycje Rzutu."
        )
    if any(
        not isinstance(line.quantity, int)
        or isinstance(line.quantity, bool)
        or line.quantity < 1
        for line in lines
    ):
        raise ReservationUnavailable(
            "Każda Pozycja Rzutu musi mieć dodatnią liczbę sztuk."
        )

    try:
        return _create_reservation(
            rzut_id=rzut_id,
            lines=lines,
            checkout=checkout,
            now=now,
        )
    except OperationalError as exc:
        raise ReservationUnavailable(
            "Inny Klient właśnie Rezerwuje te Pozycje Rzutu. "
            "Sprawdź Dostępność i spróbuj ponownie."
        ) from exc


def _create_reservation(*, rzut_id, lines, checkout, now):
    normalized_email = normalize_customer_email(checkout.email)
    with transaction.atomic():
        locked = OrderEdition.objects.filter(pk=rzut_id).update(
            allocation_revision=F("allocation_revision") + 1
        )
        if not locked:
            raise ReservationUnavailable("Ten Rzut nie jest już dostępny.")

        rzut = OrderEdition.objects.get(pk=rzut_id)
        if rzut.phase_at(now) != OrderEdition.Phase.OPEN:
            raise ReservationUnavailable(
                "Ten Rzut nie przyjmuje już nowych Rezerwacji."
            )
        pickup_slots = {
            (slot.starts_at, slot.ends_at) for slot in rzut.pickup_slots()
        }
        if (
            checkout.pickup_starts_at,
            checkout.pickup_ends_at,
        ) not in pickup_slots:
            raise ReservationUnavailable(
                "Wybrany Przedział Odbioru nie jest dostępny w tym Rzucie."
            )

        item_ids = [line.item_id for line in lines]
        items = {
            item.pk: item
            for item in RzutItem.objects.filter(
                pk__in=item_ids,
                rzut_id=rzut_id,
            ).select_related("product")
        }
        if set(items) != set(item_ids):
            raise ReservationUnavailable(
                "Co najmniej jedna Pozycja Rzutu nie jest już dostępna."
            )

        for line in lines:
            item = items[line.item_id]
            if not item.is_active or item.product.type != "physical":
                raise ReservationUnavailable(
                    f"Pozycja Rzutu „{item.product.title}” nie jest już "
                    "aktywna."
                )
            if item.price != line.expected_price:
                raise ReservationPriceChanged(
                    f"Cena Pozycji Rzutu „{item.product.title}” zmieniła się. "
                    "Sprawdź i zaakceptuj aktualną sumę."
                )

            if item.per_customer_limit is not None:
                already_allocated = (
                    ReservationItem.objects.filter(
                        rzut_item_id=item.pk,
                        reservation__rzut_id=rzut_id,
                        reservation__customer_email=normalized_email,
                        reservation__status__in=[
                            Reservation.Status.ACTIVE,
                            Reservation.Status.CONFIRMED,
                        ],
                    ).aggregate(total=Sum("quantity"))["total"]
                    or 0
                )
                if already_allocated + line.quantity > item.per_customer_limit:
                    raise ReservationCustomerLimitExceeded(
                        f"Limit Klienta dla Pozycji Rzutu "
                        f"„{item.product.title}” "
                        f"wynosi {item.per_customer_limit} szt. w tym Rzucie."
                    )

            updated = RzutItem.objects.filter(
                pk=item.pk,
                rzut_id=rzut_id,
                is_active=True,
                product__type="physical",
                price=line.expected_price,
                allocated_quantity__lte=F("pool") - line.quantity,
            ).update(
                allocated_quantity=F("allocated_quantity") + line.quantity
            )
            if not updated:
                raise ReservationUnavailable(
                    f"Brakuje Dostępności dla Pozycji Rzutu "
                    f"„{item.product.title}”. Zmień liczbę sztuk."
                )

        total = sum(
            (line.expected_price * line.quantity for line in lines),
            Decimal("0.00"),
        )
        reservation = Reservation.objects.create(
            rzut=rzut,
            customer_name=checkout.name.strip(),
            customer_email=normalized_email,
            customer_phone=checkout.phone.strip(),
            customer_notes=checkout.notes.strip(),
            pickup_starts_at=checkout.pickup_starts_at,
            pickup_ends_at=checkout.pickup_ends_at,
            total=total,
            data_processing_accepted_at=now,
            terms_accepted_at=now,
            expires_at=now + RESERVATION_LIFETIME,
        )
        ReservationItem.objects.bulk_create([
            ReservationItem(
                reservation=reservation,
                rzut_item=items[line.item_id],
                quantity=line.quantity,
                unit_price=line.expected_price,
            )
            for line in lines
        ])
        return reservation


def _release_active_reservation(
    reservation,
    *,
    target_status,
    expired_by=None,
):
    with transaction.atomic():
        OrderEdition.objects.filter(pk=reservation.rzut_id).update(
            allocation_revision=F("allocation_revision") + 1
        )
        current = Reservation.objects.select_for_update().get(
            pk=reservation.pk
        )
        if (
            current.status != Reservation.Status.ACTIVE
            or (expired_by is not None and current.expires_at > expired_by)
        ):
            return current, False

        for line in current.items.order_by("rzut_item_id"):
            released = RzutItem.objects.filter(
                pk=line.rzut_item_id,
                allocated_quantity__gte=line.quantity,
            ).update(
                allocated_quantity=F("allocated_quantity") - line.quantity
            )
            if not released:
                raise RuntimeError(
                    "Nie można zwolnić Puli dla nieaktywnej Rezerwacji."
                )
        current.status = target_status
        current.save(update_fields=["status", "updated_at"])
        return current, True


def fail_reservation(reservation):
    current, _ = _release_active_reservation(
        reservation,
        target_status=Reservation.Status.FAILED,
    )
    return current


def expire_due_reservations(*, now=None):
    now = now or timezone.now()
    reservations = list(
        Reservation.objects.filter(
            status=Reservation.Status.ACTIVE,
            expires_at__lte=now,
        ).only("pk", "rzut_id")
    )
    expired_count = 0
    for reservation in reservations:
        _, changed = _release_active_reservation(
            reservation,
            target_status=Reservation.Status.EXPIRED,
            expired_by=now,
        )
        if changed:
            expired_count += 1
    return expired_count


def delete_old_inactive_reservations(*, now=None):
    now = now or timezone.now()
    reservations = Reservation.objects.filter(
        status__in=[
            Reservation.Status.EXPIRED,
            Reservation.Status.FAILED,
        ],
        updated_at__lt=now - RESERVATION_RETENTION,
    )
    deleted_count = reservations.count()
    reservations.delete()
    return deleted_count


def confirm_reservation(*, reservation_id, p24_order_id, confirmed_at=None):
    confirmed_at = confirmed_at or timezone.now()
    with transaction.atomic():
        reservation_rzut_id = Reservation.objects.values_list(
            "rzut_id", flat=True
        ).get(pk=reservation_id)
        OrderEdition.objects.filter(pk=reservation_rzut_id).update(
            allocation_revision=F("allocation_revision") + 1
        )
        reservation = (
            Reservation.objects.select_for_update()
            .select_related("rzut")
            .get(pk=reservation_id)
        )
        existing_order = RzutOrder.objects.filter(
            reservation=reservation
        ).first()
        if existing_order is not None:
            return existing_order, False
        pool_was_released = reservation.status == Reservation.Status.EXPIRED
        is_late_payment = (
            pool_was_released or confirmed_at >= reservation.expires_at
        )
        if reservation.status not in [
            Reservation.Status.ACTIVE,
            Reservation.Status.EXPIRED,
        ]:
            raise ReservationConfirmationError(
                "Rezerwacja nie oczekuje na potwierdzenie płatności."
            )

        overallocated_items = []
        if pool_was_released:
            for line in reservation.items.select_related(
                "rzut_item__product"
            ).order_by("rzut_item_id"):
                item = RzutItem.objects.get(pk=line.rzut_item_id)
                new_allocation = item.allocated_quantity + line.quantity
                RzutItem.objects.filter(pk=item.pk).update(
                    allocated_quantity=F("allocated_quantity") + line.quantity
                )
                if new_allocation > item.pool:
                    overallocated_items.append(
                        f"{item.product.title}: {new_allocation}/{item.pool}"
                    )

        attention_message = ""
        if is_late_payment:
            allocation_warning = (
                f"Przekroczenie Puli: {', '.join(overallocated_items)}."
                if overallocated_items
                else "Brak bieżącego przekroczenia Puli."
            )
            attention_message = (
                "Późna płatność P24 potwierdziła Rezerwację po terminie. "
                f"{allocation_warning} Zweryfikuj produkcję i Zamówienie."
            )

        order = RzutOrder.objects.create(
            reservation=reservation,
            rzut=reservation.rzut,
            customer_name=reservation.customer_name,
            customer_email=reservation.customer_email,
            customer_phone=reservation.customer_phone,
            customer_notes=reservation.customer_notes,
            pickup_starts_at=reservation.pickup_starts_at,
            pickup_ends_at=reservation.pickup_ends_at,
            total=reservation.total,
            payment_status=RzutOrder.PaymentStatus.PAID,
            payment_method=RzutOrder.PaymentMethod.P24,
            fulfillment_stage=RzutOrder.FulfillmentStage.NEW,
            p24_session_id=reservation.p24_session_id,
            p24_order_id=p24_order_id,
            data_processing_accepted_at=(
                reservation.data_processing_accepted_at
            ),
            terms_accepted_at=reservation.terms_accepted_at,
            payment_confirmed_at=confirmed_at,
            requires_attention=is_late_payment,
            attention_message=attention_message,
        )
        reservation_items = reservation.items.select_related(
            "rzut_item__product"
        ).order_by("rzut_item_id")
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
            for line in reservation_items
        ])
        reservation.status = Reservation.Status.CONFIRMED
        reservation.save(update_fields=["status", "updated_at"])
        if is_late_payment:
            logger.critical(
                "PILNE: %s Rezerwacja %d, Zamówienie Rzutu %s.",
                attention_message,
                reservation.pk,
                order.number,
            )
        return order, True
