from datetime import time, timedelta
from decimal import Decimal
import json
from unittest.mock import patch

from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from shop.emails import send_rzut_order_customer_confirmation
from shop.models import (
    Order,
    OrderEdition,
    Product,
    Reservation,
    RzutItem,
    RzutOrder,
)
from shop.payment import calculate_sign
from shop.reservations import (
    ReservationCheckoutData,
    ReservationLineRequest,
    confirm_reservation,
    create_reservation,
    expire_due_reservations,
)


class RzutOrderTestCase(TestCase):
    def create_reservation(self):
        now = timezone.now()
        rzut = OrderEdition.objects.create(
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
        item = RzutItem.objects.create(
            rzut=rzut,
            product=product,
            price=Decimal("26.00"),
            portion="bochenek ok. 750 g",
            pool=10,
        )
        reservation = create_reservation(
            rzut_id=rzut.pk,
            lines=[ReservationLineRequest(item.pk, 2, item.price)],
            checkout=ReservationCheckoutData(
                name="Jan Kowalski",
                email="jan@example.com",
                phone="+48 500 600 700",
                notes="Odbierze siostra.",
                pickup_starts_at=time(10, 0),
                pickup_ends_at=time(11, 0),
            ),
        )
        return reservation, item


class TestConfirmReservation(RzutOrderTestCase):
    def test_paid_reservation_becomes_separate_rzut_order_with_snapshot(self):
        reservation, item = self.create_reservation()
        confirmed_at = timezone.now()

        order, created = confirm_reservation(
            reservation_id=reservation.pk,
            p24_order_id=987654,
            confirmed_at=confirmed_at,
        )

        reservation.refresh_from_db()
        order_item = order.items.get()
        self.assertTrue(created)
        self.assertEqual(reservation.status, "confirmed")
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(RzutOrder.objects.count(), 1)
        self.assertEqual(order.rzut, reservation.rzut)
        self.assertEqual(order.payment_status, "paid")
        self.assertEqual(order.payment_method, "p24")
        self.assertEqual(order.fulfillment_stage, "new")
        self.assertEqual(order.payment_confirmed_at, confirmed_at)
        self.assertEqual(order.p24_order_id, 987654)
        self.assertEqual(order.total, Decimal("52.00"))
        self.assertTrue(order.number.startswith("KK-"))
        self.assertEqual(order_item.product_name, "Chleb wiejski")
        self.assertEqual(order_item.portion, "bochenek ok. 750 g")
        self.assertEqual(order_item.unit_price, Decimal("26.00"))
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.line_total, Decimal("52.00"))
        item.refresh_from_db()
        self.assertEqual(item.allocated_quantity, 2)

    def test_active_reservation_can_finish_after_rzut_is_closed(self):
        reservation, _ = self.create_reservation()
        reservation.rzut.status = OrderEdition.Status.CLOSED
        reservation.rzut.save(update_fields=["status"])

        order, created = confirm_reservation(
            reservation_id=reservation.pk,
            p24_order_id=987654,
        )

        self.assertTrue(created)
        self.assertEqual(order.payment_status, "paid")

    def test_active_reservation_can_finish_after_rzut_is_paused(self):
        reservation, _ = self.create_reservation()
        reservation.rzut.status = OrderEdition.Status.PAUSED
        reservation.rzut.save(update_fields=["status"])

        order, created = confirm_reservation(
            reservation_id=reservation.pk,
            p24_order_id=987654,
        )

        self.assertTrue(created)
        self.assertEqual(order.payment_status, "paid")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="Kuchenna Komitywa <noreply@example.com>",
    )
    def test_product_changes_do_not_rewrite_order_history_or_email(self):
        reservation, item = self.create_reservation()
        order, _ = confirm_reservation(
            reservation_id=reservation.pk,
            p24_order_id=987654,
        )

        Product.objects.filter(pk=item.product_id).update(
            title="Nowa nazwa",
            is_archived=True,
        )
        RzutItem.objects.filter(pk=item.pk).update(
            portion="nowa Porcja",
            price=Decimal("99.00"),
        )
        send_rzut_order_customer_confirmation(order)

        order_item = order.items.get()
        self.assertEqual(order_item.product_name, "Chleb wiejski")
        self.assertEqual(order_item.portion, "bochenek ok. 750 g")
        self.assertEqual(order_item.unit_price, Decimal("26.00"))
        self.assertIn("Chleb wiejski", mail.outbox[0].body)
        self.assertIn("bochenek ok. 750 g", mail.outbox[0].body)
        self.assertNotIn("Nowa nazwa", mail.outbox[0].body)


@override_settings(
    P24_MERCHANT_ID=12345,
    P24_POS_ID=12345,
    P24_CRC_KEY="testcrc",
    P24_API_KEY="testapikey",
    P24_SANDBOX=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="Kuchenna Komitywa <noreply@example.com>",
    CONTACT_EMAIL="owner@example.com",
    PUBLIC_SITE_URL="https://example.com",
)
class TestRzutP24Webhook(RzutOrderTestCase):
    def setUp(self):
        self.reservation, self.item = self.create_reservation()

    def payload(self, **overrides):
        values = {
            "merchantId": 12345,
            "posId": 12345,
            "sessionId": self.reservation.p24_session_id,
            "amount": 5200,
            "originAmount": 5200,
            "currency": "PLN",
            "orderId": 987654,
            "methodId": 25,
            "statement": "Kuchenna Komitywa",
        }
        values.update(overrides)
        values["sign"] = calculate_sign({
            "merchantId": values["merchantId"],
            "posId": values["posId"],
            "sessionId": values["sessionId"],
            "amount": values["amount"],
            "originAmount": values["originAmount"],
            "currency": values["currency"],
            "orderId": values["orderId"],
            "methodId": values["methodId"],
            "statement": values["statement"],
            "crc": settings.P24_CRC_KEY,
        })
        return values

    @patch("shop.views.verify_transaction", return_value=True)
    def test_verified_payment_creates_order_and_sends_both_emails(
        self,
        verify_payment,
    ):
        response = self.client.post(
            reverse("shop:rzut_p24_webhook"),
            data=json.dumps(self.payload()),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200, response.content)
        order = RzutOrder.objects.get()
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, "confirmed")
        self.assertEqual(order.p24_order_id, 987654)
        self.assertIsNotNone(order.customer_confirmation_sent_at)
        self.assertIsNotNone(order.owner_notification_sent_at)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to, ["jan@example.com"])
        self.assertEqual(mail.outbox[1].to, ["owner@example.com"])
        self.assertIn(order.number, mail.outbox[0].body)
        self.assertIn("Rzut niedzielny", mail.outbox[0].body)
        self.assertIn("Chleb wiejski", mail.outbox[0].body)
        self.assertIn("bochenek ok. 750 g", mail.outbox[0].body)
        self.assertIn("52,00 zł", mail.outbox[0].body)
        self.assertIn("10:00–11:00", mail.outbox[0].body)
        self.assertIn("Odbierze siostra.", mail.outbox[0].body)
        self.assertIn(
            f"https://example.com/zamowienia/zamowienie/{order.number}/",
            mail.outbox[0].body,
        )
        self.assertIn(order.number, mail.outbox[1].body)
        verify_payment.assert_called_once_with(
            self.reservation.p24_session_id,
            987654,
            5200,
        )

    @patch("shop.views.verify_transaction", return_value=True)
    def test_repeated_webhook_does_not_duplicate_order_pool_or_emails(
        self,
        verify_payment,
    ):
        payload = json.dumps(self.payload())

        first = self.client.post(
            reverse("shop:rzut_p24_webhook"),
            data=payload,
            content_type="application/json",
        )
        second = self.client.post(
            reverse("shop:rzut_p24_webhook"),
            data=payload,
            content_type="application/json",
        )

        self.item.refresh_from_db()
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(
            first.json()["orderNumber"],
            second.json()["orderNumber"],
        )
        self.assertEqual(RzutOrder.objects.count(), 1)
        self.assertEqual(RzutOrder.objects.get().items.count(), 1)
        self.assertEqual(self.item.allocated_quantity, 2)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(verify_payment.call_count, 2)

    @patch("shop.views.verify_transaction", return_value=True)
    def test_late_payment_creates_order_and_raises_overallocation_alert(
        self,
        verify_payment,
    ):
        RzutItem.objects.filter(pk=self.item.pk).update(pool=2)
        expire_due_reservations(now=self.reservation.expires_at)
        create_reservation(
            rzut_id=self.reservation.rzut_id,
            lines=[ReservationLineRequest(self.item.pk, 2, self.item.price)],
            checkout=ReservationCheckoutData(
                name="Anna Nowak",
                email="anna@example.com",
                phone="",
                notes="",
                pickup_starts_at=time(10, 0),
                pickup_ends_at=time(11, 0),
            ),
        )

        with self.assertLogs("shop.reservations", level="CRITICAL") as logs:
            response = self.client.post(
                reverse("shop:rzut_p24_webhook"),
                data=json.dumps(self.payload()),
                content_type="application/json",
            )

        self.reservation.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.reservation.status, "confirmed")
        self.assertEqual(RzutOrder.objects.count(), 1)
        order = RzutOrder.objects.get()
        self.assertTrue(order.requires_attention)
        self.assertIn("Przekroczenie Puli", order.attention_message)
        self.assertIsNotNone(order.attention_notification_sent_at)
        self.assertEqual(self.item.allocated_quantity, 4)
        self.assertEqual(self.item.available_quantity, -2)
        self.assertIn("PILNE", " ".join(logs.output))
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(mail.outbox[2].to, ["owner@example.com"])
        self.assertIn("PILNE", mail.outbox[2].subject)
        verify_payment.assert_called_once()

    @patch("shop.views.verify_transaction", return_value=True)
    def test_overdue_active_payment_is_alerted_without_reallocating_pool(
        self,
        verify_payment,
    ):
        Reservation.objects.filter(pk=self.reservation.pk).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )

        with self.assertLogs("shop.reservations", level="CRITICAL"):
            response = self.client.post(
                reverse("shop:rzut_p24_webhook"),
                data=json.dumps(self.payload()),
                content_type="application/json",
            )

        order = RzutOrder.objects.get()
        self.item.refresh_from_db()
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(order.requires_attention)
        self.assertIn("Późna płatność", order.attention_message)
        self.assertEqual(self.item.allocated_quantity, 2)
        self.assertEqual(len(mail.outbox), 3)
        verify_payment.assert_called_once()

    @patch("shop.emails.EmailMessage.send")
    @patch("shop.views.verify_transaction", return_value=True)
    def test_late_alert_email_failure_does_not_roll_back_order(
        self,
        verify_payment,
        send_email,
    ):
        Reservation.objects.filter(pk=self.reservation.pk).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        send_email.side_effect = [1, 1, RuntimeError("SMTP niedostępne")]

        with self.assertLogs("shop.reservations", level="CRITICAL"):
            response = self.client.post(
                reverse("shop:rzut_p24_webhook"),
                data=json.dumps(self.payload()),
                content_type="application/json",
            )

        order = RzutOrder.objects.get()
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(order.payment_status, "paid")
        self.assertTrue(order.requires_attention)
        self.assertIsNone(order.attention_notification_sent_at)
        self.assertIn("SMTP niedostępne", order.attention_notification_error)
        self.assertEqual(send_email.call_count, 3)
        verify_payment.assert_called_once()

    @patch("shop.views.verify_transaction")
    def test_invalid_signature_is_rejected_before_p24_verification(
        self,
        verify_payment,
    ):
        payload = self.payload()
        payload["sign"] = "invalid"

        response = self.client.post(
            reverse("shop:rzut_p24_webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(RzutOrder.objects.exists())
        verify_payment.assert_not_called()

    @patch("shop.views.verify_transaction", return_value=False)
    def test_payment_rejected_by_p24_does_not_create_order(
        self,
        verify_payment,
    ):
        response = self.client.post(
            reverse("shop:rzut_p24_webhook"),
            data=json.dumps(self.payload()),
            content_type="application/json",
        )

        self.reservation.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.reservation.status, "active")
        self.assertFalse(RzutOrder.objects.exists())

    @patch("shop.views.verify_transaction")
    def test_mismatched_amount_is_rejected_before_p24_verification(
        self,
        verify_payment,
    ):
        response = self.client.post(
            reverse("shop:rzut_p24_webhook"),
            data=json.dumps(self.payload(amount=5100)),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(RzutOrder.objects.exists())
        verify_payment.assert_not_called()

    @patch("shop.emails.EmailMessage.send")
    @patch("shop.views.verify_transaction", return_value=True)
    def test_email_failure_is_recorded_without_rolling_back_payment(
        self,
        verify_payment,
        send_email,
    ):
        send_email.side_effect = [RuntimeError("SMTP niedostępne"), 1]
        payload = json.dumps(self.payload())

        first = self.client.post(
            reverse("shop:rzut_p24_webhook"),
            data=payload,
            content_type="application/json",
        )
        second = self.client.post(
            reverse("shop:rzut_p24_webhook"),
            data=payload,
            content_type="application/json",
        )

        order = RzutOrder.objects.get()
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(order.payment_status, "paid")
        self.assertIn("SMTP niedostępne", order.customer_confirmation_error)
        self.assertIsNone(order.customer_confirmation_sent_at)
        self.assertIsNotNone(order.owner_notification_sent_at)
        self.assertEqual(send_email.call_count, 2)

    def test_webhook_does_not_change_state_via_get(self):
        response = self.client.get(reverse("shop:rzut_p24_webhook"))

        self.assertEqual(response.status_code, 405)
        self.assertFalse(RzutOrder.objects.exists())

    def test_non_object_json_is_rejected(self):
        response = self.client.post(
            reverse("shop:rzut_p24_webhook"),
            data="[]",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(RzutOrder.objects.exists())


class TestRzutOrderPublicPages(RzutOrderTestCase):
    def setUp(self):
        self.reservation, self.item = self.create_reservation()

    def return_url(self):
        return (
            reverse("shop:rzut_p24_return")
            + f"?session={self.reservation.p24_session_id}"
        )

    def test_return_waits_before_webhook_and_shows_success_after_it(self):
        waiting = self.client.get(self.return_url())

        self.assertEqual(waiting.status_code, 200)
        self.assertContains(waiting, "Sprawdzamy płatność")
        self.assertNotContains(waiting, "Płatność potwierdzona")

        order, _ = confirm_reservation(
            reservation_id=self.reservation.pk,
            p24_order_id=987654,
        )
        confirmed = self.client.get(self.return_url())

        self.assertEqual(confirmed.status_code, 200)
        self.assertContains(confirmed, "Płatność potwierdzona")
        self.assertContains(confirmed, order.number)
        self.assertContains(
            confirmed,
            reverse("shop:rzut_order_detail", args=[order.number]),
        )

    def test_public_order_page_uses_number_and_masks_contact_data(self):
        order, _ = confirm_reservation(
            reservation_id=self.reservation.pk,
            p24_order_id=987654,
        )

        response = self.client.get(
            reverse("shop:rzut_order_detail", args=[order.number])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, order.number)
        self.assertContains(response, "Chleb wiejski")
        self.assertContains(response, "bochenek ok. 750 g")
        self.assertContains(response, "Opłacona")
        self.assertContains(response, "Nowe")
        self.assertContains(response, "j***@example.com")
        self.assertContains(response, "*** *** 700")
        self.assertNotContains(response, "jan@example.com")
        self.assertNotContains(response, "+48 500 600 700")
        self.assertNotContains(response, "Jan Kowalski")
        self.assertNotContains(response, "<form", html=False)

        predictable = self.client.get(
            f"/zamowienia/zamowienie/{order.pk}/"
        )
        self.assertEqual(predictable.status_code, 404)

    def test_unknown_payment_session_and_order_number_return_404(self):
        missing_session = self.client.get(reverse("shop:rzut_p24_return"))
        unknown_session = self.client.get(
            reverse("shop:rzut_p24_return") + "?session=rzut-unknown"
        )
        unknown_order = self.client.get(
            reverse("shop:rzut_order_detail", args=["KK-UNKNOWN"])
        )

        self.assertEqual(missing_session.status_code, 404)
        self.assertEqual(unknown_session.status_code, 404)
        self.assertEqual(unknown_order.status_code, 404)
