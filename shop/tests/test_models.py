from decimal import Decimal

from django.test import TestCase

from shop.models import Order, Product, ProductCategory


class TestProductCategory(TestCase):
    def test_create_category(self):
        cat = ProductCategory.objects.create(name="Ebooki", slug="ebooki")
        self.assertEqual(str(cat), "Ebooki")
        self.assertEqual(cat.slug, "ebooki")

    def test_ordering(self):
        ProductCategory.objects.create(name="Ciasta", slug="ciasta")
        ProductCategory.objects.create(name="Ebooki", slug="ebooki")
        cats = list(ProductCategory.objects.values_list("name", flat=True))
        self.assertEqual(cats, ["Ciasta", "Ebooki"])


class TestProduct(TestCase):
    def setUp(self):
        self.category = ProductCategory.objects.create(
            name="Ebooki", slug="ebooki"
        )

    def test_create_ebook_product(self):
        product = Product.objects.create(
            title="Weganski ebook",
            category=self.category,
            type="ebook",
            description="Krotki opis",
            price=Decimal("29.99"),
            is_active=True,
        )
        self.assertEqual(str(product), "Weganski ebook")
        self.assertEqual(product.type, "ebook")
        self.assertEqual(product.price, Decimal("29.99"))
        self.assertTrue(product.is_active)

    def test_auto_slug_generation(self):
        product = Product.objects.create(
            title="Tort czekoladowy",
            category=self.category,
            type="physical",
            description="Pyszny tort",
            price=Decimal("45.00"),
        )
        self.assertEqual(product.slug, "tort-czekoladowy")

    def test_slug_not_overwritten_if_set(self):
        product = Product.objects.create(
            title="Tort czekoladowy",
            slug="custom-slug",
            category=self.category,
            type="physical",
            description="Pyszny tort",
            price=Decimal("45.00"),
        )
        self.assertEqual(product.slug, "custom-slug")

    def test_type_choices(self):
        self.assertIn(
            ("ebook", "Ebook"),
            Product.TYPE_CHOICES,
        )
        self.assertIn(
            ("physical", "Produkt fizyczny"),
            Product.TYPE_CHOICES,
        )


class TestOrder(TestCase):
    def test_create_order(self):
        order = Order.objects.create(
            email="test@example.com",
            name="Jan Kowalski",
            pickup_date="piatek 10 stycznia",
            total=Decimal("59.99"),
            cart_snapshot={"items": []},
        )
        self.assertEqual(
            str(order), f"Zamowienie #{order.id} - test@example.com"
        )
        self.assertEqual(order.status, "pending")

    def test_status_choices(self):
        self.assertIn(
            ("pending", "Oczekujace na platnosc"),
            Order.STATUS_CHOICES,
        )
        self.assertIn(("paid", "Oplacone"), Order.STATUS_CHOICES)
        self.assertIn(
            ("completed", "Zrealizowane"), Order.STATUS_CHOICES
        )
        self.assertIn(
            ("cancelled", "Anulowane"), Order.STATUS_CHOICES
        )
