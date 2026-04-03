import hashlib
import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

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
        self.assertEqual(token, "test-token")


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
        self.assertTrue(result)


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
