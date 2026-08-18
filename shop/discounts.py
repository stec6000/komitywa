from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import DiscountCode, Reservation


MONEY_QUANTUM = Decimal("0.01")


class DiscountCodeUnavailable(ValueError):
    def __init__(self, message):
        self.user_message = message
        super().__init__(message)


class DiscountAllocationError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReclaimedDiscountUse:
    warnings: tuple[str, ...]


def normalize_discount_code(code):
    return code.strip().upper()


def calculate_discount(discount_code, subtotal):
    if discount_code.discount_type == DiscountCode.Type.PERCENTAGE:
        discount = subtotal * discount_code.value / Decimal("100")
    else:
        discount = discount_code.value
    discount = discount.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
    return min(discount, subtotal)


def get_applicable_discount(*, code, rzut_id, subtotal, now=None):
    now = now or timezone.now()
    normalized_code = normalize_discount_code(code)
    if not normalized_code:
        raise DiscountCodeUnavailable("Podaj Kod Rabatowy.")
    try:
        discount_code = DiscountCode.objects.get(code=normalized_code)
    except DiscountCode.DoesNotExist as exc:
        raise DiscountCodeUnavailable(
            "Ten Kod Rabatowy jest nieprawidłowy albo niedostępny."
        ) from exc

    discount_amount = validate_discount_code(
        discount_code=discount_code,
        rzut_id=rzut_id,
        subtotal=subtotal,
        now=now,
    )
    return discount_code, discount_amount, subtotal - discount_amount


def validate_discount_code(*, discount_code, rzut_id, subtotal, now=None):
    now = now or timezone.now()

    if not discount_code.is_active:
        raise DiscountCodeUnavailable("Ten Kod Rabatowy jest wyłączony.")
    if discount_code.rzut_id not in (None, rzut_id):
        raise DiscountCodeUnavailable(
            "Ten Kod Rabatowy nie obowiązuje w tym Rzucie."
        )
    if discount_code.valid_from and now < discount_code.valid_from:
        raise DiscountCodeUnavailable(
            "Okres ważności tego Kodu Rabatowego jeszcze się nie rozpoczął."
        )
    if discount_code.valid_until and now >= discount_code.valid_until:
        raise DiscountCodeUnavailable("Ten Kod Rabatowy wygasł.")
    if (
        discount_code.minimum_order_total is not None
        and subtotal < discount_code.minimum_order_total
    ):
        raise DiscountCodeUnavailable(
            "Minimalna wartość Zamówienia dla tego Kodu Rabatowego wynosi "
            f"{discount_code.minimum_order_total:.2f} zł."
        )
    if (
        discount_code.usage_limit is not None
        and discount_code.allocated_uses >= discount_code.usage_limit
    ):
        raise DiscountCodeUnavailable(
            "Łączny limit użyć tego Kodu Rabatowego został wyczerpany."
        )

    discount_amount = calculate_discount(discount_code, subtotal)
    return discount_amount


def reserve_discount_use(
    *,
    code,
    rzut_id,
    subtotal,
    customer_email,
    now=None,
):
    normalized_code = normalize_discount_code(code)
    with transaction.atomic():
        locked = DiscountCode.objects.filter(code=normalized_code).update(
            allocation_revision=F("allocation_revision") + 1
        )
        if not locked:
            raise DiscountCodeUnavailable(
                "Ten Kod Rabatowy jest nieprawidłowy albo niedostępny."
            )
        discount_code = DiscountCode.objects.get(code=normalized_code)
        discount_amount = validate_discount_code(
            discount_code=discount_code,
            rzut_id=rzut_id,
            subtotal=subtotal,
            now=now,
        )
        customer_uses = Reservation.objects.filter(
            discount_code=discount_code,
            customer_email=customer_email,
            status__in=[
                Reservation.Status.ACTIVE,
                Reservation.Status.CONFIRMED,
            ],
        ).count()
        if customer_uses >= discount_code.per_customer_limit:
            raise DiscountCodeUnavailable(
                "Limit użyć tego Kodu Rabatowego dla podanego e-maila "
                "został wyczerpany."
            )
        DiscountCode.objects.filter(pk=discount_code.pk).update(
            allocated_uses=F("allocated_uses") + 1
        )
        return discount_code, discount_amount


def release_discount_use(*, discount_code_id):
    with transaction.atomic():
        released = DiscountCode.objects.filter(
            pk=discount_code_id,
            allocated_uses__gte=1,
        ).update(allocated_uses=F("allocated_uses") - 1)
        if not released:
            raise DiscountAllocationError(
                "Nie można zwolnić użycia Kodu Rabatowego."
            )


def reclaim_discount_use(*, discount_code_id, customer_email):
    with transaction.atomic():
        locked = DiscountCode.objects.filter(pk=discount_code_id).update(
            allocation_revision=F("allocation_revision") + 1
        )
        if not locked:
            raise DiscountAllocationError(
                "Nie można przywrócić użycia Kodu Rabatowego."
            )
        discount_code = DiscountCode.objects.get(pk=discount_code_id)
        new_uses = discount_code.allocated_uses + 1
        customer_uses = Reservation.objects.filter(
            discount_code=discount_code,
            customer_email=customer_email,
            status__in=[
                Reservation.Status.ACTIVE,
                Reservation.Status.CONFIRMED,
            ],
        ).count()
        DiscountCode.objects.filter(pk=discount_code.pk).update(
            allocated_uses=F("allocated_uses") + 1
        )

        warnings = []
        if (
            discount_code.usage_limit is not None
            and new_uses > discount_code.usage_limit
        ):
            warnings.append(
                f"Kod Rabatowy {discount_code.code}: "
                f"{new_uses}/{discount_code.usage_limit} użyć"
            )
        new_customer_uses = customer_uses + 1
        if new_customer_uses > discount_code.per_customer_limit:
            warnings.append(
                f"Kod Rabatowy {discount_code.code} dla "
                f"{customer_email}: {new_customer_uses}/"
                f"{discount_code.per_customer_limit} użyć"
            )
        return ReclaimedDiscountUse(warnings=tuple(warnings))
