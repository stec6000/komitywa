from dataclasses import dataclass
from datetime import time, timedelta
from decimal import Decimal

from django.db import OperationalError, transaction
from django.db.models import F, Sum
from django.utils import timezone

from .models import OrderEdition, Reservation, ReservationItem, RzutItem


RESERVATION_TIME_LIMIT_MINUTES = 15
RESERVATION_LIFETIME = timedelta(minutes=RESERVATION_TIME_LIMIT_MINUTES)


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


def fail_reservation(reservation):
    with transaction.atomic():
        OrderEdition.objects.filter(pk=reservation.rzut_id).update(
            allocation_revision=F("allocation_revision") + 1
        )
        current = Reservation.objects.select_for_update().get(
            pk=reservation.pk
        )
        if current.status != Reservation.Status.ACTIVE:
            return current

        for line in current.items.order_by("rzut_item_id"):
            released = RzutItem.objects.filter(
                pk=line.rzut_item_id,
                allocated_quantity__gte=line.quantity,
            ).update(
                allocated_quantity=F("allocated_quantity") - line.quantity
            )
            if not released:
                raise RuntimeError(
                    "Nie można zwolnić Puli dla nieudanej Rezerwacji."
                )
        current.status = Reservation.Status.FAILED
        current.save(update_fields=["status", "updated_at"])
        return current
