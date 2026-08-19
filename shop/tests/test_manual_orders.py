from concurrent.futures import ThreadPoolExecutor
from datetime import time, timedelta
from decimal import Decimal
from threading import Barrier
import uuid

from django.contrib.auth import get_user_model
from django.core import mail
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core import legal
from shop.manual_orders import (
    ManualOrderData,
    ManualOrderLineRequest,
    ManualOrderUnavailable,
    create_manual_order,
)
from shop.models import (
    DiscountCode,
    OrderEdition,
    PickupSlot,
    Product,
    Reservation,
    RzutItem,
    RzutOrder,
)
from shop.reservations import (
    ReservationCheckoutData,
    ReservationCustomerLimitExceeded,
    ReservationLineRequest,
    create_reservation,
)


class ManualOrderTestCase(TestCase):
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

    def manual_data(self, **overrides):
        values = {
            "rzut_id": self.rzut.pk,
            "customer_name": "Jan Kowalski",
            "customer_email": " JAN@Example.com ",
            "customer_phone": "+48 500 600 700",
            "customer_notes": "Płatność przy odbiorze.",
            "pickup_slot": PickupSlot(time(10, 0), time(11, 0)),
            "payment_status": RzutOrder.PaymentStatus.PENDING,
            "payment_method": RzutOrder.PaymentMethod.CASH,
            "payment_method_details": "",
            "discount_code": "",
        }
        values.update(overrides)
        return ManualOrderData(**values)


class TestCreateManualOrder(ManualOrderTestCase):
    def test_cash_on_pickup_creates_confirmed_order_without_reservation(self):
        order = create_manual_order(
            data=self.manual_data(),
            lines=[ManualOrderLineRequest(self.item.pk, 2)],
        )

        self.item.refresh_from_db()
        order_item = order.items.get()
        self.assertTrue(order.is_manual)
        self.assertIsNone(order.reservation)
        self.assertFalse(Reservation.objects.exists())
        self.assertEqual(order.customer_email, "jan@example.com")
        self.assertEqual(order.payment_status, RzutOrder.PaymentStatus.PENDING)
        self.assertEqual(order.payment_method, RzutOrder.PaymentMethod.CASH)
        self.assertEqual(
            order.fulfillment_stage,
            RzutOrder.FulfillmentStage.NEW,
        )
        self.assertEqual(order.subtotal, Decimal("52.00"))
        self.assertEqual(order.total, Decimal("52.00"))
        self.assertEqual(order_item.product_name, "Chleb wiejski")
        self.assertEqual(order_item.portion, "bochenek ok. 750 g")
        self.assertEqual(order_item.unit_price, Decimal("26.00"))
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.line_total, Decimal("52.00"))
        self.assertEqual(self.item.allocated_quantity, 2)

    def test_customer_limit_counts_existing_manual_order_in_whole_rzut(self):
        self.item.per_customer_limit = 2
        self.item.save(update_fields=["per_customer_limit"])
        create_manual_order(
            data=self.manual_data(customer_email="jan@example.com"),
            lines=[ManualOrderLineRequest(self.item.pk, 1)],
        )

        with self.assertRaisesMessage(
            ManualOrderUnavailable,
            "Limit Klienta",
        ):
            create_manual_order(
                data=self.manual_data(customer_email=" JAN@EXAMPLE.COM "),
                lines=[ManualOrderLineRequest(self.item.pk, 2)],
            )

        self.item.refresh_from_db()
        self.assertEqual(RzutOrder.objects.count(), 1)
        self.assertEqual(self.item.allocated_quantity, 1)

    def test_online_reservation_counts_existing_manual_order(self):
        self.item.per_customer_limit = 1
        self.item.save(update_fields=["per_customer_limit"])
        create_manual_order(
            data=self.manual_data(customer_email="jan@example.com"),
            lines=[ManualOrderLineRequest(self.item.pk, 1)],
        )

        with self.assertRaisesMessage(
            ReservationCustomerLimitExceeded,
            "Limit Klienta",
        ):
            create_reservation(
                rzut_id=self.rzut.pk,
                lines=[
                    ReservationLineRequest(self.item.pk, 1, self.item.price)
                ],
                checkout=ReservationCheckoutData(
                    name="Jan Kowalski",
                    email="JAN@example.com",
                    phone="",
                    notes="",
                    pickup_starts_at=time(10, 0),
                    pickup_ends_at=time(11, 0),
                    terms_version=legal.CURRENT_TERMS.identifier,
                ),
            )

        self.item.refresh_from_db()
        self.assertEqual(self.item.allocated_quantity, 1)

    def test_manual_order_counts_existing_online_reservation(self):
        self.item.per_customer_limit = 2
        self.item.save(update_fields=["per_customer_limit"])
        create_reservation(
            rzut_id=self.rzut.pk,
            lines=[ReservationLineRequest(self.item.pk, 1, self.item.price)],
            checkout=ReservationCheckoutData(
                name="Jan Kowalski",
                email="jan@example.com",
                phone="",
                notes="",
                pickup_starts_at=time(10, 0),
                pickup_ends_at=time(11, 0),
                terms_version=legal.CURRENT_TERMS.identifier,
            ),
        )

        with self.assertRaisesMessage(ManualOrderUnavailable, "Limit Klienta"):
            create_manual_order(
                data=self.manual_data(customer_email="JAN@example.com"),
                lines=[ManualOrderLineRequest(self.item.pk, 2)],
            )

        self.item.refresh_from_db()
        self.assertEqual(self.item.allocated_quantity, 1)
        self.assertFalse(RzutOrder.objects.exists())

    def test_product_changes_do_not_rewrite_manual_order_item_snapshot(self):
        order = create_manual_order(
            data=self.manual_data(),
            lines=[ManualOrderLineRequest(self.item.pk, 1)],
        )

        Product.objects.filter(pk=self.item.product_id).update(
            title="Nowa nazwa",
        )
        RzutItem.objects.filter(pk=self.item.pk).update(
            portion="nowa Porcja",
            price=Decimal("99.00"),
        )

        order_item = order.items.get()
        self.assertEqual(order_item.product_name, "Chleb wiejski")
        self.assertEqual(order_item.portion, "bochenek ok. 750 g")
        self.assertEqual(order_item.unit_price, Decimal("26.00"))
        self.assertEqual(order_item.line_total, Decimal("26.00"))

    def test_full_discount_uses_code_and_creates_zero_total_order(self):
        code = DiscountCode.objects.create(
            code="GRATIS",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("100.00"),
            usage_limit=1,
        )

        order = create_manual_order(
            data=self.manual_data(
                payment_status=RzutOrder.PaymentStatus.NOT_REQUIRED,
                payment_method=RzutOrder.PaymentMethod.NONE,
                discount_code=" gratis ",
            ),
            lines=[ManualOrderLineRequest(self.item.pk, 2)],
        )

        code.refresh_from_db()
        self.assertEqual(order.subtotal, Decimal("52.00"))
        self.assertEqual(order.discount_amount, Decimal("52.00"))
        self.assertEqual(order.total, Decimal("0.00"))
        self.assertEqual(order.discount_code, code)
        self.assertEqual(order.discount_code_snapshot, "GRATIS")
        self.assertEqual(code.allocated_uses, 1)

    def test_discount_per_email_limit_counts_manual_orders(self):
        code = DiscountCode.objects.create(
            code="RAZ",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("5.00"),
        )
        create_manual_order(
            data=self.manual_data(discount_code=code.code),
            lines=[ManualOrderLineRequest(self.item.pk, 1)],
        )

        with self.assertRaisesMessage(
            ManualOrderUnavailable,
            "dla podanego e-maila",
        ):
            create_manual_order(
                data=self.manual_data(
                    customer_email="jan@EXAMPLE.com",
                    discount_code=code.code,
                ),
                lines=[ManualOrderLineRequest(self.item.pk, 1)],
            )

        code.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(RzutOrder.objects.count(), 1)
        self.assertEqual(code.allocated_uses, 1)
        self.assertEqual(self.item.allocated_quantity, 1)

    def test_cancelled_manual_order_still_counts_towards_discount_email_limit(self):
        code = DiscountCode.objects.create(
            code="RAZ",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("5.00"),
        )
        order = create_manual_order(
            data=self.manual_data(discount_code=code.code),
            lines=[ManualOrderLineRequest(self.item.pk, 1)],
        )
        order.fulfillment_stage = RzutOrder.FulfillmentStage.CANCELLED
        order.save(update_fields=["fulfillment_stage"])

        with self.assertRaisesMessage(
            ManualOrderUnavailable,
            "dla podanego e-maila",
        ):
            create_manual_order(
                data=self.manual_data(discount_code=code.code),
                lines=[ManualOrderLineRequest(self.item.pk, 1)],
            )

        code.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(RzutOrder.objects.count(), 1)
        self.assertEqual(code.allocated_uses, 1)
        self.assertEqual(self.item.allocated_quantity, 1)

    def test_other_payment_method_requires_explanation(self):
        with self.assertRaisesMessage(
            ManualOrderUnavailable,
            "Wyjaśnij inną Metodę Płatności",
        ):
            create_manual_order(
                data=self.manual_data(
                    payment_method=RzutOrder.PaymentMethod.OTHER,
                    payment_method_details="",
                ),
                lines=[ManualOrderLineRequest(self.item.pk, 1)],
            )

        order = create_manual_order(
            data=self.manual_data(
                customer_email="anna@example.com",
                payment_method=RzutOrder.PaymentMethod.OTHER,
                payment_method_details="Voucher papierowy",
            ),
            lines=[ManualOrderLineRequest(self.item.pk, 1)],
        )

        self.assertEqual(order.payment_method, RzutOrder.PaymentMethod.OTHER)
        self.assertEqual(order.payment_method_details, "Voucher papierowy")

    def test_customer_name_and_valid_email_are_required(self):
        cases = [
            ({"customer_name": "   "}, "imię i nazwisko"),
            ({"customer_email": "nie-e-mail"}, "prawidłowy e-mail"),
        ]

        for overrides, message in cases:
            with self.subTest(overrides=overrides):
                with self.assertRaisesMessage(ManualOrderUnavailable, message):
                    create_manual_order(
                        data=self.manual_data(**overrides),
                        lines=[ManualOrderLineRequest(self.item.pk, 1)],
                    )

        self.assertFalse(RzutOrder.objects.exists())
        self.item.refresh_from_db()
        self.assertEqual(self.item.allocated_quantity, 0)

    def test_zero_total_requires_not_required_status_and_no_payment_method(self):
        code = DiscountCode.objects.create(
            code="GRATIS",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("100.00"),
        )

        with self.assertRaisesMessage(
            ManualOrderUnavailable,
            "Należność 0,00 zł",
        ):
            create_manual_order(
                data=self.manual_data(discount_code=code.code),
                lines=[ManualOrderLineRequest(self.item.pk, 2)],
            )

        code.refresh_from_db()
        self.item.refresh_from_db()
        self.assertFalse(RzutOrder.objects.exists())
        self.assertEqual(code.allocated_uses, 0)
        self.assertEqual(self.item.allocated_quantity, 0)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="Kuchenna Komitywa <noreply@example.com>",
    CONTACT_EMAIL="owner@example.com",
    PUBLIC_SITE_URL="https://example.com",
)
class TestManualOrderAdmin(ManualOrderTestCase):
    def setUp(self):
        super().setUp()
        admin_user = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="testpass123",
        )
        self.client.force_login(admin_user)

    def admin_data(self, **overrides):
        values = {
            "rzut": str(self.rzut.pk),
            "customer_name": "Jan Kowalski",
            "customer_email": " JAN@Example.com ",
            "customer_phone": "+48 500 600 700",
            "customer_notes": "Płatność przy odbiorze.",
            "pickup_slot": "10:00:00|11:00:00",
            "payment_status": RzutOrder.PaymentStatus.PENDING,
            "payment_method": RzutOrder.PaymentMethod.CASH,
            "payment_method_details": "",
            "discount_code": "",
            "creation_token": str(uuid.uuid4()),
            f"quantity_{self.item.pk}": "2",
            "_save": "Zapisz",
        }
        values.update(overrides)
        return values

    def test_admin_creates_cash_on_pickup_order_and_emails_customer_only(self):
        response = self.client.post(
            reverse("admin:shop_rzutorder_add"),
            self.admin_data(),
        )

        order = RzutOrder.objects.get()
        self.assertRedirects(
            response,
            reverse("admin:shop_rzutorder_change", args=[order.pk]),
        )
        self.assertTrue(order.is_manual)
        self.assertEqual(order.customer_email, "jan@example.com")
        self.assertEqual(order.payment_status, RzutOrder.PaymentStatus.PENDING)
        self.assertEqual(order.payment_method, RzutOrder.PaymentMethod.CASH)
        self.assertEqual(order.fulfillment_stage, RzutOrder.FulfillmentStage.NEW)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["jan@example.com"])
        self.assertIn("Zamówienie Ręczne", mail.outbox[0].body)
        self.assertIn("Status Płatności: Oczekuje", mail.outbox[0].body)
        self.assertIn("Metoda Płatności: Gotówka", mail.outbox[0].body)
        self.assertIsNone(order.owner_notification_sent_at)

    def test_admin_form_offers_all_payment_statuses_and_methods(self):
        response = self.client.get(
            reverse("admin:shop_rzutorder_add"),
            {"rzut": self.rzut.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wczytaj Pozycje Rzutu")
        self.assertNotContains(response, "onchange")
        self.assertContains(
            response,
            self.rzut.pickup_date.strftime("%d.%m.%Y"),
        )
        self.assertContains(response, self.rzut.get_status_display())
        self.assertContains(response, "Chleb wiejski")
        for label in ["Oczekuje", "Opłacona", "Nie wymaga płatności", "Zwrócona"]:
            self.assertContains(response, label)
        for label in [
            "Przelewy24",
            "Gotówka",
            "Przelew ręczny",
            "Inna",
            "Brak płatności",
        ]:
            self.assertContains(response, label)

    def test_admin_blocks_rzut_without_items_or_pickup_slots_with_next_steps(self):
        empty_rzut = OrderEdition.objects.create(
            title="Nieuzupełniony Rzut",
            status=OrderEdition.Status.DRAFT,
        )

        response = self.client.get(
            reverse("admin:shop_rzutorder_add"),
            {"rzut": empty_rzut.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "nie ma aktywnych fizycznych Pozycji")
        self.assertContains(response, "nie ma dostępnych Przedziałów Odbioru")
        self.assertContains(
            response,
            reverse("admin:shop_orderedition_change", args=[empty_rzut.pk]),
        )
        self.assertNotContains(response, 'name="_save"', html=False)

    def test_admin_creates_zero_total_order_with_full_discount(self):
        code = DiscountCode.objects.create(
            code="GRATIS",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("100.00"),
        )

        response = self.client.post(
            reverse("admin:shop_rzutorder_add"),
            self.admin_data(
                payment_status=RzutOrder.PaymentStatus.NOT_REQUIRED,
                payment_method=RzutOrder.PaymentMethod.NONE,
                discount_code=" gratis ",
            ),
        )

        order = RzutOrder.objects.get()
        self.assertRedirects(
            response,
            reverse("admin:shop_rzutorder_change", args=[order.pk]),
        )
        self.assertEqual(order.subtotal, Decimal("52.00"))
        self.assertEqual(order.discount_amount, Decimal("52.00"))
        self.assertEqual(order.total, Decimal("0.00"))
        self.assertEqual(order.discount_code_snapshot, "GRATIS")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Kod Rabatowy: GRATIS", mail.outbox[0].body)
        self.assertIn("Do zapłaty: 0,00 zł", mail.outbox[0].body)

    def test_admin_cannot_exceed_customer_limit(self):
        self.item.per_customer_limit = 2
        self.item.save(update_fields=["per_customer_limit"])
        create_manual_order(
            data=self.manual_data(customer_email="jan@example.com"),
            lines=[ManualOrderLineRequest(self.item.pk, 1)],
        )

        response = self.client.post(
            reverse("admin:shop_rzutorder_add"),
            self.admin_data(**{f"quantity_{self.item.pk}": "2"}),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Limit Klienta")
        self.assertEqual(RzutOrder.objects.count(), 1)
        self.item.refresh_from_db()
        self.assertEqual(self.item.allocated_quantity, 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_admin_cannot_use_discount_after_total_limit_is_exhausted(self):
        code = DiscountCode.objects.create(
            code="KONIEC",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("5.00"),
            usage_limit=1,
            allocated_uses=1,
        )

        response = self.client.post(
            reverse("admin:shop_rzutorder_add"),
            self.admin_data(discount_code=code.code),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Łączny limit użyć")
        self.assertFalse(RzutOrder.objects.exists())
        self.item.refresh_from_db()
        code.refresh_from_db()
        self.assertEqual(self.item.allocated_quantity, 0)
        self.assertEqual(code.allocated_uses, 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_admin_cannot_use_discount_after_email_limit_is_exhausted(self):
        code = DiscountCode.objects.create(
            code="RAZ",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("5.00"),
        )
        create_manual_order(
            data=self.manual_data(discount_code=code.code),
            lines=[ManualOrderLineRequest(self.item.pk, 1)],
        )

        response = self.client.post(
            reverse("admin:shop_rzutorder_add"),
            self.admin_data(discount_code=code.code),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "dla podanego e-maila")
        self.assertEqual(RzutOrder.objects.count(), 1)
        self.item.refresh_from_db()
        code.refresh_from_db()
        self.assertEqual(self.item.allocated_quantity, 1)
        self.assertEqual(code.allocated_uses, 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_admin_cannot_exceed_pool_without_explicitly_increasing_it(self):
        self.item.pool = 1
        self.item.save(update_fields=["pool"])

        response = self.client.post(
            reverse("admin:shop_rzutorder_add"),
            self.admin_data(**{f"quantity_{self.item.pk}": "2"}),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Najpierw jawnie zwiększ jej Pulę")
        self.assertFalse(RzutOrder.objects.exists())
        self.item.refresh_from_db()
        self.assertEqual(self.item.allocated_quantity, 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_admin_keeps_order_items_and_amounts_read_only(self):
        order = create_manual_order(
            data=self.manual_data(),
            lines=[ManualOrderLineRequest(self.item.pk, 1)],
        )

        response = self.client.get(
            reverse("admin:shop_rzutorder_change", args=[order.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chleb wiejski")
        self.assertContains(response, "26,00")
        self.assertNotContains(response, 'name="total"', html=False)
        self.assertNotContains(response, 'name="subtotal"', html=False)
        self.assertNotContains(response, 'name="items-0-product_name"', html=False)
        self.assertNotContains(response, 'name="items-0-quantity"', html=False)

    def test_repeated_admin_post_creates_order_and_email_once(self):
        creation_token = str(uuid.uuid4())
        data = self.admin_data(
            creation_token=creation_token,
            **{f"quantity_{self.item.pk}": "1"},
        )

        first = self.client.post(reverse("admin:shop_rzutorder_add"), data)
        second = self.client.post(reverse("admin:shop_rzutorder_add"), data)

        order = RzutOrder.objects.get()
        self.item.refresh_from_db()
        expected_url = reverse(
            "admin:shop_rzutorder_change",
            args=[order.pk],
        )
        self.assertRedirects(first, expected_url)
        self.assertRedirects(second, expected_url)
        self.assertEqual(RzutOrder.objects.count(), 1)
        self.assertEqual(self.item.allocated_quantity, 1)
        self.assertEqual(len(mail.outbox), 1)


class TestConcurrentManualOrder(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        now = timezone.now()
        self.rzut = OrderEdition.objects.create(
            title="Rzut ostatniej sztuki",
            status=OrderEdition.Status.PUBLISHED,
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(hours=1),
            pickup_date=timezone.localdate() + timedelta(days=1),
            pickup_place_name="Kuchenna Komitywa",
            pickup_address="ul. Bukowa 14, Białystok",
            pickup_starts_at=time(10, 0),
            pickup_ends_at=time(12, 0),
        )
        product = Product.objects.create(
            title="Ostatni chleb",
            description="Chleb na zakwasie.",
            price=Decimal("26.00"),
            default_portion="bochenek",
            is_available_in_shop=False,
        )
        self.item = RzutItem.objects.create(
            rzut=self.rzut,
            product=product,
            price=Decimal("26.00"),
            portion="bochenek",
            pool=1,
        )

    def test_simultaneous_manual_orders_cannot_exceed_pool(self):
        barrier = Barrier(2)

        def attempt(index):
            close_old_connections()
            barrier.wait()
            try:
                create_manual_order(
                    data=ManualOrderData(
                        rzut_id=self.rzut.pk,
                        customer_name=f"Klient {index}",
                        customer_email=f"klient{index}@example.com",
                        customer_phone="",
                        customer_notes="",
                        pickup_slot=PickupSlot(time(10, 0), time(11, 0)),
                        payment_status=RzutOrder.PaymentStatus.PENDING,
                        payment_method=RzutOrder.PaymentMethod.CASH,
                    ),
                    lines=[ManualOrderLineRequest(self.item.pk, 1)],
                )
                return "created"
            except ManualOrderUnavailable:
                return "rejected"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(attempt, range(2)))

        self.item.refresh_from_db()
        self.assertEqual(results.count("created"), 1)
        self.assertEqual(results.count("rejected"), 1)
        self.assertEqual(RzutOrder.objects.count(), 1)
        self.assertEqual(self.item.allocated_quantity, 1)
