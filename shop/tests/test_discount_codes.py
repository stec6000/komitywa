from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from datetime import time, timedelta
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from shop.models import (
    DiscountCode,
    OrderEdition,
    Product,
    Reservation,
    RzutItem,
)
from shop.reservations import (
    OrderConfirmed,
    ReservationCheckoutData,
    ReservationLineRequest,
    ReservationUnavailable,
    confirm_reservation,
    create_reservation,
    expire_due_reservations,
    fail_reservation,
    start_checkout,
)


class TestDiscountCodeAdmin(TestCase):
    def setUp(self):
        admin_user = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="testpass123",
        )
        self.client.force_login(admin_user)

    def test_admin_creates_normalized_global_percentage_code(self):
        response = self.client.post(
            reverse("admin:shop_discountcode_add"),
            {
                "code": "  lato10  ",
                "discount_type": "percentage",
                "value": "10.00",
                "rzut": "",
                "is_active": "on",
                "valid_from": "",
                "valid_until": "",
                "minimum_order_total": "",
                "usage_limit": "",
                "per_customer_limit": "1",
            },
        )

        self.assertRedirects(
            response,
            reverse("admin:shop_discountcode_changelist"),
        )
        code = DiscountCode.objects.get()
        self.assertEqual(code.code, "LATO10")
        self.assertEqual(code.discount_type, DiscountCode.Type.PERCENTAGE)
        self.assertEqual(code.value, Decimal("10.00"))
        self.assertIsNone(code.rzut)
        self.assertEqual(code.per_customer_limit, 1)

    def test_admin_creates_scoped_fixed_code_with_optional_limits(self):
        rzut = OrderEdition.objects.create(title="Rzut świąteczny")
        valid_from = timezone.now() + timedelta(days=1)
        valid_until = valid_from + timedelta(days=7)

        response = self.client.post(
            reverse("admin:shop_discountcode_add"),
            {
                "code": "swieta",
                "discount_type": "fixed_amount",
                "value": "25.00",
                "rzut": str(rzut.pk),
                "is_active": "on",
                "valid_from_0": valid_from.strftime("%Y-%m-%d"),
                "valid_from_1": valid_from.strftime("%H:%M:%S"),
                "valid_until_0": valid_until.strftime("%Y-%m-%d"),
                "valid_until_1": valid_until.strftime("%H:%M:%S"),
                "minimum_order_total": "50.00",
                "usage_limit": "10",
                "per_customer_limit": "2",
            },
        )

        self.assertRedirects(
            response,
            reverse("admin:shop_discountcode_changelist"),
        )
        code = DiscountCode.objects.get()
        self.assertEqual(code.code, "SWIETA")
        self.assertEqual(code.discount_type, DiscountCode.Type.FIXED_AMOUNT)
        self.assertEqual(code.rzut, rzut)
        self.assertEqual(code.minimum_order_total, Decimal("50.00"))
        self.assertEqual(code.usage_limit, 10)
        self.assertEqual(code.per_customer_limit, 2)

    def test_admin_rejects_percentage_above_100(self):
        response = self.client.post(
            reverse("admin:shop_discountcode_add"),
            {
                "code": "ZA-DUZO",
                "discount_type": "percentage",
                "value": "100.01",
                "rzut": "",
                "is_active": "on",
                "valid_from": "",
                "valid_until": "",
                "minimum_order_total": "",
                "usage_limit": "",
                "per_customer_limit": "1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Rabat procentowy nie może przekraczać 100%.",
        )
        self.assertFalse(DiscountCode.objects.exists())

    def test_admin_reports_required_value_without_server_error(self):
        response = self.client.post(
            reverse("admin:shop_discountcode_add"),
            {
                "code": "BRAK-WARTOSCI",
                "discount_type": "percentage",
                "value": "",
                "rzut": "",
                "is_active": "on",
                "valid_from": "",
                "valid_until": "",
                "minimum_order_total": "",
                "usage_limit": "",
                "per_customer_limit": "1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "To pole jest wymagane.")
        self.assertFalse(DiscountCode.objects.exists())

    def test_admin_rejects_same_code_with_other_case_and_spaces(self):
        DiscountCode.objects.create(
            code="LATO",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("5.00"),
        )

        response = self.client.post(
            reverse("admin:shop_discountcode_add"),
            {
                "code": "  lato  ",
                "discount_type": "fixed_amount",
                "value": "10.00",
                "rzut": "",
                "is_active": "on",
                "valid_from": "",
                "valid_until": "",
                "minimum_order_total": "",
                "usage_limit": "",
                "per_customer_limit": "1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Istnieje już Kod Rabatowy")
        self.assertEqual(DiscountCode.objects.count(), 1)


class DiscountCodeHttpTestCase(TestCase):
    def setUp(self):
        now = timezone.now()
        self.rzut = OrderEdition.objects.create(
            title="Rzut niedzielny",
            description="Niedzielne wypieki.",
            status=OrderEdition.Status.PUBLISHED,
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(hours=1),
            pickup_date=timezone.localdate() + timedelta(days=1),
            pickup_place_name="Kuchenna Komitywa",
            pickup_address="ul. Bukowa 14, Białystok",
            pickup_starts_at=time(10, 0),
            pickup_ends_at=time(12, 0),
            pickup_instructions="Wejście od ogrodu.",
        )
        product = Product.objects.create(
            title="Chleb wiejski",
            description="Chleb na zakwasie.",
            ingredients="mąka, woda, sól",
            allergens="gluten",
            price=Decimal("24.00"),
            default_portion="bochenek ok. 750 g",
            is_available_in_shop=False,
        )
        self.item = RzutItem.objects.create(
            rzut=self.rzut,
            product=product,
            price=Decimal("26.00"),
            portion="bochenek ok. 750 g",
            pool=10,
        )
        self.client.post(
            reverse("shop:rzut_cart_add", args=[self.item.pk])
        )
        self.client.post(
            reverse("shop:rzut_cart_update", args=[self.item.pk]),
            {"quantity": "2"},
        )

    def checkout_data(self, *, email="jan@example.com"):
        return ReservationCheckoutData(
            name="Jan Kowalski",
            email=email,
            phone="",
            notes="",
            pickup_starts_at=time(10, 0),
            pickup_ends_at=time(11, 0),
        )

    def checkout_form_data(self, *, email="jan@example.com"):
        return {
            "name": "Jan Kowalski",
            "email": email,
            "phone": "",
            "notes": "",
            "pickup_slot": "10:00:00|11:00:00",
            "consent_data": "on",
            "consent_terms": "on",
        }


class TestDiscountCodeCart(DiscountCodeHttpTestCase):
    def test_customer_applies_one_normalized_percentage_code(self):
        DiscountCode.objects.create(
            code="LATO10",
            discount_type=DiscountCode.Type.PERCENTAGE,
            value=Decimal("10.00"),
        )

        response = self.client.post(
            reverse("shop:rzut_cart_discount"),
            {"code": "  lato10  "},
            follow=True,
        )

        self.assertContains(response, "przed rabatem")
        self.assertContains(response, "52,00 zł")
        self.assertContains(response, "rabat LATO10")
        self.assertContains(response, "5,20 zł")
        self.assertContains(response, "46,80 zł")
        self.assertEqual(
            self.client.session["rzut_cart"]["discount_code"],
            "LATO10",
        )

    def test_percentage_rounds_to_grosz_and_fixed_discount_stops_at_zero(self):
        DiscountCode.objects.create(
            code="TRZECIA",
            discount_type=DiscountCode.Type.PERCENTAGE,
            value=Decimal("33.33"),
        )
        DiscountCode.objects.create(
            code="GRATIS",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("100.00"),
        )

        percentage = self.client.post(
            reverse("shop:rzut_cart_discount"),
            {"code": "TRZECIA"},
            follow=True,
        )
        fixed = self.client.post(
            reverse("shop:rzut_cart_discount"),
            {"code": "GRATIS"},
            follow=True,
        )

        self.assertContains(percentage, "17,33 zł")
        self.assertContains(percentage, "34,67 zł")
        self.assertContains(fixed, "52,00 zł")
        self.assertContains(fixed, "0,00 zł")

    def test_cart_rejects_inactive_scoped_dated_minimum_and_exhausted_codes(
        self,
    ):
        other_rzut = OrderEdition.objects.create(title="Inny Rzut")
        now = timezone.now()
        cases = [
            (
                {"code": "OFF", "is_active": False},
                "wyłączony",
            ),
            (
                {"code": "INNY", "rzut": other_rzut},
                "nie obowiązuje w tym Rzucie",
            ),
            (
                {"code": "JUTRO", "valid_from": now + timedelta(days=1)},
                "jeszcze się nie rozpoczął",
            ),
            (
                {"code": "WCZORAJ", "valid_until": now - timedelta(days=1)},
                "wygasł",
            ),
            (
                {
                    "code": "MINIMUM",
                    "minimum_order_total": Decimal("52.01"),
                },
                "Minimalna wartość Zamówienia",
            ),
            (
                {"code": "LIMIT", "usage_limit": 1, "allocated_uses": 1},
                "Łączny limit użyć",
            ),
        ]
        for overrides, expected_message in cases:
            with self.subTest(code=overrides["code"]):
                values = {
                    "discount_type": DiscountCode.Type.FIXED_AMOUNT,
                    "value": Decimal("5.00"),
                }
                values.update(overrides)
                code = DiscountCode.objects.create(**values)

                response = self.client.post(
                    reverse("shop:rzut_cart_discount"),
                    {"code": code.code},
                    follow=True,
                )

                self.assertContains(response, expected_message)
                self.assertNotIn(
                    "discount_code",
                    self.client.session["rzut_cart"],
                )

    def test_global_rzut_code_does_not_discount_shop_cart(self):
        shop_product = Product.objects.create(
            title="Ebook",
            type="ebook",
            description="Przepisy.",
            price=Decimal("19.00"),
            is_available_in_shop=True,
        )
        code = DiscountCode.objects.create(
            code="GRATIS",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("100.00"),
        )
        self.client.post(reverse("shop:cart_add", args=[shop_product.pk]))
        self.client.post(
            reverse("shop:rzut_cart_discount"),
            {"code": code.code},
        )

        shop_cart = self.client.get(reverse("shop:cart"))

        self.assertContains(shop_cart, "19,00 zł")
        self.assertNotContains(shop_cart, "GRATIS")

    def test_code_is_cleared_when_last_unavailable_item_is_removed(self):
        code = DiscountCode.objects.create(
            code="GLOBALNY",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("5.00"),
        )
        self.client.post(
            reverse("shop:rzut_cart_discount"),
            {"code": code.code},
        )
        self.item.is_active = False
        self.item.save(update_fields=["is_active"])

        self.client.get(reverse("shop:rzut_cart"))

        self.assertNotIn(
            "discount_code",
            self.client.session["rzut_cart"],
        )

    @patch("shop.views.register_rzut_transaction", return_value="token-123")
    def test_customer_can_remove_code_disabled_after_application(
        self,
        register_payment,
    ):
        code = DiscountCode.objects.create(
            code="CHWILOWY",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("5.00"),
        )
        self.client.post(
            reverse("shop:rzut_cart_discount"),
            {"code": code.code},
        )
        code.is_active = False
        code.save(update_fields=["is_active"])

        cart = self.client.get(reverse("shop:rzut_cart"))
        self.assertContains(cart, "Kod Rabatowy jest wyłączony")
        self.assertContains(cart, "Usuń Kod Rabatowy")
        self.client.post(reverse("shop:rzut_cart_discount_remove"))
        response = self.client.post(
            reverse("shop:rzut_checkout"),
            self.checkout_form_data(),
        )

        reservation = Reservation.objects.get()
        self.assertRedirects(
            response,
            "https://sandbox.przelewy24.pl/trnRequest/token-123",
            fetch_redirect_response=False,
        )
        self.assertEqual(reservation.total, Decimal("52.00"))
        register_payment.assert_called_once()


class TestDiscountCodeReservation(DiscountCodeHttpTestCase):
    def test_reservation_atomically_allocates_code_and_discount(self):
        code = DiscountCode.objects.create(
            code="LATO10",
            discount_type=DiscountCode.Type.PERCENTAGE,
            value=Decimal("10.00"),
            rzut=self.rzut,
            usage_limit=5,
        )

        reservation = create_reservation(
            rzut_id=self.rzut.pk,
            lines=[ReservationLineRequest(self.item.pk, 2, self.item.price)],
            checkout=self.checkout_data(),
            discount_code=" lato10 ",
        )

        code.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(reservation.subtotal, Decimal("52.00"))
        self.assertEqual(reservation.discount_amount, Decimal("5.20"))
        self.assertEqual(reservation.total, Decimal("46.80"))
        self.assertEqual(reservation.discount_code, code)
        self.assertEqual(reservation.discount_code_snapshot, "LATO10")
        self.assertEqual(code.allocated_uses, 1)
        self.assertEqual(self.item.allocated_quantity, 2)

    def test_confirmed_order_keeps_discount_after_code_is_disabled(self):
        code = DiscountCode.objects.create(
            code="LATO10",
            discount_type=DiscountCode.Type.PERCENTAGE,
            value=Decimal("10.00"),
        )
        reservation = create_reservation(
            rzut_id=self.rzut.pk,
            lines=[ReservationLineRequest(self.item.pk, 2, self.item.price)],
            checkout=self.checkout_data(),
            discount_code=code.code,
        )
        code.is_active = False
        code.save(update_fields=["is_active"])

        order, created = confirm_reservation(
            reservation_id=reservation.pk,
            p24_order_id=987654,
        )

        code.refresh_from_db()
        self.assertTrue(created)
        self.assertEqual(order.subtotal, Decimal("52.00"))
        self.assertEqual(order.discount_amount, Decimal("5.20"))
        self.assertEqual(order.total, Decimal("46.80"))
        self.assertEqual(order.discount_code, code)
        self.assertEqual(order.discount_code_snapshot, "LATO10")
        self.assertEqual(code.allocated_uses, 1)
        detail = self.client.get(
            reverse("shop:rzut_order_detail", args=[order.number])
        )
        self.assertContains(detail, "Suma przed rabatem")
        self.assertContains(detail, "52,00 zł")
        self.assertContains(detail, "Kod Rabatowy LATO10")
        self.assertContains(detail, "5,20 zł")
        self.assertContains(detail, "46,80 zł")
        with self.assertRaisesMessage(
            ReservationUnavailable,
            "Kod Rabatowy jest wyłączony",
        ):
            create_reservation(
                rzut_id=self.rzut.pk,
                lines=[
                    ReservationLineRequest(self.item.pk, 1, self.item.price)
                ],
                checkout=self.checkout_data(email="anna@example.com"),
                discount_code=code.code,
            )

    @patch("shop.views.register_rzut_transaction", return_value="token-123")
    def test_checkout_revalidates_applied_code(self, register_payment):
        code = DiscountCode.objects.create(
            code="LATO10",
            discount_type=DiscountCode.Type.PERCENTAGE,
            value=Decimal("10.00"),
        )
        self.client.post(
            reverse("shop:rzut_cart_discount"),
            {"code": code.code},
        )

        response = self.client.post(
            reverse("shop:rzut_checkout"),
            self.checkout_form_data(),
        )

        reservation = Reservation.objects.get()
        self.assertRedirects(
            response,
            "https://sandbox.przelewy24.pl/trnRequest/token-123",
            fetch_redirect_response=False,
        )
        self.assertEqual(reservation.total, Decimal("46.80"))
        self.assertEqual(reservation.discount_code, code)
        register_payment.assert_called_once()

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="Kuchenna Komitywa <noreply@example.com>",
        CONTACT_EMAIL="owner@example.com",
        PUBLIC_SITE_URL="https://example.com",
    )
    @patch("shop.views.register_rzut_transaction")
    def test_full_discount_creates_order_without_p24(self, register_payment):
        code = DiscountCode.objects.create(
            code="GRATIS",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("100.00"),
        )
        self.client.post(
            reverse("shop:rzut_cart_discount"),
            {"code": code.code},
        )

        response = self.client.post(
            reverse("shop:rzut_checkout"),
            self.checkout_form_data(),
        )

        reservation = Reservation.objects.get()
        order = reservation.rzut_order
        code.refresh_from_db()
        self.assertRedirects(
            response,
            reverse("shop:rzut_order_detail", args=[order.number]),
        )
        self.assertEqual(reservation.status, Reservation.Status.CONFIRMED)
        self.assertEqual(order.subtotal, Decimal("52.00"))
        self.assertEqual(order.discount_amount, Decimal("52.00"))
        self.assertEqual(order.total, Decimal("0.00"))
        self.assertEqual(
            order.payment_status,
            order.PaymentStatus.NOT_REQUIRED,
        )
        self.assertEqual(order.payment_method, order.PaymentMethod.NONE)
        self.assertIsNone(order.p24_order_id)
        self.assertEqual(code.allocated_uses, 1)
        self.assertNotIn("rzut_cart", self.client.session)
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn("0,00 zł", mail.outbox[0].body)
        self.assertIn("GRATIS", mail.outbox[0].body)
        register_payment.assert_not_called()

    @patch(
        "shop.reservations._materialize_order",
        side_effect=RuntimeError("order failed"),
    )
    def test_zero_total_order_creation_rolls_back_reservation(self, _create):
        code = DiscountCode.objects.create(
            code="GRATIS",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("100.00"),
        )

        with self.assertRaisesMessage(RuntimeError, "order failed"):
            start_checkout(
                rzut_id=self.rzut.pk,
                lines=[
                    ReservationLineRequest(
                        self.item.pk,
                        2,
                        self.item.price,
                    )
                ],
                checkout=self.checkout_data(),
                discount_code=code.code,
            )

        code.refresh_from_db()
        self.item.refresh_from_db()
        self.assertFalse(Reservation.objects.exists())
        self.assertEqual(code.allocated_uses, 0)
        self.assertEqual(self.item.allocated_quantity, 0)

    def test_start_checkout_returns_confirmed_zero_total_order(self):
        code = DiscountCode.objects.create(
            code="GRATIS",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("100.00"),
        )

        result = start_checkout(
            rzut_id=self.rzut.pk,
            lines=[ReservationLineRequest(self.item.pk, 2, self.item.price)],
            checkout=self.checkout_data(),
            discount_code=code.code,
        )

        self.assertIsInstance(result, OrderConfirmed)
        self.assertEqual(result.order.total, Decimal("0.00"))

    def test_total_usage_limit_cannot_be_exceeded(self):
        code = DiscountCode.objects.create(
            code="OSTATNI",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("5.00"),
            usage_limit=1,
        )
        create_reservation(
            rzut_id=self.rzut.pk,
            lines=[ReservationLineRequest(self.item.pk, 1, self.item.price)],
            checkout=self.checkout_data(email="one@example.com"),
            discount_code=code.code,
        )

        with self.assertRaisesMessage(
            ReservationUnavailable,
            "Łączny limit użyć",
        ):
            create_reservation(
                rzut_id=self.rzut.pk,
                lines=[
                    ReservationLineRequest(self.item.pk, 1, self.item.price)
                ],
                checkout=self.checkout_data(email="two@example.com"),
                discount_code=code.code,
            )

        code.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(code.allocated_uses, 1)
        self.assertEqual(self.item.allocated_quantity, 1)

    def test_default_per_email_limit_allows_another_customer_only(self):
        code = DiscountCode.objects.create(
            code="RAZ",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("5.00"),
        )
        create_reservation(
            rzut_id=self.rzut.pk,
            lines=[ReservationLineRequest(self.item.pk, 1, self.item.price)],
            checkout=self.checkout_data(email=" JAN@example.com "),
            discount_code=code.code,
        )

        with self.assertRaisesMessage(
            ReservationUnavailable,
            "dla podanego e-maila",
        ):
            create_reservation(
                rzut_id=self.rzut.pk,
                lines=[
                    ReservationLineRequest(self.item.pk, 1, self.item.price)
                ],
                checkout=self.checkout_data(email="jan@EXAMPLE.com"),
                discount_code=code.code,
            )
        create_reservation(
            rzut_id=self.rzut.pk,
            lines=[ReservationLineRequest(self.item.pk, 1, self.item.price)],
            checkout=self.checkout_data(email="anna@example.com"),
            discount_code=code.code,
        )

        code.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(code.allocated_uses, 2)
        self.assertEqual(self.item.allocated_quantity, 2)

    def test_failed_and_expired_reservations_release_code_use(self):
        code = DiscountCode.objects.create(
            code="PONOW",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("5.00"),
            usage_limit=1,
        )
        failed = create_reservation(
            rzut_id=self.rzut.pk,
            lines=[ReservationLineRequest(self.item.pk, 1, self.item.price)],
            checkout=self.checkout_data(),
            discount_code=code.code,
        )
        fail_reservation(failed)
        retried = create_reservation(
            rzut_id=self.rzut.pk,
            lines=[ReservationLineRequest(self.item.pk, 1, self.item.price)],
            checkout=self.checkout_data(),
            discount_code=code.code,
        )

        expire_due_reservations(now=retried.expires_at)

        failed.refresh_from_db()
        code.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(failed.status, Reservation.Status.FAILED)
        retried.refresh_from_db()
        self.assertEqual(retried.status, Reservation.Status.EXPIRED)
        self.assertEqual(code.allocated_uses, 0)
        self.assertEqual(self.item.allocated_quantity, 0)

    def test_late_paid_order_reclaims_released_code_use(self):
        code = DiscountCode.objects.create(
            code="OSTATNI",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("5.00"),
            usage_limit=1,
        )
        late = create_reservation(
            rzut_id=self.rzut.pk,
            lines=[ReservationLineRequest(self.item.pk, 1, self.item.price)],
            checkout=self.checkout_data(email="late@example.com"),
            discount_code=code.code,
        )
        expire_due_reservations(now=late.expires_at)
        create_reservation(
            rzut_id=self.rzut.pk,
            lines=[ReservationLineRequest(self.item.pk, 1, self.item.price)],
            checkout=self.checkout_data(email="current@example.com"),
            discount_code=code.code,
        )

        with self.assertLogs("shop.reservations", level="CRITICAL"):
            order, created = confirm_reservation(
                reservation_id=late.pk,
                p24_order_id=987654,
                confirmed_at=late.expires_at + timedelta(minutes=1),
            )

        code.refresh_from_db()
        self.assertTrue(created)
        self.assertEqual(order.payment_status, order.PaymentStatus.PAID)
        self.assertEqual(code.allocated_uses, 2)
        self.assertIn("Przekroczenie limitu Kodu", order.attention_message)

    def test_retry_restores_code_for_fresh_validation(self):
        code = DiscountCode.objects.create(
            code="PONOW",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("5.00"),
        )
        expired = create_reservation(
            rzut_id=self.rzut.pk,
            lines=[ReservationLineRequest(self.item.pk, 1, self.item.price)],
            checkout=self.checkout_data(),
            discount_code=code.code,
        )
        expire_due_reservations(now=expired.expires_at)

        response = self.client.post(
            reverse(
                "shop:rzut_reservation_retry",
                args=[expired.p24_session_id],
            )
        )

        self.assertRedirects(response, reverse("shop:rzut_cart"))
        self.assertEqual(
            self.client.session["rzut_cart"]["discount_code"],
            "PONOW",
        )
        code.is_active = False
        code.save(update_fields=["is_active"])
        cart = self.client.get(reverse("shop:rzut_cart"))
        self.assertContains(cart, "Kod Rabatowy jest wyłączony")


class TestConcurrentDiscountCode(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        now = timezone.now()
        self.rzuty_and_items = []
        for index in range(2):
            rzut = OrderEdition.objects.create(
                title=f"Rzut {index}",
                description="Niedzielne wypieki.",
                status=OrderEdition.Status.PUBLISHED,
                opens_at=now - timedelta(hours=1),
                closes_at=now + timedelta(hours=1),
                pickup_date=timezone.localdate() + timedelta(days=1),
                pickup_place_name="Kuchenna Komitywa",
                pickup_address="ul. Bukowa 14, Białystok",
                pickup_starts_at=time(10, 0),
                pickup_ends_at=time(12, 0),
                pickup_instructions="Wejście od ogrodu.",
            )
            product = Product.objects.create(
                title=f"Chleb {index}",
                description="Chleb na zakwasie.",
                ingredients="mąka, woda, sól",
                allergens="gluten",
                price=Decimal("24.00"),
                default_portion="bochenek ok. 750 g",
                is_available_in_shop=False,
            )
            item = RzutItem.objects.create(
                rzut=rzut,
                product=product,
                price=Decimal("26.00"),
                portion="bochenek ok. 750 g",
                pool=10,
            )
            self.rzuty_and_items.append((rzut, item))
        self.code = DiscountCode.objects.create(
            code="JEDEN",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("5.00"),
            usage_limit=1,
        )

    def test_simultaneous_rzuty_cannot_exceed_total_usage_limit(self):
        barrier = Barrier(2)

        def attempt(index):
            close_old_connections()
            rzut, item = self.rzuty_and_items[index]
            barrier.wait()
            try:
                create_reservation(
                    rzut_id=rzut.pk,
                    lines=[
                        ReservationLineRequest(item.pk, 1, item.price)
                    ],
                    checkout=ReservationCheckoutData(
                        name=f"Klient {index}",
                        email=f"klient{index}@example.com",
                        phone="",
                        notes="",
                        pickup_starts_at=time(10, 0),
                        pickup_ends_at=time(11, 0),
                    ),
                    discount_code=self.code.code,
                )
                return "reserved"
            except ReservationUnavailable:
                return "rejected"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(attempt, range(2)))

        self.code.refresh_from_db()
        allocated_items = sum(
            RzutItem.objects.get(pk=item.pk).allocated_quantity
            for _, item in self.rzuty_and_items
        )
        self.assertEqual(results.count("reserved"), 1)
        self.assertEqual(results.count("rejected"), 1)
        self.assertEqual(self.code.allocated_uses, 1)
        self.assertEqual(allocated_items, 1)

    def test_simultaneous_rzuty_cannot_exceed_per_email_limit(self):
        self.code.usage_limit = None
        self.code.save(update_fields=["usage_limit"])
        barrier = Barrier(2)

        def attempt(index):
            close_old_connections()
            rzut, item = self.rzuty_and_items[index]
            barrier.wait()
            try:
                create_reservation(
                    rzut_id=rzut.pk,
                    lines=[
                        ReservationLineRequest(item.pk, 1, item.price)
                    ],
                    checkout=ReservationCheckoutData(
                        name=f"Klient {index}",
                        email=" wspolny@Example.com ",
                        phone="",
                        notes="",
                        pickup_starts_at=time(10, 0),
                        pickup_ends_at=time(11, 0),
                    ),
                    discount_code=self.code.code,
                )
                return "reserved"
            except ReservationUnavailable:
                return "rejected"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(attempt, range(2)))

        self.code.refresh_from_db()
        self.assertEqual(results.count("reserved"), 1)
        self.assertEqual(results.count("rejected"), 1)
        self.assertEqual(self.code.allocated_uses, 1)
