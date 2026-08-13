from decimal import Decimal, InvalidOperation

from django.utils import timezone

from .models import OrderEdition, RzutItem


RZUT_CART_SESSION_KEY = "rzut_cart"


class DifferentRzutError(ValueError):
    pass


class InvalidQuantityError(ValueError):
    pass


class RzutCart:
    def __init__(self, request):
        self.session = request.session
        self.data = self.session.get(RZUT_CART_SESSION_KEY)
        if self.data is None:
            self.data = {"rzut_id": None, "items": {}}
            self.save()

    @property
    def items(self):
        return self.data["items"]

    @classmethod
    def count_from_session(cls, session):
        data = session.get(RZUT_CART_SESSION_KEY, {})
        return sum(
            item["quantity"] for item in data.get("items", {}).values()
        )

    def add(self, item, quantity=1):
        self._validate_quantity(quantity)
        if self.data["rzut_id"] not in (None, item.rzut_id):
            raise DifferentRzutError

        self.data["rzut_id"] = item.rzut_id
        item_id = str(item.pk)
        if item_id in self.items:
            self.items[item_id]["quantity"] += quantity
        else:
            self.items[item_id] = {
                "quantity": quantity,
                "price": str(item.price),
            }
        self.save()

    def update(self, item_id, quantity):
        self._validate_quantity(quantity)
        item_id = str(item_id)
        if item_id in self.items:
            self.items[item_id]["quantity"] = quantity
            self.save()

    def remove(self, item_id):
        self.items.pop(str(item_id), None)
        if not self.items:
            self.data["rzut_id"] = None
        self.save()

    def snapshot(self):
        item_ids = list(self.items)
        items = RzutItem.objects.filter(pk__in=item_ids).select_related(
            "product",
            "rzut",
        )
        items_by_id = {str(item.pk): item for item in items}
        removed_items = []
        now = timezone.now()
        for item_id in list(self.items):
            item = items_by_id.get(item_id)
            if item is None:
                removed_items.append("Niedostępna Pozycja")
            elif not item.is_offered_at(now):
                removed_items.append(f"Pozycja „{item.product.title}”")
            else:
                continue
            del self.items[item_id]

        if removed_items:
            if not self.items:
                self.data["rzut_id"] = None
            self.save()

        lines = []
        total = Decimal("0.00")
        has_price_changes = False
        has_availability_errors = False
        for item_id, stored in self.items.items():
            item = items_by_id.get(item_id)
            if item is None:
                continue
            quantity = stored["quantity"]
            line_total = item.price * quantity
            total += line_total
            stored_price = Decimal(stored["price"])
            price_changed = stored_price != item.price
            has_price_changes = has_price_changes or price_changed
            availability_error = quantity > item.available_quantity
            has_availability_errors = (
                has_availability_errors or availability_error
            )
            lines.append({
                "item": item,
                "quantity": quantity,
                "stored_price": stored_price,
                "line_total": line_total,
                "price_changed": price_changed,
                "availability_error": availability_error,
                "available_quantity": item.available_quantity,
            })

        rzut = None
        if self.data["rzut_id"] is not None:
            rzut = OrderEdition.objects.filter(
                pk=self.data["rzut_id"]
            ).first()
        return {
            "rzut": rzut,
            "lines": lines,
            "total": total,
            "has_price_changes": has_price_changes,
            "has_availability_errors": has_availability_errors,
            "removed_items": removed_items,
        }

    def accept_current_prices(self, expected_prices):
        items = list(RzutItem.objects.filter(pk__in=self.items))
        if {str(item.pk) for item in items} != set(self.items):
            return False
        try:
            prices_still_match = all(
                Decimal(expected_prices[str(item.pk)]) == item.price
                for item in items
            )
        except (InvalidOperation, KeyError, ValueError):
            return False
        if not prices_still_match:
            return False

        for item in items:
            self.items[str(item.pk)]["price"] = str(item.price)
        self.save()
        return True

    def save(self):
        self.session[RZUT_CART_SESSION_KEY] = self.data
        self.session.modified = True

    @staticmethod
    def _validate_quantity(quantity):
        if not isinstance(quantity, int) or isinstance(quantity, bool):
            raise InvalidQuantityError
        if quantity < 1:
            raise InvalidQuantityError
