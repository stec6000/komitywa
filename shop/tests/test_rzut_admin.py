from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from shop.models import OrderEdition, Product, RzutItem


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
