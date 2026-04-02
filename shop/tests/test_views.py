from decimal import Decimal

from django.test import TestCase

from shop.forms import CheckoutForm
from shop.models import Product, ProductCategory


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

    def test_checkout_post_creates_order(self):
        from shop.models import Order

        self._add_to_cart()
        response = self.client.post("/zamowienie/", {
            "email": "test@example.com",
            "name": "Jan Kowalski",
            "pickup_date": "piatek 10 stycznia",
            "consent_data": True,
            "consent_terms": True,
        })
        self.assertRedirects(response, "/zamowienie/potwierdzenie/")
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.email, "test@example.com")
        self.assertEqual(order.total, Decimal("29.99"))

    def test_checkout_confirm_returns_200(self):
        response = self.client.get("/zamowienie/potwierdzenie/")
        self.assertEqual(response.status_code, 200)


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
