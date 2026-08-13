from decimal import Decimal

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class TestRzutLifecycleMigration(TransactionTestCase):
    migrate_from = [("shop", "0007_rzut_items")]
    migrate_to = [("shop", "0010_rzut_item_allocation")]

    def setUp(self):
        super().setUp()
        self.executor = MigrationExecutor(connection)
        self.executor.migrate(self.migrate_from)
        old_apps = self.executor.loader.project_state(self.migrate_from).apps
        OrderEdition = old_apps.get_model("shop", "OrderEdition")
        Product = old_apps.get_model("shop", "Product")
        RzutItem = old_apps.get_model("shop", "RzutItem")

        self.status_ids = {
            status: OrderEdition.objects.create(
                title=f"Rzut {status}",
                slug=f"rzut-{status}",
                status=status,
                pickup_details=(
                    "Odbiór przy wejściu od ogrodu."
                    if status == "open"
                    else ""
                ),
            ).pk
            for status in ["draft", "upcoming", "open", "closed"]
        }
        product = Product.objects.create(
            title="Chleb migracyjny",
            slug="chleb-migracyjny",
            description="Opis chleba.",
            price=Decimal("20.00"),
        )
        self.item_id = RzutItem.objects.create(
            rzut_id=self.status_ids["draft"],
            product_id=product.pk,
            price=Decimal("22.00"),
            portion="bochenek",
            pool=10,
        ).pk

    def tearDown(self):
        self.executor = MigrationExecutor(connection)
        self.executor.migrate(self.executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_incomplete_legacy_rzuty_return_to_safe_drafts(self):
        self.executor = MigrationExecutor(connection)
        self.executor.migrate(self.migrate_to)
        new_apps = self.executor.loader.project_state(self.migrate_to).apps
        OrderEdition = new_apps.get_model("shop", "OrderEdition")
        RzutItem = new_apps.get_model("shop", "RzutItem")

        statuses = {
            legacy_status: OrderEdition.objects.get(pk=pk).status
            for legacy_status, pk in self.status_ids.items()
        }
        migrated_open = OrderEdition.objects.get(pk=self.status_ids["open"])

        self.assertEqual(statuses["draft"], "draft")
        self.assertEqual(statuses["upcoming"], "draft")
        self.assertEqual(statuses["open"], "draft")
        self.assertEqual(statuses["closed"], "closed")
        self.assertIsNone(migrated_open.pickup_date)
        self.assertEqual(migrated_open.pickup_place_name, "")
        self.assertEqual(migrated_open.pickup_address, "")
        self.assertEqual(
            migrated_open.pickup_instructions,
            "Odbiór przy wejściu od ogrodu.",
        )
        self.assertTrue(migrated_open.show_upcoming_menu)
        self.assertEqual(
            RzutItem.objects.get(pk=self.item_id).allocated_quantity,
            0,
        )

    def test_reverse_maps_new_statuses_to_supported_legacy_statuses(self):
        self.executor = MigrationExecutor(connection)
        self.executor.migrate(self.migrate_to)
        new_apps = self.executor.loader.project_state(self.migrate_to).apps
        OrderEdition = new_apps.get_model("shop", "OrderEdition")
        published_id = OrderEdition.objects.create(
            title="Nowy opublikowany Rzut",
            slug="nowy-opublikowany-rzut",
            status="published",
        ).pk
        paused_id = OrderEdition.objects.create(
            title="Nowy wstrzymany Rzut",
            slug="nowy-wstrzymany-rzut",
            status="paused",
        ).pk

        self.executor = MigrationExecutor(connection)
        self.executor.migrate(self.migrate_from)
        old_apps = self.executor.loader.project_state(self.migrate_from).apps
        LegacyOrderEdition = old_apps.get_model("shop", "OrderEdition")

        self.assertEqual(
            LegacyOrderEdition.objects.get(pk=published_id).status,
            "open",
        )
        self.assertEqual(
            LegacyOrderEdition.objects.get(pk=paused_id).status,
            "closed",
        )
