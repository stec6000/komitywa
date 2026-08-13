from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from shop.models import Order, OrderEdition, Product, ProductCategory


class TestProductCategory(TestCase):
    def test_create_category(self):
        cat = ProductCategory.objects.create(name="Zupy", slug="zupy")
        self.assertEqual(str(cat), "Zupy")
        self.assertEqual(cat.slug, "zupy")

    def test_ordering(self):
        ProductCategory.objects.all().delete()
        ProductCategory.objects.create(name="Zupy", slug="zupy")
        ProductCategory.objects.create(name="Desery", slug="desery")
        cats = list(ProductCategory.objects.values_list("name", flat=True))
        self.assertEqual(cats, ["Desery", "Zupy"])


class TestOrderEdition(TestCase):
    def test_slug_is_generated_and_made_unique(self):
        first = OrderEdition.objects.create(title="Świąteczna edycja")
        second = OrderEdition.objects.create(title="Świąteczna edycja")

        self.assertEqual(first.slug, "swiateczna-edycja")
        self.assertEqual(second.slug, "swiateczna-edycja-2")

    def test_current_returns_published_rzut_inside_time_window(self):
        now = timezone.now()
        current = OrderEdition.objects.create(
            title="Sierpniowe wypieki",
            status=OrderEdition.Status.PUBLISHED,
            opens_at=now - timedelta(days=1),
            closes_at=now + timedelta(days=1),
        )
        OrderEdition.objects.create(
            title="Jesienne wypieki",
            status=OrderEdition.Status.PUBLISHED,
            opens_at=now + timedelta(days=1),
            closes_at=now + timedelta(days=2),
        )
        OrderEdition.objects.create(
            title="Poprzednia edycja",
            status=OrderEdition.Status.PUBLISHED,
            opens_at=now - timedelta(days=2),
            closes_at=now,
        )
        OrderEdition.objects.create(
            title="Szkic",
            status=OrderEdition.Status.DRAFT,
        )

        self.assertEqual(OrderEdition.objects.current(at=now), current)

    def test_published_rzut_without_dates_is_not_current(self):
        OrderEdition.objects.create(
            title="Rzut bez dat",
            status=OrderEdition.Status.PUBLISHED,
        )

        self.assertIsNone(OrderEdition.objects.current())

    def test_current_returns_none_when_orders_are_closed(self):
        OrderEdition.objects.create(
            title="Zamknięta edycja",
            status=OrderEdition.Status.CLOSED,
        )

        self.assertIsNone(OrderEdition.objects.current())

    def test_end_must_be_after_start(self):
        now = timezone.now()
        edition = OrderEdition(
            title="Błędne okno zamówień",
            opens_at=now,
            closes_at=now - timedelta(minutes=1),
        )

        with self.assertRaises(ValidationError) as error:
            edition.full_clean()

        self.assertIn("closes_at", error.exception.message_dict)


class TestProduct(TestCase):
    def setUp(self):
        self.category, _ = ProductCategory.objects.get_or_create(
            slug="ebooki", defaults={"name": "Ebooki"}
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

    def test_edition_fields_are_optional_for_existing_shop_flow(self):
        product = Product.objects.create(
            title="Produkt bez edycji",
            category=self.category,
            type="physical",
            description="Opis",
            price=Decimal("15.00"),
        )

        self.assertIsNone(product.edition)
        self.assertEqual(product.ingredients, "")
        self.assertEqual(product.allergens, "")
        self.assertEqual(product.sort_order, 0)

    def test_product_can_be_assigned_to_edition(self):
        edition = OrderEdition.objects.create(title="Letni stół")
        product = Product.objects.create(
            title="Drożdżówka",
            edition=edition,
            category=self.category,
            type="physical",
            description="Opis",
            ingredients="mąka, śliwki",
            allergens="gluten",
            price=Decimal("16.00"),
            sort_order=2,
        )

        self.assertEqual(list(edition.products.all()), [product])


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
            str(order), f"Zamówienie #{order.id} - test@example.com"
        )
        self.assertEqual(order.status, "pending")

    def test_status_choices(self):
        self.assertIn(
            ("pending", "Oczekujące na płatność"),
            Order.STATUS_CHOICES,
        )
        self.assertIn(("paid", "Opłacone"), Order.STATUS_CHOICES)
        self.assertIn(
            ("completed", "Zrealizowane"), Order.STATUS_CHOICES
        )
        self.assertIn(
            ("cancelled", "Anulowane"), Order.STATUS_CHOICES
        )
