from concurrent.futures import ThreadPoolExecutor
from datetime import time, timedelta
from decimal import Decimal
from threading import Event
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import close_old_connections
from django.test import Client, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from core import legal
from shop.models import OrderEdition, Product, RzutItem
from shop.reservations import (
    ReservationCheckoutData,
    ReservationError,
    ReservationLineRequest,
    create_reservation,
)


class TestConcurrentPoolChange(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            email="pool-admin@test.com",
            password="testpass123",
        )
        now = timezone.now()
        self.rzut = OrderEdition.objects.create(
            title="Rzut współbieżny",
            description="Oferta z bezpieczną Pulą.",
            status=OrderEdition.Status.PUBLISHED,
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(hours=2),
            pickup_date=timezone.localdate() + timedelta(days=1),
            pickup_place_name="Kuchenna Komitywa",
            pickup_address="ul. Bukowa 14, Białystok",
            pickup_starts_at=time(10, 0),
            pickup_ends_at=time(12, 0),
            pickup_instructions="Wejście od ogrodu.",
        )
        self.product = Product.objects.create(
            title="Chleb współbieżny",
            description="Chleb na zakwasie.",
            ingredients="mąka, woda, sól",
            allergens="gluten",
            price=Decimal("25.00"),
            default_portion="bochenek",
        )
        self.item = RzutItem.objects.create(
            rzut=self.rzut,
            product=self.product,
            price=Decimal("25.00"),
            portion="bochenek",
            pool=10,
        )
        RzutItem.objects.filter(pk=self.item.pk).update(allocated_quantity=4)

    def admin_payload(self):
        rzut = self.rzut
        return {
            "title": rzut.title,
            "slug": rzut.slug,
            "status": rzut.status,
            "description": rzut.description,
            "opens_at_0": timezone.localtime(rzut.opens_at).date().isoformat(),
            "opens_at_1": timezone.localtime(rzut.opens_at).time().strftime(
                "%H:%M:%S"
            ),
            "closes_at_0": timezone.localtime(rzut.closes_at).date().isoformat(),
            "closes_at_1": timezone.localtime(rzut.closes_at).time().strftime(
                "%H:%M:%S"
            ),
            "pickup_date": rzut.pickup_date.isoformat(),
            "pickup_place_name": rzut.pickup_place_name,
            "pickup_address": rzut.pickup_address,
            "pickup_starts_at": rzut.pickup_starts_at.strftime("%H:%M:%S"),
            "pickup_ends_at": rzut.pickup_ends_at.strftime("%H:%M:%S"),
            "pickup_instructions": rzut.pickup_instructions,
            "payment_details": rzut.payment_details,
            "show_upcoming_menu": "on",
            "show_in_archive": "on",
            "items-TOTAL_FORMS": "1",
            "items-INITIAL_FORMS": "1",
            "items-MIN_NUM_FORMS": "0",
            "items-MAX_NUM_FORMS": "1000",
            "items-0-id": self.item.pk,
            "items-0-product": self.product.pk,
            "items-0-price": "25.00",
            "items-0-portion": "bochenek",
            "items-0-pool": "5",
            "items-0-per_customer_limit": "",
            "items-0-sort_order": "0",
            "items-0-is_active": "on",
            "items-0-production_note": "",
            "_save": "Zapisz",
        }

    def checkout(self):
        return ReservationCheckoutData(
            name="Jan Kowalski",
            email="jan@example.com",
            phone="",
            notes="",
            pickup_starts_at=time(10, 0),
            pickup_ends_at=time(11, 0),
            terms_version=legal.CURRENT_TERMS.identifier,
        )

    def test_pool_reduction_serializes_with_new_reservation(self):
        validation_reached = Event()
        reservation_finished = Event()
        original_clean = RzutItem.clean

        def signal_during_admin_validation(item):
            original_clean(item)
            if item.pk == self.item.pk:
                validation_reached.set()
                reservation_finished.wait(timeout=0.5)

        client = Client()
        client.force_login(self.admin_user)

        def reduce_pool():
            close_old_connections()
            try:
                return client.post(
                    reverse(
                        "admin:shop_orderedition_change",
                        args=[self.rzut.pk],
                    ),
                    self.admin_payload(),
                )
            finally:
                close_old_connections()

        with patch.object(RzutItem, "clean", signal_during_admin_validation):
            with ThreadPoolExecutor(max_workers=1) as executor:
                admin_future = executor.submit(reduce_pool)
                self.assertTrue(validation_reached.wait(timeout=2))
                try:
                    create_reservation(
                        rzut_id=self.rzut.pk,
                        lines=[
                            ReservationLineRequest(
                                self.item.pk,
                                2,
                                self.item.price,
                            )
                        ],
                        checkout=self.checkout(),
                    )
                except ReservationError:
                    reservation_result = "rejected"
                else:
                    reservation_result = "reserved"
                finally:
                    reservation_finished.set()
                admin_response = admin_future.result(timeout=2)

        self.assertEqual(admin_response.status_code, 302)
        self.assertEqual(reservation_result, "rejected")
        self.item.refresh_from_db()
        self.assertEqual(self.item.pool, 5)
        self.assertEqual(self.item.allocated_quantity, 4)
