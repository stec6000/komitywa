from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from shop.models import (
    DiscountCode,
    OrderEdition,
    Product,
    Reservation,
    ReservationItem,
    RzutItem,
)
from shop.reservations import confirm_reservation


class RzutReuseAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser(
            email="reuse-admin@test.com",
            password="testpass123",
        )
        now = timezone.now()
        cls.rzut = OrderEdition.objects.create(
            title="Rzut sierpniowy",
            description="Opis sierpniowego Rzutu.",
            image="order-editions/rzut-sierpniowy.jpg",
            image_alt="Bochenki na stole",
            status=OrderEdition.Status.CLOSED,
            opens_at=now - timedelta(days=2),
            closes_at=now - timedelta(days=1),
            pickup_date=timezone.localdate(),
            pickup_place_name="Kuchenna Komitywa",
            pickup_address="ul. Bukowa 14, Białystok",
            pickup_starts_at=time(10, 0),
            pickup_ends_at=time(13, 0),
            pickup_instructions="Wejście od ogrodu.",
            payment_details="Płatność online.",
        )
        cls.product = Product.objects.create(
            title="Chleb wiejski",
            description="Chleb na zakwasie.",
            ingredients="mąka, woda, sól",
            allergens="gluten",
            price=Decimal("24.00"),
            default_portion="bochenek",
        )
        cls.item = RzutItem.objects.create(
            rzut=cls.rzut,
            product=cls.product,
            price=Decimal("26.00"),
            portion="bochenek 800 g",
            pool=12,
            per_customer_limit=2,
            production_note="Fermentacja od soboty.",
        )

    def setUp(self):
        self.client.force_login(self.admin_user)

    def create_reservation(self, *, discount_code=None):
        now = timezone.now()
        reservation = Reservation.objects.create(
            rzut=self.rzut,
            customer_name="Jan Kowalski",
            customer_email="jan@example.com",
            pickup_starts_at=time(10, 0),
            pickup_ends_at=time(11, 0),
            subtotal=Decimal("26.00"),
            discount_amount=Decimal("0.00"),
            discount_code=discount_code,
            discount_code_snapshot=discount_code.code if discount_code else "",
            total=Decimal("26.00"),
            data_processing_accepted_at=now,
            terms_accepted_at=now,
            terms_version="2026-08",
            expires_at=now + timedelta(minutes=15),
        )
        ReservationItem.objects.create(
            reservation=reservation,
            rzut_item=self.item,
            quantity=1,
            unit_price=self.item.price,
        )
        return reservation

    def test_copy_action_creates_hidden_draft_without_transactional_data(self):
        discount_code = DiscountCode.objects.create(
            code="SIERPIEN",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("5.00"),
            rzut=self.rzut,
        )
        reservation = self.create_reservation(discount_code=discount_code)
        confirm_reservation(
            reservation_id=reservation.pk,
            p24_order_id=987654,
        )
        RzutItem.objects.filter(pk=self.item.pk).update(allocated_quantity=1)

        response = self.client.post(
            reverse("admin:shop_orderedition_changelist"),
            {
                "action": "copy_as_draft",
                "_selected_action": [self.rzut.pk],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        copy = OrderEdition.objects.exclude(pk=self.rzut.pk).get()
        self.assertEqual(copy.status, OrderEdition.Status.DRAFT)
        self.assertIsNone(copy.opens_at)
        self.assertIsNone(copy.closes_at)
        self.assertIsNone(copy.pickup_date)
        self.assertIsNone(copy.pickup_starts_at)
        self.assertIsNone(copy.pickup_ends_at)
        self.assertEqual(copy.description, self.rzut.description)
        self.assertEqual(copy.image.name, self.rzut.image.name)
        self.assertEqual(copy.image_alt, self.rzut.image_alt)
        self.assertEqual(copy.pickup_place_name, self.rzut.pickup_place_name)
        self.assertEqual(copy.pickup_address, self.rzut.pickup_address)
        self.assertEqual(copy.pickup_instructions, self.rzut.pickup_instructions)
        copied_item = copy.items.get()
        self.assertEqual(copied_item.product, self.product)
        self.assertEqual(copied_item.pool, self.item.pool)
        self.assertEqual(copied_item.allocated_quantity, 0)
        self.assertFalse(copy.reservations.exists())
        self.assertFalse(copy.rzut_orders.exists())
        self.assertFalse(copy.discount_codes.exists())
        self.assertNotContains(self.client.get(reverse("orders")), copy.title)

    def test_deleting_used_rzut_archives_it_without_losing_history(self):
        reservation = self.create_reservation()

        response = self.client.post(
            reverse("admin:shop_orderedition_delete", args=[self.rzut.pk]),
            {"post": "yes"},
        )

        self.assertRedirects(
            response,
            reverse("admin:shop_orderedition_changelist"),
        )
        self.rzut.refresh_from_db()
        self.assertEqual(self.rzut.status, OrderEdition.Status.CLOSED)
        self.assertFalse(self.rzut.show_in_archive)
        self.assertTrue(Reservation.objects.filter(pk=reservation.pk).exists())
        self.assertTrue(
            self.rzut.events.filter(
                kind="archive_visibility_changed",
                context={"before": True, "after": False},
            ).exists()
        )
        order, created = confirm_reservation(
            reservation_id=reservation.pk,
            p24_order_id=123456,
        )
        self.assertTrue(created)
        self.assertEqual(order.payment_status, "paid")
        self.assertNotContains(self.client.get(reverse("orders")), self.rzut.title)

    def test_deleting_unrelated_draft_physically_removes_it(self):
        draft = OrderEdition.objects.create(title="Pusty szkic")

        response = self.client.post(
            reverse("admin:shop_orderedition_delete", args=[draft.pk]),
            {"post": "yes"},
        )

        self.assertRedirects(
            response,
            reverse("admin:shop_orderedition_changelist"),
        )
        self.assertFalse(OrderEdition.objects.filter(pk=draft.pk).exists())

    def test_deleting_used_product_and_code_archives_them(self):
        discount_code = DiscountCode.objects.create(
            code="HISTORIA",
            discount_type=DiscountCode.Type.PERCENTAGE,
            value=Decimal("10.00"),
            rzut=self.rzut,
        )
        reservation = self.create_reservation(discount_code=discount_code)

        product_response = self.client.post(
            reverse("admin:shop_product_delete", args=[self.product.pk]),
            {"post": "yes"},
        )
        code_response = self.client.post(
            reverse("admin:shop_discountcode_delete", args=[discount_code.pk]),
            {"post": "yes"},
        )

        self.assertRedirects(
            product_response,
            reverse("admin:shop_product_changelist"),
        )
        self.assertRedirects(
            code_response,
            reverse("admin:shop_discountcode_changelist"),
        )
        self.product.refresh_from_db()
        discount_code.refresh_from_db()
        self.assertTrue(self.product.is_archived)
        self.assertFalse(self.product.is_available_in_shop)
        self.item.refresh_from_db()
        self.assertFalse(self.item.is_active)
        self.assertFalse(discount_code.is_active)
        order, created = confirm_reservation(
            reservation_id=reservation.pk,
            p24_order_id=234567,
        )
        self.assertTrue(created)
        self.assertEqual(order.discount_code, discount_code)

        OrderEdition.objects.filter(pk=self.rzut.pk).update(
            status=OrderEdition.Status.PUBLISHED,
            opens_at=timezone.now() - timedelta(hours=1),
            closes_at=timezone.now() + timedelta(hours=1),
        )
        self.assertNotContains(
            self.client.get(reverse("orders")),
            self.product.title,
        )
        self.assertEqual(
            self.client.post(
                reverse("shop:rzut_cart_add", args=[self.item.pk])
            ).status_code,
            404,
        )
