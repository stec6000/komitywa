from datetime import time, timedelta
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from shop.models import OrderEdition, Product, RzutItem
from shop.reservations import (
    ReservationCheckoutData,
    ReservationCustomerLimitExceeded,
    ReservationLineRequest,
    create_reservation,
    fail_reservation,
    ReservationError,
    ReservationUnavailable,
)


class ReservationTestCase(TestCase):
    def create_open_rzut(self):
        now = timezone.now()
        return OrderEdition.objects.create(
            title="Rzut niedzielny",
            description="Niedzielne wypieki.",
            status=OrderEdition.Status.PUBLISHED,
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(hours=1),
            pickup_date=timezone.localdate() + timedelta(days=1),
            pickup_place_name="Kuchenna Komitywa",
            pickup_address="ul. Bukowa 14, Białystok",
            pickup_starts_at=time(10, 0),
            pickup_ends_at=time(13, 0),
            pickup_instructions="Wejście od ogrodu.",
        )

    def create_item(self, rzut, title="Chleb wiejski", **overrides):
        product = Product.objects.create(
            title=title,
            description="Chleb na zakwasie.",
            ingredients="mąka, woda, sól",
            allergens="gluten",
            price=Decimal("24.00"),
            default_portion="bochenek ok. 750 g",
            is_available_in_shop=False,
        )
        values = {
            "rzut": rzut,
            "product": product,
            "price": Decimal("26.00"),
            "portion": "bochenek ok. 750 g",
            "pool": 10,
        }
        values.update(overrides)
        return RzutItem.objects.create(**values)

    def checkout_data(self, **overrides):
        values = {
            "name": "Jan Kowalski",
            "email": "  JAN@Example.COM ",
            "phone": "+48 500 600 700",
            "notes": "Odbierze siostra.",
            "pickup_starts_at": time(10, 0),
            "pickup_ends_at": time(11, 0),
        }
        values.update(overrides)
        return ReservationCheckoutData(**values)


class TestCreateReservation(ReservationTestCase):
    def test_reserves_quantity_and_checkout_snapshot_for_15_minutes(self):
        now = timezone.now()
        item = self.create_item(self.create_open_rzut())

        reservation = create_reservation(
            rzut_id=item.rzut_id,
            lines=[
                ReservationLineRequest(
                    item_id=item.pk,
                    quantity=2,
                    expected_price=Decimal("26.00"),
                )
            ],
            checkout=self.checkout_data(),
            now=now,
        )

        item.refresh_from_db()
        line = reservation.items.get()
        self.assertEqual(reservation.status, "active")
        self.assertEqual(reservation.customer_email, "jan@example.com")
        self.assertEqual(reservation.customer_name, "Jan Kowalski")
        self.assertEqual(reservation.customer_phone, "+48 500 600 700")
        self.assertEqual(reservation.customer_notes, "Odbierze siostra.")
        self.assertEqual(reservation.total, Decimal("52.00"))
        self.assertEqual(reservation.expires_at, now + timedelta(minutes=15))
        self.assertEqual(reservation.data_processing_accepted_at, now)
        self.assertEqual(reservation.terms_accepted_at, now)
        self.assertEqual(item.allocated_quantity, 2)
        self.assertEqual(line.rzut_item, item)
        self.assertEqual(line.quantity, 2)
        self.assertEqual(line.unit_price, Decimal("26.00"))

    def test_unavailable_second_item_rolls_back_every_quantity(self):
        rzut = self.create_open_rzut()
        bread = self.create_item(rzut, "Chleb")
        bun = self.create_item(rzut, "Bułka", pool=1, allocated_quantity=1)

        with self.assertRaisesMessage(
            ReservationUnavailable,
            "Brakuje Dostępności",
        ):
            create_reservation(
                rzut_id=rzut.pk,
                lines=[
                    ReservationLineRequest(
                        item_id=bread.pk,
                        quantity=2,
                        expected_price=bread.price,
                    ),
                    ReservationLineRequest(
                        item_id=bun.pk,
                        quantity=1,
                        expected_price=bun.price,
                    ),
                ],
                checkout=self.checkout_data(),
            )

        bread.refresh_from_db()
        bun.refresh_from_db()
        self.assertEqual(bread.allocated_quantity, 0)
        self.assertEqual(bun.allocated_quantity, 1)
        self.assertFalse(bread.reservation_items.exists())

    def test_customer_limit_uses_normalized_email_across_reservations(self):
        item = self.create_item(
            self.create_open_rzut(),
            per_customer_limit=2,
        )
        create_reservation(
            rzut_id=item.rzut_id,
            lines=[ReservationLineRequest(item.pk, 1, item.price)],
            checkout=self.checkout_data(email="JAN@example.com"),
        )

        with self.assertRaisesMessage(
            ReservationCustomerLimitExceeded,
            "Limit Klienta",
        ):
            create_reservation(
                rzut_id=item.rzut_id,
                lines=[ReservationLineRequest(item.pk, 2, item.price)],
                checkout=self.checkout_data(email=" jan@EXAMPLE.com "),
            )

        item.refresh_from_db()
        self.assertEqual(item.allocated_quantity, 1)

    def test_each_reservation_gets_a_unique_p24_session_id(self):
        item = self.create_item(self.create_open_rzut())

        first = create_reservation(
            rzut_id=item.rzut_id,
            lines=[ReservationLineRequest(item.pk, 1, item.price)],
            checkout=self.checkout_data(email="one@example.com"),
        )
        second = create_reservation(
            rzut_id=item.rzut_id,
            lines=[ReservationLineRequest(item.pk, 1, item.price)],
            checkout=self.checkout_data(email="two@example.com"),
        )

        self.assertNotEqual(first.p24_session_id, second.p24_session_id)
        self.assertTrue(first.p24_session_id.startswith("rzut-"))

    def test_rejects_pickup_interval_outside_rzut_slots(self):
        item = self.create_item(self.create_open_rzut())

        with self.assertRaisesMessage(
            ReservationUnavailable,
            "Przedział Odbioru",
        ):
            create_reservation(
                rzut_id=item.rzut_id,
                lines=[ReservationLineRequest(item.pk, 1, item.price)],
                checkout=self.checkout_data(
                    pickup_starts_at=time(9, 0),
                    pickup_ends_at=time(10, 0),
                ),
            )

        item.refresh_from_db()
        self.assertEqual(item.allocated_quantity, 0)

    def test_paused_and_closed_rzut_reject_new_reservations(self):
        for status in [OrderEdition.Status.PAUSED, OrderEdition.Status.CLOSED]:
            with self.subTest(status=status):
                rzut = self.create_open_rzut()
                item = self.create_item(rzut, title=f"Chleb {status}")
                rzut.status = status
                rzut.save(update_fields=["status"])

                with self.assertRaisesMessage(
                    ReservationUnavailable,
                    "nie przyjmuje już nowych Rezerwacji",
                ):
                    create_reservation(
                        rzut_id=rzut.pk,
                        lines=[
                            ReservationLineRequest(item.pk, 1, item.price)
                        ],
                        checkout=self.checkout_data(),
                    )

                item.refresh_from_db()
                self.assertEqual(item.allocated_quantity, 0)


class TestFailReservation(ReservationTestCase):
    def test_failure_releases_every_quantity_once(self):
        rzut = self.create_open_rzut()
        bread = self.create_item(rzut, "Chleb")
        bun = self.create_item(rzut, "Bułka")
        reservation = create_reservation(
            rzut_id=rzut.pk,
            lines=[
                ReservationLineRequest(bread.pk, 2, bread.price),
                ReservationLineRequest(bun.pk, 3, bun.price),
            ],
            checkout=self.checkout_data(),
        )

        fail_reservation(reservation)
        fail_reservation(reservation)

        reservation.refresh_from_db()
        bread.refresh_from_db()
        bun.refresh_from_db()
        self.assertEqual(reservation.status, "failed")
        self.assertEqual(bread.allocated_quantity, 0)
        self.assertEqual(bun.allocated_quantity, 0)


class TestConcurrentReservation(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        helper = ReservationTestCase()
        self.rzut = helper.create_open_rzut()
        self.item = helper.create_item(self.rzut, pool=1)
        self.checkout = helper.checkout_data()

    def test_only_one_attempt_can_reserve_the_last_item(self):
        barrier = Barrier(2)

        def attempt(email):
            close_old_connections()
            barrier.wait()
            try:
                create_reservation(
                    rzut_id=self.rzut.pk,
                    lines=[
                        ReservationLineRequest(
                            self.item.pk,
                            1,
                            self.item.price,
                        )
                    ],
                    checkout=ReservationCheckoutData(
                        name="Jan Kowalski",
                        email=email,
                        phone="",
                        notes="",
                        pickup_starts_at=time(10, 0),
                        pickup_ends_at=time(11, 0),
                    ),
                )
                return "reserved"
            except ReservationError:
                return "rejected"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(
                attempt,
                ["one@example.com", "two@example.com"],
            ))

        self.item.refresh_from_db()
        self.assertEqual(results.count("reserved"), 1)
        self.assertEqual(results.count("rejected"), 1)
        self.assertEqual(self.item.allocated_quantity, 1)

    def test_concurrent_attempts_cannot_exceed_customer_limit(self):
        self.item.pool = 2
        self.item.per_customer_limit = 1
        self.item.save(update_fields=["pool", "per_customer_limit"])
        barrier = Barrier(2)

        def attempt():
            close_old_connections()
            barrier.wait()
            try:
                create_reservation(
                    rzut_id=self.rzut.pk,
                    lines=[
                        ReservationLineRequest(
                            self.item.pk,
                            1,
                            self.item.price,
                        )
                    ],
                    checkout=ReservationCheckoutData(
                        name="Jan Kowalski",
                        email=" JAN@Example.COM ",
                        phone="",
                        notes="",
                        pickup_starts_at=time(10, 0),
                        pickup_ends_at=time(11, 0),
                    ),
                )
                return "reserved"
            except ReservationError:
                return "rejected"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: attempt(), range(2)))

        self.item.refresh_from_db()
        self.assertEqual(results.count("reserved"), 1)
        self.assertEqual(results.count("rejected"), 1)
        self.assertEqual(self.item.allocated_quantity, 1)
