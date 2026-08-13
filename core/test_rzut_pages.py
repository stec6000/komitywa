from datetime import time, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from shop.models import OrderEdition, Product, RzutItem


class RzutPageTestCase(TestCase):
    def create_rzut(self, *, title, opens_at, closes_at, **overrides):
        values = {
            "title": title,
            "description": f"Opis: {title}",
            "status": OrderEdition.Status.PUBLISHED,
            "opens_at": opens_at,
            "closes_at": closes_at,
            "pickup_date": timezone.localdate() + timedelta(days=2),
            "pickup_place_name": "Kuchenna Komitywa",
            "pickup_address": "ul. Bukowa 14, Białystok",
            "pickup_starts_at": time(10, 0),
            "pickup_ends_at": time(13, 0),
            "pickup_instructions": "Wejście od ogrodu.",
        }
        values.update(overrides)
        return OrderEdition.objects.create(**values)

    def add_item(
        self,
        rzut,
        *,
        title,
        pool=10,
        allocated_quantity=0,
        is_active=True,
    ):
        product = Product.objects.create(
            title=title,
            description=f"Opis produktu: {title}",
            ingredients="mąka, woda, sól",
            allergens="gluten",
            price=Decimal("24.00"),
        )
        return RzutItem.objects.create(
            rzut=rzut,
            product=product,
            price=Decimal("26.00"),
            portion="bochenek ok. 750 g",
            pool=pool,
            allocated_quantity=allocated_quantity,
            is_active=is_active,
        )


class TestUpcomingRzutPage(RzutPageTestCase):
    def test_shows_nearest_upcoming_rzut_but_respects_hidden_menu(self):
        now = timezone.now()
        nearest = self.create_rzut(
            title="Najbliższy Rzut",
            opens_at=now + timedelta(hours=1),
            closes_at=now + timedelta(hours=2),
            show_upcoming_menu=False,
        )
        self.add_item(nearest, title="Ukryta cynamonka")
        later = self.create_rzut(
            title="Późniejszy Rzut",
            opens_at=now + timedelta(hours=4),
            closes_at=now + timedelta(hours=5),
        )
        self.add_item(later, title="Późniejszy chleb")

        response = self.client.get(reverse("orders"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["upcoming_rzut"], nearest)
        self.assertContains(response, "Najbliższy Rzut")
        self.assertContains(response, "Menu tego Rzutu pokażemy przy otwarciu")
        self.assertNotContains(response, "Ukryta cynamonka")
        self.assertNotContains(response, "Późniejszy Rzut")

    def test_shows_upcoming_menu_when_enabled(self):
        now = timezone.now()
        rzut = self.create_rzut(
            title="Zapowiedziany Rzut",
            opens_at=now + timedelta(hours=1),
            closes_at=now + timedelta(hours=2),
            show_upcoming_menu=True,
        )
        item = self.add_item(rzut, title="Cynamonka z kardamonem")

        response = self.client.get(reverse("orders"))

        self.assertEqual(list(response.context["upcoming_items"]), [item])
        self.assertContains(response, "Cynamonka z kardamonem")
        self.assertContains(response, "bochenek ok. 750 g")
        self.assertNotContains(response, "Menu tego Rzutu pokażemy przy otwarciu")


class TestOpenRzutPage(RzutPageTestCase):
    def test_shows_rzut_items_and_low_exact_availability(self):
        now = timezone.now()
        rzut = self.create_rzut(
            title="Otwarty Rzut",
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(hours=1),
        )
        item = self.add_item(rzut, title="Chleb żytni", pool=3)

        response = self.client.get(reverse("orders"))

        detail_url = reverse(
            "rzut_item_detail",
            kwargs={
                "rzut_slug": rzut.slug,
                "product_slug": item.product.slug,
            },
        )
        self.assertEqual(response.context["current_rzut"], rzut)
        self.assertEqual(list(response.context["current_items"]), [item])
        self.assertContains(response, "Otwarty Rzut")
        self.assertContains(response, "Chleb żytni")
        self.assertContains(response, "26,00 zł")
        self.assertContains(response, "bochenek ok. 750 g")
        self.assertContains(response, "Zostały 3 sztuki")
        self.assertContains(response, f'href="{detail_url}"')
        self.assertContains(response, "ul. Bukowa 14, Białystok")
        shop_add_url = reverse("shop:cart_add", args=[item.product.pk])
        self.assertNotContains(response, f'action="{shop_add_url}"')

    def test_home_recognizes_open_rzut_built_from_rzut_items(self):
        now = timezone.now()
        rzut = self.create_rzut(
            title="Rzut widoczny na stronie głównej",
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(hours=1),
        )
        self.add_item(rzut, title="Chleb ze strony głównej")

        response = self.client.get(reverse("home"))

        self.assertContains(response, rzut.title)
        self.assertNotContains(
            response,
            "Obecnie nie prowadzimy zapisów na żaden rzut.",
        )

    def test_shows_exact_availability_at_twenty_percent_of_pool(self):
        now = timezone.now()
        rzut = self.create_rzut(
            title="Rzut z małą Dostępnością",
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(hours=1),
        )
        self.add_item(
            rzut,
            title="Chleb z małą Dostępnością",
            pool=20,
            allocated_quantity=16,
        )

        response = self.client.get(reverse("orders"))

        self.assertContains(response, "Zostały 4 sztuki")

    def test_completely_sold_out_rzut_and_item_remain_visible(self):
        now = timezone.now()
        rzut = self.create_rzut(
            title="Wyprzedany Rzut",
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(hours=1),
        )
        item = self.add_item(
            rzut,
            title="Wyprzedany chleb",
            pool=10,
            allocated_quantity=10,
        )

        response = self.client.get(reverse("orders"))

        self.assertEqual(response.context["current_rzut"], rzut)
        self.assertContains(response, "Wyprzedany Rzut")
        self.assertContains(response, "Wyprzedany chleb")
        self.assertContains(response, "Wyprzedane")
        self.assertEqual(
            self.client.get(
                reverse(
                    "rzut_item_detail",
                    kwargs={
                        "rzut_slug": rzut.slug,
                        "product_slug": item.product.slug,
                    },
                )
            ).status_code,
            200,
        )


class TestRzutArchivePage(RzutPageTestCase):
    def test_shows_full_menu_only_for_public_archived_rzuty(self):
        now = timezone.now()
        archived = self.create_rzut(
            title="Archiwalny Rzut",
            opens_at=now - timedelta(hours=4),
            closes_at=now - timedelta(hours=2),
            show_in_archive=True,
        )
        archived_item = self.add_item(
            archived,
            title="Archiwalna drożdżówka",
        )
        hidden = self.create_rzut(
            title="Ukryty Rzut",
            opens_at=now - timedelta(hours=3),
            closes_at=now - timedelta(hours=1),
            show_in_archive=False,
        )
        self.add_item(hidden, title="Ukryty produkt")

        response = self.client.get(reverse("orders"))

        self.assertEqual(list(response.context["archived_rzuty"]), [archived])
        self.assertContains(response, "Archiwalny Rzut")
        self.assertContains(response, archived_item.product.title)
        self.assertContains(response, archived_item.portion)
        self.assertNotContains(response, "Ukryty Rzut")
        self.assertNotContains(response, "Ukryty produkt")


class TestRzutItemDetailPage(RzutPageTestCase):
    def detail_url(self, item):
        return reverse(
            "rzut_item_detail",
            kwargs={
                "rzut_slug": item.rzut.slug,
                "product_slug": item.product.slug,
            },
        )

    def test_open_rzut_item_has_details_in_rzut_context(self):
        now = timezone.now()
        rzut = self.create_rzut(
            title="Rzut szczegółowy",
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(hours=1),
        )
        item = self.add_item(rzut, title="Chałka z kruszonką", pool=3)

        response = self.client.get(self.detail_url(item))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["item"], item)
        self.assertContains(response, "Rzut szczegółowy")
        self.assertContains(response, "Chałka z kruszonką")
        self.assertContains(response, "bochenek ok. 750 g")
        self.assertContains(response, "Zostały 3 sztuki")

    def test_hidden_upcoming_menu_and_inactive_item_return_404(self):
        now = timezone.now()
        hidden_rzut = self.create_rzut(
            title="Ukryta zapowiedź",
            opens_at=now + timedelta(hours=1),
            closes_at=now + timedelta(hours=2),
            show_upcoming_menu=False,
        )
        hidden_item = self.add_item(hidden_rzut, title="Ukryta bułka")
        open_rzut = self.create_rzut(
            title="Otwarty Rzut z nieaktywną Pozycją",
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(minutes=30),
        )
        inactive_item = self.add_item(
            open_rzut,
            title="Nieaktywna bułka",
            is_active=False,
        )

        self.assertEqual(
            self.client.get(self.detail_url(hidden_item)).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(self.detail_url(inactive_item)).status_code,
            404,
        )
