from decimal import Decimal

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class TestRzutCatalogMigration(TransactionTestCase):
    migrate_from = [("shop", "0005_order_editions")]
    migrate_to = [("shop", "0007_rzut_items")]

    def setUp(self):
        super().setUp()
        self.executor = MigrationExecutor(connection)
        self.executor.migrate(self.migrate_from)
        old_apps = self.executor.loader.project_state(
            self.migrate_from
        ).apps

        OrderEdition = old_apps.get_model("shop", "OrderEdition")
        Product = old_apps.get_model("shop", "Product")
        Order = old_apps.get_model("shop", "Order")

        edition = OrderEdition.objects.create(
            title="Rzut sierpniowy",
            slug="rzut-sierpniowy",
            status="draft",
        )
        product = Product.objects.create(
            title="Chleb wiejski",
            slug="chleb-wiejski",
            edition=edition,
            type="physical",
            description="Chleb na zakwasie.",
            price=Decimal("24.00"),
            is_active=True,
            sort_order=7,
        )
        self.edition_id = edition.pk
        self.product_id = product.pk
        inactive_product = Product.objects.create(
            title="Nieaktywny produkt sklepowy",
            slug="nieaktywny-produkt-sklepowy",
            type="physical",
            description="Produkt ukryty przed migracją.",
            price=Decimal("12.00"),
            is_active=False,
        )
        self.inactive_product_id = inactive_product.pk

        order = Order.objects.create(
            email="klient@example.com",
            name="Jan Kowalski",
            pickup_date="niedziela",
            total=Decimal("48.00"),
            cart_snapshot={
                str(product.pk): {"quantity": 2, "price": "24.00"}
            },
        )
        self.order_id = order.pk
        self.order_snapshot = order.cart_snapshot

    def tearDown(self):
        self.executor = MigrationExecutor(connection)
        self.executor.migrate(self.executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_existing_assignment_becomes_one_safe_rzut_item(self):
        self.executor = MigrationExecutor(connection)
        self.executor.migrate(self.migrate_to)
        new_apps = self.executor.loader.project_state(self.migrate_to).apps

        Product = new_apps.get_model("shop", "Product")
        RzutItem = new_apps.get_model("shop", "RzutItem")
        Order = new_apps.get_model("shop", "Order")

        product = Product.objects.get(pk=self.product_id)
        inactive_product = Product.objects.get(pk=self.inactive_product_id)
        items = RzutItem.objects.filter(
            rzut_id=self.edition_id,
            product_id=self.product_id,
        )
        order = Order.objects.get(pk=self.order_id)

        self.assertEqual(items.count(), 1)
        item = items.get()
        self.assertEqual(item.price, Decimal("24.00"))
        self.assertEqual(item.portion, "")
        self.assertEqual(item.pool, 1)
        self.assertEqual(item.sort_order, 7)
        self.assertFalse(item.is_active)
        self.assertEqual(product.edition_id, self.edition_id)
        self.assertTrue(product.is_available_in_shop)
        self.assertFalse(inactive_product.is_available_in_shop)
        self.assertEqual(order.cart_snapshot, self.order_snapshot)
