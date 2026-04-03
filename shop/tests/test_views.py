import json
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings

from shop.forms import CheckoutForm
from shop.models import Order, Product, ProductCategory
from shop.payment import calculate_sign


class TestProductList(TestCase):
    def test_product_list_returns_200(self):
        response = self.client.get("/sklep/")
        self.assertEqual(response.status_code, 200)


class TestProductDetail(TestCase):
    def setUp(self):
        self.category, _ = ProductCategory.objects.get_or_create(
            slug="ebooki", defaults={"name": "Ebooki"}
        )
        self.product = Product.objects.create(
            title="Testowy produkt",
            slug="testowy-produkt",
            category=self.category,
            type="ebook",
            description="Opis",
            price=Decimal("19.99"),
        )

    def test_product_detail_returns_200(self):
        response = self.client.get("/sklep/testowy-produkt/")
        self.assertEqual(response.status_code, 200)


class TestCartView(TestCase):
    def test_cart_view_returns_200(self):
        response = self.client.get("/koszyk/")
        self.assertEqual(response.status_code, 200)


@override_settings(
    P24_CRC_KEY="testcrc",
    P24_MERCHANT_ID=12345,
    P24_POS_ID=12345,
    P24_API_KEY="testapikey",
    P24_SANDBOX=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class TestCheckout(TestCase):
    def setUp(self):
        self.category, _ = ProductCategory.objects.get_or_create(
            slug="ebooki", defaults={"name": "Ebooki"}
        )
        self.product = Product.objects.create(
            title="Checkout produkt",
            slug="checkout-produkt",
            category=self.category,
            type="physical",
            description="Opis",
            price=Decimal("29.99"),
        )

    def _add_to_cart(self):
        """Add a product to cart via session."""
        session = self.client.session
        session["cart"] = {
            str(self.product.id): {
                "quantity": 1,
                "price": str(self.product.price),
            }
        }
        session.save()

    def test_checkout_empty_cart_redirects(self):
        response = self.client.get("/zamowienie/")
        self.assertRedirects(response, "/koszyk/")

    def test_checkout_with_cart_returns_200(self):
        self._add_to_cart()
        response = self.client.get("/zamowienie/")
        self.assertEqual(response.status_code, 200)

    @patch("shop.views.register_transaction", return_value="testtoken123")
    @patch("shop.views.get_payment_url",
           return_value="https://sandbox.przelewy24.pl/trnRequest/testtoken123")
    def test_checkout_post_redirects_to_p24(self, mock_url, mock_register):
        self._add_to_cart()
        response = self.client.post("/zamowienie/", {
            "email": "test@example.com",
            "name": "Jan Kowalski",
            "pickup_date": "piatek 10 stycznia",
            "consent_data": True,
            "consent_terms": True,
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn("przelewy24.pl", response.url)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertTrue(order.p24_session_id.startswith("order-"))

    @patch("shop.views.register_transaction", return_value="testtoken123")
    @patch("shop.views.get_payment_url",
           return_value="https://sandbox.przelewy24.pl/trnRequest/testtoken123")
    def test_checkout_post_clears_cart(self, mock_url, mock_register):
        self._add_to_cart()
        self.client.post("/zamowienie/", {
            "email": "test@example.com",
            "name": "Jan Kowalski",
            "pickup_date": "piatek 10 stycznia",
            "consent_data": True,
            "consent_terms": True,
        })
        cart = self.client.session.get("cart")
        self.assertTrue(cart is None or cart == {})


class TestCheckoutForm(TestCase):
    def test_valid_form(self):
        form = CheckoutForm(
            data={
                "email": "test@example.com",
                "name": "Jan Kowalski",
                "pickup_date": "piatek 10 stycznia",
                "consent_data": True,
                "consent_terms": True,
            }
        )
        self.assertTrue(form.is_valid())

    def test_optional_phone(self):
        form = CheckoutForm(
            data={
                "email": "test@example.com",
                "name": "Jan Kowalski",
                "phone": "",
                "pickup_date": "piatek 10 stycznia",
                "consent_data": True,
                "consent_terms": True,
            }
        )
        self.assertTrue(form.is_valid())

    def test_missing_consent_data(self):
        form = CheckoutForm(
            data={
                "email": "test@example.com",
                "name": "Jan Kowalski",
                "pickup_date": "piatek 10 stycznia",
                "consent_data": False,
                "consent_terms": True,
            }
        )
        self.assertFalse(form.is_valid())

    def test_missing_consent_terms(self):
        form = CheckoutForm(
            data={
                "email": "test@example.com",
                "name": "Jan Kowalski",
                "pickup_date": "piatek 10 stycznia",
                "consent_data": True,
                "consent_terms": False,
            }
        )
        self.assertFalse(form.is_valid())


@override_settings(
    P24_CRC_KEY="testcrc",
    P24_MERCHANT_ID=12345,
    P24_POS_ID=12345,
    P24_API_KEY="testapikey",
    P24_SANDBOX=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class TestP24Webhook(TestCase):
    def setUp(self):
        self.category, _ = ProductCategory.objects.get_or_create(
            slug="ebooki", defaults={"name": "Ebooki"}
        )
        self.order = Order.objects.create(
            email="test@example.com",
            name="Jan Kowalski",
            phone="",
            pickup_date="piatek 10 stycznia",
            total=Decimal("29.99"),
            cart_snapshot={"1": {"quantity": 1, "price": "29.99"}},
            p24_session_id="order-1-abc12345",
            status="pending",
        )

    def _build_webhook_data(self, session_id=None, order_id=100,
                            amount=2999):
        session_id = session_id or self.order.p24_session_id
        data = {
            "merchantId": 12345,
            "posId": 12345,
            "sessionId": session_id,
            "amount": amount,
            "originAmount": amount,
            "currency": "PLN",
            "orderId": order_id,
            "methodId": 25,
            "statement": "test",
        }
        sign = calculate_sign({
            "merchantId": data["merchantId"],
            "posId": data["posId"],
            "sessionId": session_id,
            "amount": amount,
            "originAmount": data["originAmount"],
            "currency": "PLN",
            "orderId": order_id,
            "methodId": data["methodId"],
            "statement": data["statement"],
            "crc": "testcrc",
        })
        data["sign"] = sign
        return data

    @patch("shop.views.verify_transaction", return_value=True)
    @patch("shop.views.send_order_confirmation")
    @patch("shop.views.send_ebook_delivery")
    def test_webhook_valid_sign_updates_order(
        self, mock_ebook, mock_confirm, mock_verify
    ):
        data = self._build_webhook_data()
        response = self.client.post(
            "/zamowienie/webhook/p24/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")

    def test_webhook_invalid_sign_returns_400(self):
        data = self._build_webhook_data()
        data["sign"] = "invalidsign"
        response = self.client.post(
            "/zamowienie/webhook/p24/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_webhook_unknown_session_returns_404(self):
        data = self._build_webhook_data(session_id="order-999-nonexist")
        response = self.client.post(
            "/zamowienie/webhook/p24/",
            data=json.dumps(data),
            content_type="application/json",
        )
        # Sign will be valid for the data but session won't match an order
        self.assertEqual(response.status_code, 404)

    def test_webhook_invalid_json_returns_400(self):
        response = self.client.post(
            "/zamowienie/webhook/p24/",
            data="not json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_webhook_csrf_exempt(self):
        """POST without CSRF token should NOT return 403."""
        from django.test import Client

        client = Client(enforce_csrf_checks=True)
        data = self._build_webhook_data()
        response = client.post(
            "/zamowienie/webhook/p24/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertNotEqual(response.status_code, 403)


class TestP24Return(TestCase):
    def setUp(self):
        self.order = Order.objects.create(
            email="test@example.com",
            name="Jan Kowalski",
            phone="",
            pickup_date="piatek 10 stycznia",
            total=Decimal("29.99"),
            cart_snapshot={"1": {"quantity": 1, "price": "29.99"}},
            p24_session_id="order-1-abc12345",
            status="pending",
        )

    def test_return_page_returns_200(self):
        response = self.client.get("/zamowienie/powrot/")
        self.assertEqual(response.status_code, 200)

    def test_return_page_with_order_id(self):
        response = self.client.get(
            f"/zamowienie/powrot/?order_id={self.order.id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dziękujemy za zamówienie")

    def test_return_page_unknown_order(self):
        response = self.client.get("/zamowienie/powrot/?order_id=9999")
        self.assertEqual(response.status_code, 200)


class TestP24Cancel(TestCase):
    def setUp(self):
        self.order = Order.objects.create(
            email="test@example.com",
            name="Jan Kowalski",
            phone="",
            pickup_date="piatek 10 stycznia",
            total=Decimal("29.99"),
            cart_snapshot={"1": {"quantity": 1, "price": "29.99"}},
            p24_session_id="order-1-abc12345",
            status="pending",
        )

    def test_cancel_restores_cart(self):
        response = self.client.get(
            f"/zamowienie/anulowano/?order_id={self.order.id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.session["cart"],
            {"1": {"quantity": 1, "price": "29.99"}},
        )

    def test_cancel_sets_order_cancelled(self):
        self.client.get(
            f"/zamowienie/anulowano/?order_id={self.order.id}"
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "cancelled")

    def test_cancel_page_returns_200(self):
        response = self.client.get("/zamowienie/anulowano/")
        self.assertEqual(response.status_code, 200)


class TestProductAdmin(TestCase):
    def test_admin_accessible(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        admin_user = User.objects.create_superuser(
            email="admin@test.com", password="testpass123"
        )
        self.client.force_login(admin_user)
        response = self.client.get("/admin/shop/product/")
        self.assertEqual(response.status_code, 200)
