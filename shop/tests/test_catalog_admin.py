from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from shop.models import OrderEdition, Product, ProductCategory, RzutItem


class AdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser(
            email="admin@test.com",
            password="testpass123",
        )

    def setUp(self):
        self.client.force_login(self.admin_user)


class TestProductCatalogAdmin(AdminTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.category = ProductCategory.objects.create(
            name="Wypieki",
            slug="wypieki",
        )

    def test_admin_can_create_catalog_product_with_shop_settings(self):
        response = self.client.post(
            reverse("admin:shop_product_add"),
            {
                "title": "Chleb wiejski",
                "slug": "chleb-wiejski",
                "category": self.category.pk,
                "type": "physical",
                "description": "Chleb na zakwasie.",
                "full_description": "Długo fermentowany chleb pszenny.",
                "ingredients": "mąka pszenna, woda, sól",
                "allergens": "gluten",
                "price": "24.00",
                "default_portion": "bochenek ok. 750 g",
                "is_available_in_shop": "on",
                "sort_order": "10",
                "_save": "Zapisz",
            },
        )

        self.assertRedirects(
            response,
            reverse("admin:shop_product_changelist"),
        )
        product = Product.objects.get(slug="chleb-wiejski")
        self.assertEqual(product.price, Decimal("24.00"))
        self.assertEqual(product.default_portion, "bochenek ok. 750 g")
        self.assertTrue(product.is_available_in_shop)
        self.assertFalse(product.is_archived)

    def test_shop_visibility_is_independent_from_catalog_and_archive(self):
        visible = Product.objects.create(
            title="Chleb dostępny",
            category=self.category,
            description="Widoczny w sklepie.",
            price=Decimal("20.00"),
            is_active=True,
            is_available_in_shop=True,
            is_archived=False,
        )
        unavailable = Product.objects.create(
            title="Chleb tylko do Rzutów",
            category=self.category,
            description="Niewidoczny w sklepie.",
            price=Decimal("21.00"),
            is_active=True,
            is_available_in_shop=False,
            is_archived=False,
        )
        archived = Product.objects.create(
            title="Chleb archiwalny",
            category=self.category,
            description="Zarchiwizowany.",
            price=Decimal("22.00"),
            is_active=True,
            is_available_in_shop=True,
            is_archived=True,
        )
        available_despite_legacy_flag = Product.objects.create(
            title="Chleb dostępny niezależnie",
            category=self.category,
            description="Widoczny dzięki ustawieniu Sklepu.",
            price=Decimal("23.00"),
            is_active=False,
            is_available_in_shop=True,
            is_archived=False,
        )

        response = self.client.get(reverse("shop:list"))

        self.assertContains(response, visible.title)
        self.assertContains(response, available_despite_legacy_flag.title)
        self.assertNotContains(response, unavailable.title)
        self.assertNotContains(response, archived.title)


class TestRzutCatalogAdmin(AdminTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.product = Product.objects.create(
            title="Chleb wiejski",
            description="Chleb na zakwasie.",
            price=Decimal("24.00"),
            default_portion="bochenek ok. 750 g",
        )

    def test_admin_can_create_draft_with_existing_product(self):
        response = self.client.post(
            reverse("admin:shop_orderedition_add"),
            {
                "title": "Rzut niedziela 16.08",
                "slug": "rzut-niedziela-16-08",
                "status": OrderEdition.Status.DRAFT,
                "description": "Niedzielne wypieki.",
                "show_in_archive": "on",
                "items-TOTAL_FORMS": "1",
                "items-INITIAL_FORMS": "0",
                "items-MIN_NUM_FORMS": "0",
                "items-MAX_NUM_FORMS": "1000",
                "items-0-product": self.product.pk,
                "items-0-price": "26.00",
                "items-0-portion": "bochenek ok. 800 g",
                "items-0-pool": "10",
                "items-0-per_customer_limit": "2",
                "items-0-sort_order": "3",
                "items-0-is_active": "on",
                "items-0-production_note": "Fermentacja od soboty.",
                "_save": "Zapisz",
            },
        )

        self.assertRedirects(
            response,
            reverse("admin:shop_orderedition_changelist"),
        )
        rzut = OrderEdition.objects.get(slug="rzut-niedziela-16-08")
        item = RzutItem.objects.get(rzut=rzut, product=self.product)
        self.assertEqual(rzut.status, OrderEdition.Status.DRAFT)
        self.assertEqual(item.price, Decimal("26.00"))
        self.assertEqual(item.portion, "bochenek ok. 800 g")
        self.assertEqual(item.pool, 10)
        self.assertEqual(item.per_customer_limit, 2)
        self.assertEqual(item.sort_order, 3)
        self.assertTrue(item.is_active)
        self.assertEqual(item.production_note, "Fermentacja od soboty.")

        public_response = self.client.get(reverse("orders"))
        self.assertNotContains(public_response, rzut.title)

    def test_admin_uses_product_defaults_for_new_rzut_item(self):
        response = self.client.post(
            reverse("admin:shop_orderedition_add"),
            {
                "title": "Rzut z wartościami domyślnymi",
                "slug": "rzut-z-wartosciami-domyslnymi",
                "status": OrderEdition.Status.DRAFT,
                "description": "Oferta oparta na katalogu.",
                "items-TOTAL_FORMS": "1",
                "items-INITIAL_FORMS": "0",
                "items-MIN_NUM_FORMS": "0",
                "items-MAX_NUM_FORMS": "1000",
                "items-0-product": self.product.pk,
                "items-0-price": "",
                "items-0-portion": "",
                "items-0-pool": "10",
                "items-0-per_customer_limit": "",
                "items-0-sort_order": "0",
                "items-0-is_active": "on",
                "items-0-production_note": "",
                "_save": "Zapisz",
            },
        )

        self.assertRedirects(
            response,
            reverse("admin:shop_orderedition_changelist"),
        )
        item = RzutItem.objects.get(
            rzut__slug="rzut-z-wartosciami-domyslnymi"
        )
        self.assertEqual(item.price, self.product.price)
        self.assertEqual(item.portion, self.product.default_portion)

    def test_editing_product_defaults_does_not_change_rzut_item(self):
        rzut = OrderEdition.objects.create(title="Rzut sierpniowy")
        item = RzutItem.objects.create(
            rzut=rzut,
            product=self.product,
            price=Decimal("26.00"),
            portion="bochenek ok. 800 g",
            pool=10,
        )

        response = self.client.post(
            reverse("admin:shop_product_change", args=[self.product.pk]),
            {
                "title": self.product.title,
                "slug": self.product.slug,
                "type": self.product.type,
                "description": self.product.description,
                "full_description": self.product.full_description,
                "ingredients": self.product.ingredients,
                "allergens": self.product.allergens,
                "price": "30.00",
                "default_portion": "bochenek ok. 900 g",
                "is_available_in_shop": "on",
                "sort_order": "0",
                "_save": "Zapisz",
            },
        )

        self.assertRedirects(
            response,
            reverse("admin:shop_product_changelist"),
        )
        item.refresh_from_db()
        self.assertEqual(item.price, Decimal("26.00"))
        self.assertEqual(item.portion, "bochenek ok. 800 g")

    def test_admin_rejects_nonpositive_pool_and_customer_limit(self):
        response = self.client.post(
            reverse("admin:shop_orderedition_add"),
            {
                "title": "Nieprawidłowy Rzut",
                "slug": "nieprawidlowy-rzut",
                "status": OrderEdition.Status.DRAFT,
                "description": "Oferta z błędnymi limitami.",
                "items-TOTAL_FORMS": "1",
                "items-INITIAL_FORMS": "0",
                "items-MIN_NUM_FORMS": "0",
                "items-MAX_NUM_FORMS": "1000",
                "items-0-product": self.product.pk,
                "items-0-price": "26.00",
                "items-0-portion": "bochenek",
                "items-0-pool": "0",
                "items-0-per_customer_limit": "0",
                "items-0-sort_order": "0",
                "items-0-is_active": "on",
                "_save": "Zapisz",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Upewnij się, że ta wartość jest większa")
        self.assertFalse(
            OrderEdition.objects.filter(slug="nieprawidlowy-rzut").exists()
        )
