from datetime import time, timedelta
from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from shop.models import OrderEdition, Product, RzutItem


class RzutCartHttpTestCase(TestCase):
    def create_open_rzut(self, title="Rzut niedzielny"):
        now = timezone.now()
        return OrderEdition.objects.create(
            title=title,
            description="Niedzielne wypieki.",
            status=OrderEdition.Status.PUBLISHED,
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(hours=1),
            pickup_date=timezone.localdate() + timedelta(days=1),
            pickup_place_name="Kuchenna Komitywa",
            pickup_address="ul. Bukowa 14, Białystok",
            pickup_starts_at=time(10, 0),
            pickup_ends_at=time(13, 0),
            pickup_instructions="Wejście od ogrodu.",
        )

    def create_item(self, rzut, title="Chleb wiejski", **overrides):
        product = Product.objects.create(
            title=title,
            description="Chleb na zakwasie.",
            ingredients="mąka, woda, sól",
            allergens="gluten",
            price=Decimal("24.00"),
            default_portion="bochenek ok. 750 g",
            is_available_in_shop=False,
        )
        values = {
            "rzut": rzut,
            "product": product,
            "price": Decimal("26.00"),
            "portion": "bochenek ok. 750 g",
            "pool": 10,
        }
        values.update(overrides)
        return RzutItem.objects.create(**values)


class TestRzutCartIsolation(RzutCartHttpTestCase):
    def test_rzut_cart_coexists_with_shop_cart_without_reserving_pool(self):
        shop_product = Product.objects.create(
            title="Ebook",
            type="ebook",
            description="Przepisy.",
            price=Decimal("19.00"),
            is_available_in_shop=True,
        )
        rzut = self.create_open_rzut()
        item = self.create_item(rzut)

        self.client.post(reverse("shop:cart_add", args=[shop_product.pk]))
        response = self.client.post(
            reverse("shop:rzut_cart_add", args=[item.pk])
        )

        self.assertRedirects(response, reverse("shop:rzut_cart"))
        session = self.client.session
        self.assertEqual(session["cart"][str(shop_product.pk)]["quantity"], 1)
        self.assertEqual(
            session["rzut_cart"]["items"][str(item.pk)],
            {"quantity": 1, "price": "26.00"},
        )
        item.refresh_from_db()
        self.assertEqual(item.allocated_quantity, 0)

    def test_cart_rejects_an_item_from_another_rzut(self):
        first_rzut = self.create_open_rzut("Pierwszy Rzut")
        first_item = self.create_item(first_rzut, "Chleb")
        second_rzut = self.create_open_rzut("Drugi Rzut")
        second_item = self.create_item(second_rzut, "Cynamonka")
        self.client.post(
            reverse("shop:rzut_cart_add", args=[first_item.pk])
        )

        response = self.client.post(
            reverse("shop:rzut_cart_add", args=[second_item.pk]),
            follow=True,
        )

        self.assertContains(
            response,
            "Koszyk Rzutu może zawierać Pozycje tylko jednego Rzutu.",
        )
        cart = self.client.session["rzut_cart"]
        self.assertEqual(cart["rzut_id"], first_rzut.pk)
        self.assertEqual(list(cart["items"]), [str(first_item.pk)])


class TestRzutCartQuantities(RzutCartHttpTestCase):
    def test_customer_can_set_positive_quantity_and_remove_item(self):
        item = self.create_item(self.create_open_rzut())
        self.client.post(reverse("shop:rzut_cart_add", args=[item.pk]))

        response = self.client.post(
            reverse("shop:rzut_cart_update", args=[item.pk]),
            {"quantity": "3"},
        )

        self.assertRedirects(response, reverse("shop:rzut_cart"))
        self.assertEqual(
            self.client.session["rzut_cart"]["items"][str(item.pk)][
                "quantity"
            ],
            3,
        )

        response = self.client.post(
            reverse("shop:rzut_cart_remove", args=[item.pk])
        )

        self.assertRedirects(response, reverse("shop:rzut_cart"))
        self.assertEqual(
            self.client.session["rzut_cart"],
            {"rzut_id": None, "items": {}},
        )

    def test_non_positive_or_non_integer_quantity_is_rejected(self):
        item = self.create_item(self.create_open_rzut())
        self.client.post(reverse("shop:rzut_cart_add", args=[item.pk]))

        for invalid_quantity in ["0", "-1", "1.5", "chleb", ""]:
            with self.subTest(quantity=invalid_quantity):
                response = self.client.post(
                    reverse("shop:rzut_cart_update", args=[item.pk]),
                    {"quantity": invalid_quantity},
                    follow=True,
                )

                self.assertContains(
                    response,
                    "Podaj dodatnią, całkowitą liczbę sztuk.",
                )
                self.assertEqual(
                    self.client.session["rzut_cart"]["items"][str(item.pk)][
                        "quantity"
                    ],
                    1,
                )


class TestRzutCartView(RzutCartHttpTestCase):
    def test_cart_shows_items_total_and_no_availability_guarantee(self):
        rzut = self.create_open_rzut()
        item = self.create_item(rzut)
        self.client.post(reverse("shop:rzut_cart_add", args=[item.pk]))
        self.client.post(
            reverse("shop:rzut_cart_update", args=[item.pk]),
            {"quantity": "2"},
        )

        response = self.client.get(reverse("shop:rzut_cart"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, rzut.title)
        self.assertContains(response, item.product.title)
        self.assertContains(response, "Liczba sztuk: 2")
        self.assertContains(response, "Porcja: bochenek ok. 750 g")
        self.assertContains(response, "52,00 zł")
        self.assertContains(
            response,
            "Koszyk Rzutu nie rezerwuje Dostępności",
        )

    def test_customer_must_accept_a_changed_price(self):
        item = self.create_item(self.create_open_rzut())
        self.client.post(reverse("shop:rzut_cart_add", args=[item.pk]))
        item.price = Decimal("30.00")
        item.save(update_fields=["price"])

        response = self.client.get(reverse("shop:rzut_cart"))

        self.assertContains(
            response,
            "Cena zmieniła się z 26,00 zł na 30,00 zł.",
        )
        self.assertContains(response, "Akceptuj nową cenę")
        self.assertEqual(
            self.client.session["rzut_cart"]["items"][str(item.pk)]["price"],
            "26.00",
        )

        response = self.client.post(
            reverse("shop:rzut_cart_accept_prices"),
            {f"price_{item.pk}": "30.00"},
            follow=True,
        )

        self.assertNotContains(response, "Cena zmieniła się")
        self.assertContains(response, "30,00 zł")
        self.assertEqual(
            self.client.session["rzut_cart"]["items"][str(item.pk)]["price"],
            "30.00",
        )

    def test_price_that_changes_during_acceptance_stays_unaccepted(self):
        item = self.create_item(self.create_open_rzut())
        self.client.post(reverse("shop:rzut_cart_add", args=[item.pk]))
        RzutItem.objects.filter(pk=item.pk).update(price=Decimal("30.00"))
        self.client.get(reverse("shop:rzut_cart"))
        RzutItem.objects.filter(pk=item.pk).update(price=Decimal("35.00"))

        response = self.client.post(
            reverse("shop:rzut_cart_accept_prices"),
            {f"price_{item.pk}": "30.00"},
            follow=True,
        )

        self.assertContains(
            response,
            "Ceny ponownie się zmieniły. Sprawdź aktualną sumę.",
        )
        self.assertContains(
            response,
            "Cena zmieniła się z 26,00 zł na 35,00 zł.",
        )
        self.assertEqual(
            self.client.session["rzut_cart"]["items"][str(item.pk)]["price"],
            "26.00",
        )

    def test_malformed_price_acceptance_is_rejected(self):
        item = self.create_item(self.create_open_rzut())
        self.client.post(reverse("shop:rzut_cart_add", args=[item.pk]))
        RzutItem.objects.filter(pk=item.pk).update(price=Decimal("30.00"))

        response = self.client.post(
            reverse("shop:rzut_cart_accept_prices"),
            {f"price_{item.pk}": "nie-cena"},
            follow=True,
        )

        self.assertContains(
            response,
            "Ceny ponownie się zmieniły. Sprawdź aktualną sumę.",
        )
        self.assertEqual(
            self.client.session["rzut_cart"]["items"][str(item.pk)]["price"],
            "26.00",
        )

    def test_unavailable_quantity_is_not_reduced_silently(self):
        item = self.create_item(self.create_open_rzut(), pool=10)
        self.client.post(reverse("shop:rzut_cart_add", args=[item.pk]))
        self.client.post(
            reverse("shop:rzut_cart_update", args=[item.pk]),
            {"quantity": "4"},
        )
        RzutItem.objects.filter(pk=item.pk).update(allocated_quantity=8)

        response = self.client.get(reverse("shop:rzut_cart"))

        self.assertContains(
            response,
            "Wybrana liczba sztuk to 4, ale Dostępność wynosi 2. "
            "Zmień ilość.",
        )
        self.assertEqual(
            self.client.session["rzut_cart"]["items"][str(item.pk)][
                "quantity"
            ],
            4,
        )

    def test_inactive_item_is_reported_and_removed_from_session(self):
        item = self.create_item(self.create_open_rzut())
        self.client.post(reverse("shop:rzut_cart_add", args=[item.pk]))
        item.is_active = False
        item.save(update_fields=["is_active"])

        response = self.client.get(reverse("shop:rzut_cart"))

        self.assertContains(
            response,
            "Pozycja „Chleb wiejski” nie jest już dostępna i została "
            "usunięta z Koszyka Rzutu.",
        )
        self.assertEqual(
            self.client.session["rzut_cart"],
            {"rzut_id": None, "items": {}},
        )

    def test_closed_rzut_and_deleted_item_are_removed_safely(self):
        rzut = self.create_open_rzut()
        closed_item = self.create_item(rzut, "Chleb zamkniętego Rzutu")
        deleted_item = self.create_item(rzut, "Usunięta bułka")
        self.client.post(
            reverse("shop:rzut_cart_add", args=[closed_item.pk])
        )
        self.client.post(
            reverse("shop:rzut_cart_add", args=[deleted_item.pk])
        )
        deleted_item.delete()
        rzut.status = OrderEdition.Status.CLOSED
        rzut.save(update_fields=["status"])

        response = self.client.get(reverse("shop:rzut_cart"))

        self.assertContains(response, "nie jest już dostępna")
        self.assertEqual(
            self.client.session["rzut_cart"],
            {"rzut_id": None, "items": {}},
        )


class TestRzutCartPurchasePaths(RzutCartHttpTestCase):
    def test_open_item_can_be_added_but_sold_out_item_cannot(self):
        rzut = self.create_open_rzut()
        available = self.create_item(rzut, "Dostępny chleb")
        sold_out = self.create_item(
            rzut,
            "Wyprzedana bułka",
            pool=3,
            allocated_quantity=3,
        )

        response = self.client.get(reverse("orders"))

        self.assertContains(
            response,
            reverse("shop:rzut_cart_add", args=[available.pk]),
        )
        self.assertNotContains(
            response,
            reverse("shop:rzut_cart_add", args=[sold_out.pk]),
        )
        self.assertEqual(
            self.client.post(
                reverse("shop:rzut_cart_add", args=[sold_out.pk])
            ).status_code,
            404,
        )
        self.assertContains(response, reverse("shop:rzut_cart"))
        detail_response = self.client.get(
            reverse(
                "rzut_item_detail",
                kwargs={
                    "rzut_slug": rzut.slug,
                    "product_slug": available.product.slug,
                },
            )
        )
        self.assertContains(
            detail_response,
            reverse("shop:rzut_cart_add", args=[available.pk]),
        )

    def test_rzut_only_product_is_not_purchasable_through_shop(self):
        item = self.create_item(self.create_open_rzut())

        detail_response = self.client.get(
            reverse("shop:detail", args=[item.product.slug])
        )
        add_response = self.client.post(
            reverse("shop:cart_add", args=[item.product.pk])
        )

        self.assertEqual(detail_response.status_code, 404)
        self.assertEqual(add_response.status_code, 404)

    def test_cart_mutations_require_csrf_token(self):
        item = self.create_item(self.create_open_rzut())
        csrf_client = Client(enforce_csrf_checks=True)

        response = csrf_client.post(
            reverse("shop:rzut_cart_add", args=[item.pk])
        )

        self.assertEqual(response.status_code, 403)
