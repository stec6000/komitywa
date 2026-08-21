from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from shop.models import (
    OrderEdition,
    Product,
    Reservation,
    ReservationItem,
    RzutEvent,
    RzutItem,
)
from shop.reservations import confirm_reservation


class TestRzutPublicationAdmin(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser(
            email="admin-rzut@test.com",
            password="testpass123",
        )
        cls.rzut = OrderEdition.objects.create(
            title="Rzut niedzielny",
            description="Niedzielne wypieki.",
        )
        cls.product = Product.objects.create(
            title="Chleb wiejski",
            description="Chleb na zakwasie.",
            ingredients="mąka, woda, sól",
            allergens="gluten",
            price=Decimal("24.00"),
            default_portion="bochenek ok. 750 g",
        )
        cls.item = RzutItem.objects.create(
            rzut=cls.rzut,
            product=cls.product,
            price=Decimal("26.00"),
            portion="bochenek ok. 750 g",
            pool=10,
        )

    def setUp(self):
        self.client.force_login(self.admin_user)

    def test_admin_can_publish_complete_rzut(self):
        opens_at = timezone.localtime().replace(second=0, microsecond=0)
        closes_at = opens_at + timedelta(hours=1)
        pickup_date = timezone.localdate() + timedelta(days=1)

        response = self.client.post(
            reverse("admin:shop_orderedition_change", args=[self.rzut.pk]),
            {
                "title": self.rzut.title,
                "slug": self.rzut.slug,
                "status": OrderEdition.Status.PUBLISHED,
                "description": self.rzut.description,
                "opens_at_0": opens_at.date().isoformat(),
                "opens_at_1": opens_at.time().strftime("%H:%M:%S"),
                "closes_at_0": closes_at.date().isoformat(),
                "closes_at_1": closes_at.time().strftime("%H:%M:%S"),
                "pickup_date": pickup_date.isoformat(),
                "pickup_place_name": "Kuchenna Komitywa",
                "pickup_address": "ul. Bukowa 14, Białystok",
                "pickup_starts_at": time(10, 0).strftime("%H:%M:%S"),
                "pickup_ends_at": time(13, 0).strftime("%H:%M:%S"),
                "pickup_instructions": "Wejście od ogrodu.",
                "payment_details": "Płatność online.",
                "show_upcoming_menu": "on",
                "show_in_archive": "on",
                "items-TOTAL_FORMS": "1",
                "items-INITIAL_FORMS": "1",
                "items-MIN_NUM_FORMS": "0",
                "items-MAX_NUM_FORMS": "1000",
                "items-0-id": self.item.pk,
                "items-0-product": self.product.pk,
                "items-0-price": "26.00",
                "items-0-portion": "bochenek ok. 750 g",
                "items-0-pool": "10",
                "items-0-per_customer_limit": "",
                "items-0-sort_order": "0",
                "items-0-is_active": "on",
                "items-0-production_note": "",
                "_save": "Zapisz",
            },
        )

        self.assertRedirects(
            response,
            reverse("admin:shop_orderedition_changelist"),
        )
        self.rzut.refresh_from_db()
        self.assertEqual(self.rzut.status, OrderEdition.Status.PUBLISHED)
        self.assertEqual(self.rzut.pickup_place_name, "Kuchenna Komitywa")

    def test_admin_shows_concrete_missing_fields_before_publication(self):
        response = self.client.post(
            reverse("admin:shop_orderedition_change", args=[self.rzut.pk]),
            {
                "title": self.rzut.title,
                "slug": self.rzut.slug,
                "status": OrderEdition.Status.PUBLISHED,
                "description": self.rzut.description,
                "payment_details": "Płatność online.",
                "show_upcoming_menu": "on",
                "show_in_archive": "on",
                "items-TOTAL_FORMS": "1",
                "items-INITIAL_FORMS": "1",
                "items-MIN_NUM_FORMS": "0",
                "items-MAX_NUM_FORMS": "1000",
                "items-0-id": self.item.pk,
                "items-0-product": self.product.pk,
                "items-0-price": "26.00",
                "items-0-portion": "bochenek ok. 750 g",
                "items-0-pool": "10",
                "items-0-per_customer_limit": "",
                "items-0-sort_order": "0",
                "items-0-is_active": "on",
                "items-0-production_note": "",
                "_save": "Zapisz",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ustaw początek sprzedaży.")
        self.assertContains(response, "Ustaw dzień odbioru.")
        self.assertContains(response, "Uzupełnij adres odbioru.")
        self.rzut.refresh_from_db()
        self.assertEqual(self.rzut.status, OrderEdition.Status.DRAFT)

    def test_admin_blocks_publishing_while_deactivating_only_item(self):
        opens_at = timezone.localtime().replace(second=0, microsecond=0)
        closes_at = opens_at + timedelta(hours=1)
        pickup_date = timezone.localdate() + timedelta(days=1)

        response = self.client.post(
            reverse("admin:shop_orderedition_change", args=[self.rzut.pk]),
            {
                "title": self.rzut.title,
                "slug": self.rzut.slug,
                "status": OrderEdition.Status.PUBLISHED,
                "description": self.rzut.description,
                "opens_at_0": opens_at.date().isoformat(),
                "opens_at_1": opens_at.time().strftime("%H:%M:%S"),
                "closes_at_0": closes_at.date().isoformat(),
                "closes_at_1": closes_at.time().strftime("%H:%M:%S"),
                "pickup_date": pickup_date.isoformat(),
                "pickup_place_name": "Kuchenna Komitywa",
                "pickup_address": "ul. Bukowa 14, Białystok",
                "pickup_starts_at": time(10, 0).strftime("%H:%M:%S"),
                "pickup_ends_at": time(13, 0).strftime("%H:%M:%S"),
                "pickup_instructions": "Wejście od ogrodu.",
                "payment_details": "Płatność online.",
                "show_upcoming_menu": "on",
                "show_in_archive": "on",
                "items-TOTAL_FORMS": "1",
                "items-INITIAL_FORMS": "1",
                "items-MIN_NUM_FORMS": "0",
                "items-MAX_NUM_FORMS": "1000",
                "items-0-id": self.item.pk,
                "items-0-product": self.product.pk,
                "items-0-price": "26.00",
                "items-0-portion": "bochenek ok. 750 g",
                "items-0-pool": "10",
                "items-0-per_customer_limit": "",
                "items-0-sort_order": "0",
                "items-0-production_note": "",
                "_save": "Zapisz",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Dodaj co najmniej jedną aktywną Pozycję Rzutu.",
        )
        self.rzut.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(self.rzut.status, OrderEdition.Status.DRAFT)
        self.assertTrue(self.item.is_active)

    def test_admin_rejects_pool_smaller_than_allocated_quantity(self):
        RzutItem.objects.filter(pk=self.item.pk).update(allocated_quantity=6)

        response = self.client.post(
            reverse("admin:shop_orderedition_change", args=[self.rzut.pk]),
            {
                "title": self.rzut.title,
                "slug": self.rzut.slug,
                "status": OrderEdition.Status.DRAFT,
                "description": self.rzut.description,
                "payment_details": "Płatność online.",
                "show_upcoming_menu": "on",
                "show_in_archive": "on",
                "items-TOTAL_FORMS": "1",
                "items-INITIAL_FORMS": "1",
                "items-MIN_NUM_FORMS": "0",
                "items-MAX_NUM_FORMS": "1000",
                "items-0-id": self.item.pk,
                "items-0-product": self.product.pk,
                "items-0-price": "26.00",
                "items-0-portion": "bochenek ok. 750 g",
                "items-0-pool": "5",
                "items-0-per_customer_limit": "",
                "items-0-sort_order": "0",
                "items-0-is_active": "on",
                "items-0-production_note": "",
                "_save": "Zapisz",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Pula nie może być mniejsza niż 6 już przydzielonych sztuk.",
        )
        self.item.refresh_from_db()
        self.assertEqual(self.item.pool, 10)


class TestLiveRzutAdmin(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser(
            email="live-admin@test.com",
            password="testpass123",
        )
        now = timezone.now()
        cls.rzut = OrderEdition.objects.create(
            title="Rzut na żywo",
            description="Oferta na dziś.",
            status=OrderEdition.Status.PUBLISHED,
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(hours=2),
            pickup_date=timezone.localdate() + timedelta(days=1),
            pickup_place_name="Kuchenna Komitywa",
            pickup_address="ul. Bukowa 14, Białystok",
            pickup_starts_at=time(10, 0),
            pickup_ends_at=time(13, 0),
            pickup_instructions="Wejście od ogrodu.",
        )
        cls.product = Product.objects.create(
            title="Chleb żytni",
            description="Chleb na zakwasie.",
            ingredients="mąka, woda, sól",
            allergens="gluten",
            price=Decimal("25.00"),
            default_portion="bochenek",
        )
        cls.item = RzutItem.objects.create(
            rzut=cls.rzut,
            product=cls.product,
            price=Decimal("25.00"),
            portion="bochenek",
            pool=10,
        )

    def setUp(self):
        self.client.force_login(self.admin_user)

    def change_payload(self, *, status=None, pool=10):
        rzut = self.rzut
        return {
            "title": rzut.title,
            "slug": rzut.slug,
            "status": status or rzut.status,
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
            "items-0-pool": str(pool),
            "items-0-per_customer_limit": "",
            "items-0-sort_order": "0",
            "items-0-is_active": "on",
            "items-0-production_note": "",
            "_save": "Zapisz",
        }

    def test_status_change_is_audited_with_admin_identity(self):
        response = self.client.post(
            reverse("admin:shop_orderedition_change", args=[self.rzut.pk]),
            self.change_payload(status=OrderEdition.Status.PAUSED),
        )

        self.assertRedirects(
            response,
            reverse("admin:shop_orderedition_changelist"),
        )
        self.rzut.refresh_from_db()
        self.assertEqual(self.rzut.status, OrderEdition.Status.PAUSED)
        self.assertNotContains(
            self.client.get(reverse("orders")),
            self.rzut.title,
        )
        self.assertEqual(
            self.client.post(
                reverse("shop:rzut_cart_add", args=[self.item.pk])
            ).status_code,
            404,
        )
        event = RzutEvent.objects.get(rzut=self.rzut)
        self.assertEqual(event.kind, RzutEvent.Kind.STATUS_CHANGED)
        self.assertEqual(event.actor, self.admin_user)
        self.assertEqual(event.context["before"], OrderEdition.Status.PUBLISHED)
        self.assertEqual(event.context["after"], OrderEdition.Status.PAUSED)

    def test_admin_can_resume_and_close_rzut_early(self):
        OrderEdition.objects.filter(pk=self.rzut.pk).update(
            status=OrderEdition.Status.PAUSED
        )
        self.rzut.status = OrderEdition.Status.PAUSED

        resume_response = self.client.post(
            reverse("admin:shop_orderedition_change", args=[self.rzut.pk]),
            self.change_payload(status=OrderEdition.Status.PUBLISHED),
        )
        self.assertRedirects(
            resume_response,
            reverse("admin:shop_orderedition_changelist"),
        )
        self.rzut.refresh_from_db()
        self.assertEqual(self.rzut.status, OrderEdition.Status.PUBLISHED)
        self.assertContains(self.client.get(reverse("orders")), self.rzut.title)

        close_response = self.client.post(
            reverse("admin:shop_orderedition_change", args=[self.rzut.pk]),
            self.change_payload(status=OrderEdition.Status.CLOSED),
        )
        self.assertRedirects(
            close_response,
            reverse("admin:shop_orderedition_changelist"),
        )
        self.rzut.refresh_from_db()
        self.assertEqual(self.rzut.status, OrderEdition.Status.CLOSED)
        self.assertContains(self.client.get(reverse("orders")), self.rzut.title)
        self.assertEqual(
            self.client.post(
                reverse("shop:rzut_cart_add", args=[self.item.pk])
            ).status_code,
            404,
        )
        self.assertEqual(
            list(
                self.rzut.events.values_list(
                    "context__before", "context__after"
                ).order_by("pk")
            ),
            [
                (OrderEdition.Status.PAUSED, OrderEdition.Status.PUBLISHED),
                (OrderEdition.Status.PUBLISHED, OrderEdition.Status.CLOSED),
            ],
        )

    def test_hiding_closed_rzut_is_audited_and_removes_public_archive(self):
        payload = self.change_payload(status=OrderEdition.Status.CLOSED)
        payload.pop("show_in_archive")

        response = self.client.post(
            reverse("admin:shop_orderedition_change", args=[self.rzut.pk]),
            payload,
        )

        self.assertRedirects(
            response,
            reverse("admin:shop_orderedition_changelist"),
        )
        self.rzut.refresh_from_db()
        self.assertFalse(self.rzut.show_in_archive)
        event = self.rzut.events.get(
            kind=RzutEvent.Kind.ARCHIVE_VISIBILITY_CHANGED
        )
        self.assertEqual(event.context, {"before": True, "after": False})
        self.assertTrue(self.rzut.items.filter(pk=self.item.pk).exists())
        self.assertNotContains(
            self.client.get(reverse("orders")),
            self.rzut.title,
        )

    def test_pool_change_is_audited_and_reopens_sold_out_item(self):
        RzutItem.objects.filter(pk=self.item.pk).update(allocated_quantity=10)
        self.assertEqual(
            self.client.post(
                reverse("shop:rzut_cart_add", args=[self.item.pk])
            ).status_code,
            404,
        )

        response = self.client.post(
            reverse("admin:shop_orderedition_change", args=[self.rzut.pk]),
            self.change_payload(pool=14),
        )

        self.assertRedirects(
            response,
            reverse("admin:shop_orderedition_changelist"),
        )
        self.item.refresh_from_db()
        self.assertEqual(self.item.available_quantity, 4)
        self.assertRedirects(
            self.client.post(
                reverse("shop:rzut_cart_add", args=[self.item.pk])
            ),
            reverse("shop:rzut_cart"),
        )
        event = RzutEvent.objects.get(rzut=self.rzut)
        self.assertEqual(event.kind, RzutEvent.Kind.POOL_CHANGED)
        self.assertEqual(event.context["rzut_item_id"], self.item.pk)
        self.assertEqual(event.context["before"], 10)
        self.assertEqual(event.context["after"], 14)

    def test_admin_adds_item_to_running_rzut_and_public_menu_shows_it(self):
        rolls = Product.objects.create(
            title="Bułki maślane",
            description="Miękkie bułki.",
            ingredients="mąka, masło, mleko",
            allergens="gluten, mleko",
            price=Decimal("12.00"),
            default_portion="4 sztuki",
        )
        payload = self.change_payload()
        payload.update({
            "items-TOTAL_FORMS": "2",
            "items-1-id": "",
            "items-1-product": rolls.pk,
            "items-1-price": "12.00",
            "items-1-portion": "4 sztuki",
            "items-1-pool": "8",
            "items-1-per_customer_limit": "",
            "items-1-sort_order": "1",
            "items-1-is_active": "on",
            "items-1-production_note": "",
        })

        response = self.client.post(
            reverse("admin:shop_orderedition_change", args=[self.rzut.pk]),
            payload,
        )

        self.assertRedirects(
            response,
            reverse("admin:shop_orderedition_changelist"),
        )
        self.assertTrue(self.rzut.items.filter(product=rolls).exists())
        public_response = self.client.get(reverse("orders"))
        self.assertContains(public_response, rolls.title)

    def test_deleting_used_item_in_admin_disables_it_and_preserves_history(self):
        now = timezone.now()
        reservation = Reservation.objects.create(
            rzut=self.rzut,
            customer_name="Anna Nowak",
            customer_email="anna@example.com",
            pickup_starts_at=time(10, 0),
            pickup_ends_at=time(11, 0),
            subtotal=self.item.price,
            total=self.item.price,
            data_processing_accepted_at=now,
            terms_accepted_at=now,
            terms_version="2026-08",
            expires_at=now + timedelta(minutes=15),
        )
        reservation_item = ReservationItem.objects.create(
            reservation=reservation,
            rzut_item=self.item,
            quantity=1,
            unit_price=self.item.price,
        )
        rolls = Product.objects.create(
            title="Bułki zapasowe",
            description="Miękkie bułki.",
            ingredients="mąka, masło",
            allergens="gluten, mleko",
            price=Decimal("12.00"),
            default_portion="4 sztuki",
        )
        replacement = RzutItem.objects.create(
            rzut=self.rzut,
            product=rolls,
            price=rolls.price,
            portion=rolls.default_portion,
            pool=8,
            sort_order=1,
        )
        payload = self.change_payload()
        payload.update({
            "items-TOTAL_FORMS": "2",
            "items-INITIAL_FORMS": "2",
            "items-0-DELETE": "on",
            "items-1-id": replacement.pk,
            "items-1-product": rolls.pk,
            "items-1-price": "12.00",
            "items-1-portion": "4 sztuki",
            "items-1-pool": "8",
            "items-1-per_customer_limit": "",
            "items-1-sort_order": "1",
            "items-1-is_active": "on",
            "items-1-production_note": "",
        })

        response = self.client.post(
            reverse("admin:shop_orderedition_change", args=[self.rzut.pk]),
            payload,
        )

        self.assertRedirects(
            response,
            reverse("admin:shop_orderedition_changelist"),
        )
        self.item.refresh_from_db()
        self.assertFalse(self.item.is_active)
        self.assertTrue(
            ReservationItem.objects.filter(pk=reservation_item.pk).exists()
        )
        order, created = confirm_reservation(
            reservation_id=reservation.pk,
            p24_order_id=987654,
        )
        self.assertTrue(created)
        self.assertEqual(order.payment_status, "paid")
        public_response = self.client.get(reverse("orders"))
        self.assertNotContains(public_response, self.product.title)
