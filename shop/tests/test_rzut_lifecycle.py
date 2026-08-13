from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from shop.models import OrderEdition, Product, RzutItem


class TestRzutPhase(TestCase):
    def test_published_rzut_phase_is_derived_from_sales_window(self):
        now = timezone.now()
        rzut = OrderEdition.objects.create(
            title="Rzut sierpniowy",
            status=OrderEdition.Status.PUBLISHED,
            opens_at=now + timedelta(hours=1),
            closes_at=now + timedelta(hours=3),
        )

        self.assertEqual(
            rzut.phase_at(now),
            OrderEdition.Phase.UPCOMING,
        )
        self.assertEqual(
            rzut.phase_at(now + timedelta(hours=2)),
            OrderEdition.Phase.OPEN,
        )
        self.assertEqual(
            rzut.phase_at(now + timedelta(hours=4)),
            OrderEdition.Phase.ENDED,
        )


class TestPickupSlots(TestCase):
    def test_generates_hourly_slots_with_shorter_last_slot(self):
        rzut = OrderEdition.objects.create(
            title="Rzut z odbiorem",
            pickup_date=date(2026, 8, 16),
            pickup_starts_at=time(10, 30),
            pickup_ends_at=time(13, 15),
        )

        slots = rzut.pickup_slots()

        self.assertEqual(
            [(slot.starts_at, slot.ends_at) for slot in slots],
            [
                (time(10, 30), time(11, 30)),
                (time(11, 30), time(12, 30)),
                (time(12, 30), time(13, 15)),
            ],
        )


class TestRzutPublication(TestCase):
    def complete_rzut(self, **overrides):
        now = timezone.now()
        values = {
            "title": "Kompletny Rzut",
            "description": "Niedzielne wypieki.",
            "opens_at": now,
            "closes_at": now + timedelta(hours=1),
            "pickup_date": timezone.localdate() + timedelta(days=1),
            "pickup_place_name": "Kuchenna Komitywa",
            "pickup_address": "ul. Bukowa 14, Białystok",
            "pickup_starts_at": time(10, 0),
            "pickup_ends_at": time(13, 0),
            "pickup_instructions": "Wejście od ogrodu.",
        }
        values.update(overrides)
        return OrderEdition.objects.create(**values)

    def add_complete_item(self, rzut, title="Chleb wiejski"):
        product = Product.objects.create(
            title=title,
            description="Chleb na zakwasie.",
            ingredients="mąka, woda, sól",
            allergens="gluten",
            price=Decimal("24.00"),
        )
        return RzutItem.objects.create(
            rzut=rzut,
            product=product,
            price=Decimal("26.00"),
            portion="bochenek ok. 750 g",
            pool=10,
        )

    def test_publishing_incomplete_rzut_lists_missing_information(self):
        rzut = OrderEdition.objects.create(title="Niekompletny Rzut")
        rzut.status = OrderEdition.Status.PUBLISHED

        with self.assertRaises(ValidationError) as error:
            rzut.full_clean()

        messages = error.exception.message_dict["status"]
        self.assertIn("Uzupełnij opis Rzutu.", messages)
        self.assertIn("Ustaw początek sprzedaży.", messages)
        self.assertIn("Ustaw koniec sprzedaży.", messages)
        self.assertIn("Ustaw dzień odbioru.", messages)
        self.assertIn("Uzupełnij nazwę miejsca odbioru.", messages)
        self.assertIn("Uzupełnij adres odbioru.", messages)
        self.assertIn("Ustaw godziny odbioru.", messages)
        self.assertIn("Uzupełnij instrukcję odbioru.", messages)
        self.assertIn(
            "Dodaj co najmniej jedną aktywną Pozycję Rzutu.",
            messages,
        )

    def test_publishing_lists_missing_product_information(self):
        rzut = self.complete_rzut()
        product = Product.objects.create(
            title="Chleb wiejski",
            description="Chleb na zakwasie.",
            ingredients="",
            allergens="",
            price=Decimal("24.00"),
        )
        RzutItem.objects.create(
            rzut=rzut,
            product=product,
            price=Decimal("26.00"),
            portion="bochenek ok. 750 g",
            pool=10,
        )
        rzut.status = OrderEdition.Status.PUBLISHED

        with self.assertRaises(ValidationError) as error:
            rzut.full_clean()

        messages = error.exception.message_dict["status"]
        self.assertIn(
            "Pozycja „Chleb wiejski”: uzupełnij skład Produktu.",
            messages,
        )
        self.assertIn(
            "Pozycja „Chleb wiejski”: uzupełnij alergeny Produktu.",
            messages,
        )

    def test_published_sales_windows_cannot_overlap(self):
        now = timezone.now()
        first = self.complete_rzut(
            title="Pierwszy Rzut",
            opens_at=now,
            closes_at=now + timedelta(hours=2),
        )
        self.add_complete_item(first, title="Chleb pierwszy")
        first.status = OrderEdition.Status.PUBLISHED
        first.full_clean()
        first.save()

        second = self.complete_rzut(
            title="Drugi Rzut",
            opens_at=now + timedelta(hours=1),
            closes_at=now + timedelta(hours=3),
        )
        self.add_complete_item(second, title="Chleb drugi")
        second.status = OrderEdition.Status.PUBLISHED

        with self.assertRaises(ValidationError) as error:
            second.full_clean()

        self.assertIn("opens_at", error.exception.message_dict)
        self.assertIn(
            "Okno sprzedaży nakłada się na opublikowany Rzut „Pierwszy Rzut”.",
            error.exception.message_dict["opens_at"],
        )

    def test_sales_must_end_before_pickup_and_pickup_needs_valid_hours(self):
        pickup_date = timezone.localdate() + timedelta(days=1)
        pickup_starts_at = time(10, 0)
        pickup_start = timezone.make_aware(
            datetime.combine(pickup_date, pickup_starts_at),
            timezone.get_current_timezone(),
        )
        rzut = self.complete_rzut(
            closes_at=pickup_start,
            pickup_date=pickup_date,
            pickup_starts_at=pickup_starts_at,
            pickup_ends_at=time(9, 0),
        )

        with self.assertRaises(ValidationError) as error:
            rzut.full_clean()

        self.assertIn("closes_at", error.exception.message_dict)
        self.assertIn("pickup_ends_at", error.exception.message_dict)
