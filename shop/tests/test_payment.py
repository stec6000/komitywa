import hashlib
import json
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase, override_settings

from shop.models import Order, ProductCategory


@override_settings(
    P24_MERCHANT_ID=12345,
    P24_POS_ID=12345,
    P24_CRC_KEY="testcrc",
    P24_API_KEY="testapikey",
    P24_SANDBOX=True,
)
class TestCalculateSign(TestCase):
    def test_produces_sha384_hex_digest(self):
        from shop.payment import calculate_sign

        params = {
            "sessionId": "test-123",
            "merchantId": 12345,
            "amount": 1000,
            "currency": "PLN",
            "crc": "abc",
        }
        result = calculate_sign(params)
        # SHA-384 hex digest is 96 characters
        self.assertEqual(len(result), 96)

    def test_deterministic_output(self):
        from shop.payment import calculate_sign

        params = {
            "sessionId": "test-123",
            "merchantId": 12345,
            "amount": 1000,
            "currency": "PLN",
            "crc": "abc",
        }
        expected = hashlib.sha384(
            json.dumps(params, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        result = calculate_sign(params)
        self.assertEqual(result, expected)


@override_settings(
    P24_MERCHANT_ID=12345,
    P24_POS_ID=12345,
    P24_CRC_KEY="testcrc",
    P24_API_KEY="testapikey",
    P24_SANDBOX=True,
)
class TestRegisterTransaction(TestCase):
    def setUp(self):
        self.category, _ = ProductCategory.objects.get_or_create(
            slug="test-cat", defaults={"name": "Test"}
        )
        self.order = Order.objects.create(
            email="test@example.com",
            name="Jan Kowalski",
            pickup_date="piatek",
            total=Decimal("29.99"),
            cart_snapshot={"1": {"quantity": 1, "price": "29.99"}},
            p24_session_id="order-1-abc",
        )

    @patch("shop.payment.requests.post")
    def test_calls_post_with_correct_url(self, mock_post):
        from shop.payment import register_transaction

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"token": "test-token"}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        token = register_transaction(
            self.order,
            "http://localhost/return",
            "http://localhost/webhook",
        )

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn(
            "/api/v1/transaction/register", call_args[0][0]
        )
        self.assertEqual(call_args[1]["json"]["sessionId"], "order-1-abc")
        self.assertEqual(call_args[1]["json"]["amount"], 2999)
        self.assertEqual(call_args[1]["timeout"], (3.05, 10))
        self.assertEqual(token, "test-token")


@override_settings(
    P24_MERCHANT_ID=12345,
    P24_POS_ID=12345,
    P24_CRC_KEY="testcrc",
    P24_API_KEY="testapikey",
    P24_SANDBOX=True,
    P24_HTTP_TIMEOUT=(3.05, 10),
)
class TestRegisterRzutTransaction(TestCase):
    def setUp(self):
        self.reservation = SimpleNamespace(
            p24_session_id="rzut-abc123",
            total=Decimal("29.99"),
            customer_email="jan@example.com",
            rzut=SimpleNamespace(title="Rzut niedzielny"),
        )

    @patch("shop.payment.requests.post")
    def test_sends_15_minute_rzut_payment_contract(self, mock_post):
        from shop.payment import calculate_sign, register_rzut_transaction

        response = MagicMock()
        response.json.return_value = {"data": {"token": "rzut-token"}}
        mock_post.return_value = response

        token = register_rzut_transaction(
            self.reservation,
            "https://example.com/zamowienia/powrot/?session=rzut-abc123",
            "https://example.com/zamowienia/webhook/p24/",
        )

        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(token, "rzut-token")
        self.assertEqual(payload["sessionId"], "rzut-abc123")
        self.assertEqual(payload["amount"], 2999)
        self.assertEqual(payload["timeLimit"], 15)
        self.assertEqual(payload["email"], "jan@example.com")
        self.assertEqual(
            payload["urlReturn"],
            "https://example.com/zamowienia/powrot/?session=rzut-abc123",
        )
        self.assertEqual(
            payload["urlStatus"],
            "https://example.com/zamowienia/webhook/p24/",
        )
        self.assertEqual(mock_post.call_args.kwargs["timeout"], (3.05, 10))
        self.assertEqual(
            payload["sign"],
            calculate_sign({
                "sessionId": "rzut-abc123",
                "merchantId": 12345,
                "amount": 2999,
                "currency": "PLN",
                "crc": "testcrc",
            }),
        )

    @patch("shop.payment.requests.post", side_effect=requests.Timeout)
    def test_timeout_is_not_retried_blindly(self, mock_post):
        from shop.payment import register_rzut_transaction

        with self.assertRaises(requests.Timeout):
            register_rzut_transaction(
                self.reservation,
                "https://example.com/return/",
                "https://example.com/status/",
            )

        mock_post.assert_called_once()


@override_settings(
    P24_MERCHANT_ID=12345,
    P24_POS_ID=12345,
    P24_CRC_KEY="testcrc",
    P24_API_KEY="testapikey",
    P24_SANDBOX=True,
)
class TestVerifyTransaction(TestCase):
    @patch("shop.payment.requests.put")
    def test_calls_put_with_correct_url(self, mock_put):
        from shop.payment import verify_transaction

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {"status": "success"}
        }
        mock_response.raise_for_status = MagicMock()
        mock_put.return_value = mock_response

        result = verify_transaction("session-1", 12345, 1000)

        mock_put.assert_called_once()
        call_args = mock_put.call_args
        self.assertIn(
            "/api/v1/transaction/verify", call_args[0][0]
        )
        self.assertEqual(call_args[1]["timeout"], (3.05, 10))
        self.assertTrue(result)


@override_settings(
    P24_MERCHANT_ID=12345,
    P24_POS_ID=12345,
    P24_API_KEY="testapikey",
    P24_SANDBOX=True,
    P24_HTTP_TIMEOUT=(3.05, 10),
)
class TestRefundRzutTransaction(TestCase):
    def refund_request(self, **overrides):
        from shop.payment import P24RefundRequest

        values = {
            "p24_order_id": 987654,
            "p24_session_id": "rzut-session-1",
            "amount": Decimal("48.99"),
            "request_id": "refund-request-1",
            "refunds_uuid": "refunds-uuid-1",
            "description": "Zwrot KK ABC123",
        }
        values.update(overrides)
        return P24RefundRequest(**values)

    @patch("shop.payment.requests.post")
    def test_requests_full_refund_with_stable_identifiers(self, mock_post):
        from shop.payment import refund_rzut_transaction

        response = MagicMock()
        response.json.return_value = {
            "data": [
                {
                    "orderId": 987654,
                    "sessionId": "rzut-session-1",
                    "amount": 4899,
                    "status": True,
                    "message": "success",
                }
            ],
            "responseCode": 0,
        }
        mock_post.return_value = response

        result = refund_rzut_transaction(self.refund_request())

        self.assertEqual(result["message"], "success")
        self.assertFalse(result["completed"])
        mock_post.assert_called_once_with(
            "https://sandbox.przelewy24.pl/api/v1/transaction/refund",
            json={
                "requestId": "refund-request-1",
                "refundsUuid": "refunds-uuid-1",
                "refunds": [
                    {
                        "orderId": 987654,
                        "sessionId": "rzut-session-1",
                        "amount": 4899,
                        "description": "Zwrot KK ABC123",
                    }
                ],
            },
            auth=("12345", "testapikey"),
            timeout=(3.05, 10),
        )

    @patch("shop.payment.requests.post")
    def test_raises_when_p24_rejects_refund_in_successful_http_response(
        self, mock_post
    ):
        from shop.payment import P24RefundError, refund_rzut_transaction

        response = MagicMock()
        response.json.return_value = {
            "data": [
                {
                    "orderId": 987654,
                    "sessionId": "rzut-session-1",
                    "amount": 4899,
                    "status": False,
                    "message": "Insufficient funds available",
                }
            ],
            "responseCode": 0,
        }
        mock_post.return_value = response

        with self.assertRaisesMessage(
            P24RefundError, "Insufficient funds available"
        ):
            refund_rzut_transaction(self.refund_request())

    @patch("shop.payment.requests.post")
    def test_rejects_success_response_for_different_refund(self, mock_post):
        from shop.payment import P24RefundError, refund_rzut_transaction

        response = MagicMock()
        response.json.return_value = {
            "data": [
                {
                    "orderId": 987654,
                    "sessionId": "different-session",
                    "amount": 1,
                    "status": True,
                    "message": "success",
                }
            ],
            "responseCode": 0,
        }
        mock_post.return_value = response

        with self.assertRaisesMessage(
            P24RefundError, "nie odpowiada żądanemu pełnemu zwrotowi"
        ):
            refund_rzut_transaction(self.refund_request())

    @patch("shop.payment.requests.get")
    def test_finds_previously_accepted_refund_for_safe_retry(self, mock_get):
        from shop.payment import get_rzut_refund

        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "data": {
                "orderId": 987654,
                "sessionId": "rzut-session-1",
                "amount": 4899,
                "currency": "PLN",
                "refunds": [
                    {
                        "requestId": "refund-request-1",
                        "status": 2,
                        "amount": 4899,
                        "description": "Zwrot KK ABC123",
                    }
                ],
            },
            "responseCode": 0,
        }
        mock_get.return_value = response

        result = get_rzut_refund(self.refund_request())

        self.assertTrue(result["status"])
        self.assertFalse(result["completed"])
        self.assertEqual(result["refundStatus"], 2)
        self.assertEqual(result["requestId"], "refund-request-1")
        mock_get.assert_called_once_with(
            "https://sandbox.przelewy24.pl/api/v1/refund/by/orderId/987654",
            auth=("12345", "testapikey"),
            timeout=(3.05, 10),
        )

    @patch("shop.payment.requests.get")
    def test_marks_only_completed_p24_refund_as_completed(self, mock_get):
        from shop.payment import get_rzut_refund

        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "data": {
                "orderId": 987654,
                "sessionId": "rzut-session-1",
                "amount": 4899,
                "currency": "PLN",
                "refunds": [
                    {
                        "requestId": "refund-request-1",
                        "status": 1,
                        "amount": 4899,
                    }
                ],
            },
            "responseCode": 0,
        }
        mock_get.return_value = response

        result = get_rzut_refund(self.refund_request())

        self.assertTrue(result["completed"])
        self.assertEqual(result["refundStatus"], 1)


@override_settings(P24_SANDBOX=True)
class TestGetBaseUrl(TestCase):
    def test_sandbox_url(self):
        from shop.payment import get_base_url

        self.assertEqual(
            get_base_url(), "https://sandbox.przelewy24.pl"
        )

    @override_settings(P24_SANDBOX=False)
    def test_production_url(self):
        from shop.payment import get_base_url

        self.assertEqual(
            get_base_url(), "https://secure.przelewy24.pl"
        )


@override_settings(P24_SANDBOX=True)
class TestGetPaymentUrl(TestCase):
    def test_returns_url_with_token(self):
        from shop.payment import get_payment_url

        result = get_payment_url("token123")
        self.assertEqual(
            result,
            "https://sandbox.przelewy24.pl/trnRequest/token123",
        )
