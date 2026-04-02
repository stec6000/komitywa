from decimal import Decimal

from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory, TestCase

from shop.cart import Cart
from shop.models import Product, ProductCategory


class CartTestBase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.category = ProductCategory.objects.create(
            name="Ebooki", slug="ebooki"
        )
        self.ebook = Product.objects.create(
            title="Ebook testowy",
            category=self.category,
            type="ebook",
            description="Opis ebooka",
            price=Decimal("29.99"),
        )
        self.physical = Product.objects.create(
            title="Danie w sloiku",
            category=self.category,
            type="physical",
            description="Opis dania",
            price=Decimal("25.00"),
        )

    def _get_request(self):
        request = self.factory.get("/")
        request.session = SessionStore()
        return request


class TestCartAdd(CartTestBase):
    def test_add_product_stores_in_session(self):
        request = self._get_request()
        cart = Cart(request)
        cart.add(self.physical)
        self.assertIn(str(self.physical.id), cart.cart)
        item = cart.cart[str(self.physical.id)]
        self.assertEqual(item["quantity"], 1)
        self.assertEqual(item["price"], str(self.physical.price))

    def test_add_ebook_always_quantity_one(self):
        request = self._get_request()
        cart = Cart(request)
        cart.add(self.ebook)
        cart.add(self.ebook)
        cart.add(self.ebook)
        self.assertEqual(cart.cart[str(self.ebook.id)]["quantity"], 1)

    def test_add_physical_increments_quantity(self):
        request = self._get_request()
        cart = Cart(request)
        cart.add(self.physical)
        cart.add(self.physical)
        self.assertEqual(
            cart.cart[str(self.physical.id)]["quantity"], 2
        )


class TestCartRemove(CartTestBase):
    def test_remove_product(self):
        request = self._get_request()
        cart = Cart(request)
        cart.add(self.physical)
        cart.remove(self.physical.id)
        self.assertNotIn(str(self.physical.id), cart.cart)

    def test_remove_nonexistent_product(self):
        request = self._get_request()
        cart = Cart(request)
        cart.remove(9999)  # should not raise


class TestCartUpdate(CartTestBase):
    def test_update_quantity(self):
        request = self._get_request()
        cart = Cart(request)
        cart.add(self.physical)
        cart.update_quantity(self.physical.id, 3)
        self.assertEqual(
            cart.cart[str(self.physical.id)]["quantity"], 3
        )


class TestCartMethods(CartTestBase):
    def test_len_returns_total_quantity(self):
        request = self._get_request()
        cart = Cart(request)
        cart.add(self.physical)
        cart.add(self.physical)
        cart.add(self.ebook)
        self.assertEqual(len(cart), 3)

    def test_get_total_price(self):
        request = self._get_request()
        cart = Cart(request)
        cart.add(self.physical)
        cart.add(self.physical)
        cart.add(self.ebook)
        expected = Decimal("25.00") * 2 + Decimal("29.99")
        self.assertEqual(cart.get_total_price(), expected)

    def test_clear(self):
        request = self._get_request()
        cart = Cart(request)
        cart.add(self.physical)
        cart.add(self.ebook)
        cart.clear()
        self.assertEqual(len(cart), 0)


class TestCartContextProcessor(TestCase):
    def test_cart_count_context_processor(self):
        from shop.context_processors import cart_count

        factory = RequestFactory()
        request = factory.get("/")
        request.session = {
            "cart": {
                "1": {"quantity": 2, "price": "10.00"},
                "2": {"quantity": 1, "price": "20.00"},
            }
        }
        result = cart_count(request)
        self.assertEqual(result, {"cart_count": 3})

    def test_cart_count_empty_session(self):
        from shop.context_processors import cart_count

        factory = RequestFactory()
        request = factory.get("/")
        request.session = {}
        result = cart_count(request)
        self.assertEqual(result, {"cart_count": 0})
