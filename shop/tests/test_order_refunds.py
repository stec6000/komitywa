from datetime import time, timedelta
from decimal import Decimal
from unittest.mock import patch

import requests
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from shop.models import (
    DiscountCode,
    OrderEdition,
    Product,
    Reservation,
    RzutItem,
    RzutOrder,
    RzutOrderItem,
)


@override_settings(
    P24_MERCHANT_ID=12345,
    P24_POS_ID=12345,
    P24_API_KEY="testapikey",
    P24_SANDBOX=True,
    P24_HTTP_TIMEOUT=(3.05, 10),
)
class TestRzutOrderRefundAdmin(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser(
            email="zwroty@example.com",
            password="testpass123",
        )
        cls.rzut = OrderEdition.objects.create(
            title="Rzut niedzielny",
            pickup_date=timezone.localdate() + timedelta(days=2),
            pickup_place_name="Kuchenna Komitywa",
            pickup_address="ul. Bukowa 14, Białystok",
            pickup_starts_at=time(10, 0),
            pickup_ends_at=time(13, 0),
            pickup_instructions="Wejście od ogrodu.",
        )
        product = Product.objects.create(
            title="Chleb wiejski",
            description="Chleb na zakwasie.",
            price=Decimal("24.00"),
            default_portion="bochenek",
            is_available_in_shop=False,
        )
        cls.rzut_item = RzutItem.objects.create(
            rzut=cls.rzut,
            product=product,
            price=Decimal("24.00"),
            portion="bochenek",
            pool=10,
            allocated_quantity=2,
        )

    def setUp(self):
        self.client.force_login(self.admin_user)
        now = timezone.now()
        reservation = Reservation.objects.create(
            rzut=self.rzut,
            status=Reservation.Status.CONFIRMED,
            customer_name="Jan Kowalski",
            customer_email="jan@example.com",
            pickup_starts_at=time(10, 0),
            pickup_ends_at=time(11, 0),
            subtotal=Decimal("48.00"),
            total=Decimal("48.00"),
            data_processing_accepted_at=now,
            terms_accepted_at=now,
            terms_version="2026-08-19-rzuty-v1",
            expires_at=now + timedelta(minutes=15),
        )
        self.order = RzutOrder.objects.create(
            reservation=reservation,
            rzut=self.rzut,
            customer_name="Jan Kowalski",
            customer_email="jan@example.com",
            pickup_starts_at=time(10, 0),
            pickup_ends_at=time(11, 0),
            subtotal=Decimal("48.00"),
            total=Decimal("48.00"),
            payment_status=RzutOrder.PaymentStatus.PAID,
            payment_method=RzutOrder.PaymentMethod.P24,
            p24_session_id=reservation.p24_session_id,
            p24_order_id=987654,
            payment_confirmed_at=now,
        )
        RzutOrderItem.objects.create(
            order=self.order,
            rzut_item=self.rzut_item,
            product_name="Chleb wiejski",
            portion="bochenek",
            unit_price=Decimal("24.00"),
            quantity=2,
            line_total=Decimal("48.00"),
        )

    def action_url(self):
        return reverse("admin:shop_rzutorder_changelist")

    def change_url(self):
        return reverse("admin:shop_rzutorder_change", args=[self.order.pk])

    def change_data(self, **overrides):
        data = {
            "customer_name": self.order.customer_name,
            "customer_email": self.order.customer_email,
            "customer_phone": self.order.customer_phone,
            "customer_notes": self.order.customer_notes,
            "pickup_slot": "10:00:00|11:00:00",
            "internal_note": "",
            "payment_status": self.order.payment_status,
            "fulfillment_stage": self.order.fulfillment_stage,
            "items-TOTAL_FORMS": "1",
            "items-INITIAL_FORMS": "1",
            "items-MIN_NUM_FORMS": "0",
            "items-MAX_NUM_FORMS": "0",
            "items-0-id": str(self.order.items.get().pk),
            "events-TOTAL_FORMS": "0",
            "events-INITIAL_FORMS": "0",
            "events-MIN_NUM_FORMS": "0",
            "events-MAX_NUM_FORMS": "0",
            "_continue": "Zapisz i kontynuuj edycję",
        }
        data.update(overrides)
        return data

    def test_refund_action_previews_order_amount_and_pool_decision(self):
        response = self.client.post(
            self.action_url(),
            {
                "action": "refund_p24_payment",
                "_selected_action": [str(self.order.pk)],
                "index": "0",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Potwierdź pełny zwrot Przelewy24")
        self.assertContains(response, self.order.number)
        self.assertContains(response, "48,00")
        self.assertContains(response, "Przywróć sztuki do Puli")
        self.assertContains(response, "Nie przywracaj sztuk")
        self.assertNotContains(response, 'name="amount"')

    @patch("shop.fulfillment.get_rzut_refund")
    @patch("shop.fulfillment.refund_rzut_transaction")
    def test_successful_full_refund_cancels_and_restores_pool_with_audit(
        self, refund_transaction, get_refund
    ):
        refund_transaction.return_value = {
            "orderId": 987654,
            "sessionId": self.order.p24_session_id,
            "amount": 4800,
            "status": True,
            "completed": False,
            "message": "success",
        }

        confirmation = {
            "action": "refund_p24_payment",
            "_selected_action": [str(self.order.pk)],
            "confirm_refund": "1",
            "restore_pool": "1",
        }

        requested = self.client.post(
            self.action_url(), confirmation, follow=True
        )

        self.order.refresh_from_db()
        self.rzut_item.refresh_from_db()
        self.assertContains(requested, "Zlecenie pełnego zwrotu zostało przyjęte")
        self.assertEqual(
            self.order.payment_status, RzutOrder.PaymentStatus.PAID
        )
        self.assertEqual(
            self.order.fulfillment_stage, RzutOrder.FulfillmentStage.NEW
        )
        self.assertEqual(self.rzut_item.allocated_quantity, 2)
        get_refund.return_value = {
            "orderId": 987654,
            "sessionId": self.order.p24_session_id,
            "amount": 4800,
            "status": True,
            "completed": True,
            "refundStatus": 1,
            "requestId": self.order.p24_refund_request_id,
        }

        response = self.client.post(
            self.action_url(), confirmation, follow=True
        )

        self.order.refresh_from_db()
        self.rzut_item.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pełny zwrot Przelewy24 został przyjęty")
        self.assertEqual(
            self.order.payment_status, RzutOrder.PaymentStatus.REFUNDED
        )
        self.assertEqual(
            self.order.fulfillment_stage,
            RzutOrder.FulfillmentStage.CANCELLED,
        )
        self.assertIsNotNone(self.order.p24_refunded_at)
        self.assertEqual(self.order.p24_refund_error, "")
        self.assertTrue(self.order.p24_refund_result["status"])
        self.assertEqual(self.rzut_item.allocated_quantity, 0)
        self.assertEqual(self.rzut_item.withdrawn_quantity, 0)
        refund_transaction.assert_called_once()
        get_refund.assert_called_once()
        refund_event = self.order.events.get(kind="refund_succeeded")
        self.assertEqual(refund_event.context["amount"], "48.00")
        self.assertTrue(refund_event.context["pool_restored"])

    @patch("shop.fulfillment.get_rzut_refund")
    @patch("shop.fulfillment.refund_rzut_transaction")
    def test_failed_refund_preserves_state_and_retry_keeps_quantity_withdrawn(
        self, refund_transaction, get_refund
    ):
        refund_transaction.side_effect = requests.Timeout(
            "Przekroczono czas odpowiedzi P24"
        )
        get_refund.side_effect = [
            {
                "orderId": 987654,
                "sessionId": self.order.p24_session_id,
                "amount": 4800,
                "status": True,
                "completed": False,
                "refundStatus": 2,
                "requestId": "filled-after-first-attempt",
            },
            {
                "orderId": 987654,
                "sessionId": self.order.p24_session_id,
                "amount": 4800,
                "status": True,
                "completed": True,
                "refundStatus": 1,
                "requestId": "filled-after-first-attempt",
            },
        ]
        confirmation = {
            "action": "refund_p24_payment",
            "_selected_action": [str(self.order.pk)],
            "confirm_refund": "1",
            "restore_pool": "0",
        }

        failed = self.client.post(self.action_url(), confirmation, follow=True)

        self.order.refresh_from_db()
        self.rzut_item.refresh_from_db()
        first_request_id = self.order.p24_refund_request_id
        first_refunds_uuid = self.order.p24_refunds_uuid
        self.assertContains(failed, "Przekroczono czas odpowiedzi P24")
        self.assertContains(failed, "Błąd pełnego zwrotu P24")
        self.assertContains(failed, first_request_id)
        self.assertEqual(
            self.order.payment_status, RzutOrder.PaymentStatus.PAID
        )
        self.assertEqual(
            self.order.fulfillment_stage, RzutOrder.FulfillmentStage.NEW
        )
        self.assertEqual(self.rzut_item.allocated_quantity, 2)
        self.assertEqual(self.rzut_item.withdrawn_quantity, 0)
        self.assertEqual(
            self.order.p24_refund_error,
            "Przekroczono czas odpowiedzi P24",
        )
        failed_event = self.order.events.get(kind="refund_failed")
        self.assertFalse(failed_event.context["requested_pool_restore"])
        self.assertIsNone(failed_event.context["pool_restored"])

        pending = self.client.post(self.action_url(), confirmation, follow=True)

        self.order.refresh_from_db()
        self.rzut_item.refresh_from_db()
        self.assertContains(pending, "Zwrot oczekuje na zakończenie w Przelewy24")
        self.assertEqual(
            self.order.payment_status, RzutOrder.PaymentStatus.PAID
        )
        self.assertEqual(
            self.order.fulfillment_stage, RzutOrder.FulfillmentStage.NEW
        )
        self.assertEqual(self.rzut_item.allocated_quantity, 2)

        retried = self.client.post(self.action_url(), confirmation, follow=True)

        self.order.refresh_from_db()
        self.rzut_item.refresh_from_db()
        self.assertContains(retried, "Pełny zwrot Przelewy24 został przyjęty")
        self.assertEqual(self.order.p24_refund_request_id, first_request_id)
        self.assertEqual(self.order.p24_refunds_uuid, first_refunds_uuid)
        refund_transaction.assert_called_once()
        self.assertEqual(get_refund.call_count, 2)
        self.assertEqual(
            self.order.payment_status, RzutOrder.PaymentStatus.REFUNDED
        )
        self.assertEqual(
            self.order.fulfillment_stage,
            RzutOrder.FulfillmentStage.CANCELLED,
        )
        self.assertEqual(self.order.p24_refund_error, "")
        self.assertEqual(self.rzut_item.allocated_quantity, 0)
        self.assertEqual(self.rzut_item.withdrawn_quantity, 2)
        self.assertEqual(
            self.order.events.filter(kind="refund_failed").count(), 1
        )
        self.assertEqual(
            self.order.events.filter(kind="refund_succeeded").count(), 1
        )

    @patch("shop.fulfillment.refund_rzut_transaction")
    def test_cancellation_does_not_refund_and_repeated_post_is_idempotent(
        self, refund_transaction
    ):
        data = self.change_data(
            fulfillment_stage=RzutOrder.FulfillmentStage.CANCELLED,
            confirm_cancellation="1",
            restore_pool="1",
        )

        first = self.client.post(self.change_url(), data, follow=True)
        second = self.client.post(self.change_url(), data, follow=True)

        self.order.refresh_from_db()
        self.rzut_item.refresh_from_db()
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        refund_transaction.assert_not_called()
        self.assertEqual(
            self.order.payment_status, RzutOrder.PaymentStatus.PAID
        )
        self.assertEqual(
            self.order.fulfillment_stage,
            RzutOrder.FulfillmentStage.CANCELLED,
        )
        self.assertEqual(self.rzut_item.allocated_quantity, 0)
        self.assertEqual(self.rzut_item.withdrawn_quantity, 0)
        self.assertEqual(
            self.order.events.filter(kind="fulfillment_stage_changed").count(),
            1,
        )

    @patch("shop.fulfillment.get_rzut_refund")
    @patch("shop.fulfillment.refund_rzut_transaction")
    def test_refund_can_restore_quantity_kept_out_by_earlier_cancellation(
        self, refund_transaction, get_refund
    ):
        cancellation = self.change_data(
            fulfillment_stage=RzutOrder.FulfillmentStage.CANCELLED,
            confirm_cancellation="1",
            restore_pool="0",
        )
        self.client.post(self.change_url(), cancellation)
        self.order.refresh_from_db()
        self.rzut_item.refresh_from_db()
        self.assertFalse(self.order.cancelled_quantity_restored)
        self.assertEqual(self.rzut_item.withdrawn_quantity, 2)
        RzutOrder.objects.filter(pk=self.order.pk).update(
            cancelled_quantity_restored=None
        )
        self.order.refresh_from_db()

        refund_transaction.return_value = {
            "orderId": 987654,
            "sessionId": self.order.p24_session_id,
            "amount": 4800,
            "status": True,
            "completed": False,
            "message": "success",
        }
        refund_confirmation = {
            "action": "refund_p24_payment",
            "_selected_action": [str(self.order.pk)],
            "confirm_refund": "1",
            "restore_pool": "1",
        }
        self.client.post(self.action_url(), refund_confirmation)
        get_refund.return_value = {
            "orderId": 987654,
            "sessionId": self.order.p24_session_id,
            "amount": 4800,
            "status": True,
            "completed": True,
            "refundStatus": 1,
            "requestId": self.order.p24_refund_request_id,
        }

        response = self.client.post(
            self.action_url(), refund_confirmation, follow=True
        )

        self.order.refresh_from_db()
        self.rzut_item.refresh_from_db()
        self.assertContains(response, "Pełny zwrot Przelewy24 został przyjęty")
        self.assertTrue(self.order.cancelled_quantity_restored)
        self.assertEqual(self.rzut_item.allocated_quantity, 0)
        self.assertEqual(self.rzut_item.withdrawn_quantity, 0)
        event = self.order.events.get(kind="refund_succeeded")
        self.assertTrue(event.context["requested_pool_restore"])
        self.assertTrue(event.context["pool_restored"])

    @patch("shop.fulfillment.get_rzut_refund")
    @patch("shop.fulfillment.refund_rzut_transaction")
    def test_confirmed_financial_refund_survives_local_pool_error(
        self, refund_transaction, get_refund
    ):
        refund_transaction.return_value = {
            "orderId": 987654,
            "sessionId": self.order.p24_session_id,
            "amount": 4800,
            "status": True,
            "completed": False,
            "message": "success",
        }
        confirmation = {
            "action": "refund_p24_payment",
            "_selected_action": [str(self.order.pk)],
            "confirm_refund": "1",
            "restore_pool": "1",
        }
        self.client.post(self.action_url(), confirmation)
        self.order.refresh_from_db()
        get_refund.return_value = {
            "orderId": 987654,
            "sessionId": self.order.p24_session_id,
            "amount": 4800,
            "status": True,
            "completed": True,
            "refundStatus": 1,
            "requestId": self.order.p24_refund_request_id,
        }
        RzutItem.objects.filter(pk=self.rzut_item.pk).update(
            allocated_quantity=0
        )

        response = self.client.post(
            self.action_url(), confirmation, follow=True
        )

        self.order.refresh_from_db()
        self.assertContains(
            response,
            "rozliczenie Puli i anulowanie realizacji wymaga pilnej uwagi",
        )
        self.assertEqual(
            self.order.payment_status, RzutOrder.PaymentStatus.REFUNDED
        )
        self.assertEqual(
            self.order.fulfillment_stage,
            RzutOrder.FulfillmentStage.NEW,
        )
        self.assertTrue(self.order.requires_attention)
        self.assertIn(
            "Przelewy24 potwierdziło pełny zwrot",
            self.order.attention_message,
        )
        self.assertTrue(self.order.p24_refund_result["completed"])
        event = self.order.events.get(kind="refund_succeeded")
        self.assertIn("Nie można zwolnić Puli", event.context["allocation_error"])
        self.assertIsNone(event.context["pool_restored"])

    @patch("shop.fulfillment.refund_rzut_transaction")
    def test_refund_action_rejects_non_p24_order(self, refund_transaction):
        self.order.payment_method = RzutOrder.PaymentMethod.CASH
        self.order.save(update_fields=["payment_method"])

        response = self.client.post(
            self.action_url(),
            {
                "action": "refund_p24_payment",
                "_selected_action": [str(self.order.pk)],
                "index": "0",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "nie kwalifikuje się")
        refund_transaction.assert_not_called()
        self.order.refresh_from_db()
        self.assertEqual(
            self.order.payment_status, RzutOrder.PaymentStatus.PAID
        )

    @patch("shop.fulfillment.get_rzut_refund")
    @patch("shop.fulfillment.refund_rzut_transaction")
    def test_refund_does_not_restore_confirmed_discount_use(
        self, refund_transaction, get_refund
    ):
        code = DiscountCode.objects.create(
            code="RAZ",
            discount_type=DiscountCode.Type.FIXED_AMOUNT,
            value=Decimal("5.00"),
            allocated_uses=1,
        )
        self.order.discount_code = code
        self.order.discount_code_snapshot = code.code
        self.order.discount_amount = Decimal("5.00")
        self.order.save(
            update_fields=[
                "discount_code",
                "discount_code_snapshot",
                "discount_amount",
            ]
        )
        refund_transaction.return_value = {
            "orderId": 987654,
            "sessionId": self.order.p24_session_id,
            "amount": 4800,
            "status": True,
            "completed": False,
            "message": "success",
        }

        self.client.post(
            self.action_url(),
            {
                "action": "refund_p24_payment",
                "_selected_action": [str(self.order.pk)],
                "confirm_refund": "1",
                "restore_pool": "1",
            },
        )
        self.order.refresh_from_db()
        get_refund.return_value = {
            "orderId": 987654,
            "sessionId": self.order.p24_session_id,
            "amount": 4800,
            "status": True,
            "completed": True,
            "refundStatus": 1,
            "requestId": self.order.p24_refund_request_id,
        }
        self.client.post(
            self.action_url(),
            {
                "action": "refund_p24_payment",
                "_selected_action": [str(self.order.pk)],
                "confirm_refund": "1",
                "restore_pool": "1",
            },
        )

        code.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(
            self.order.payment_status, RzutOrder.PaymentStatus.REFUNDED
        )
        self.assertEqual(code.allocated_uses, 1)
