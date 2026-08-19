from datetime import time, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core import legal
from shop.models import OrderEdition, Product, Reservation, RzutItem


class RzutCheckoutHttpTestCase(TestCase):
    def setUp(self):
        now = timezone.now()
        self.rzut = OrderEdition.objects.create(
            title="Rzut niedzielny",
            description="Niedzielne wypieki.",
            status=OrderEdition.Status.PUBLISHED,
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(hours=1),
            pickup_date=timezone.localdate() + timedelta(days=1),
            pickup_place_name="Kuchenna Komitywa",
            pickup_address="ul. Bukowa 14, Białystok",
            pickup_starts_at=time(10, 0),
            pickup_ends_at=time(12, 30),
            pickup_instructions="Wejście od ogrodu.",
        )
        product = Product.objects.create(
            title="Chleb wiejski",
            description="Chleb na zakwasie.",
            ingredients="mąka, woda, sól",
            allergens="gluten",
            price=Decimal("24.00"),
            default_portion="bochenek ok. 750 g",
            is_available_in_shop=False,
        )
        self.item = RzutItem.objects.create(
            rzut=self.rzut,
            product=product,
            price=Decimal("26.00"),
            portion="bochenek ok. 750 g",
            pool=10,
        )
        self.client.post(
            reverse("shop:rzut_cart_add", args=[self.item.pk])
        )

    def valid_data(self, **overrides):
        values = {
            "name": "Jan Kowalski",
            "email": " JAN@Example.COM ",
            "phone": "+48 500 600 700",
            "notes": "Odbierze siostra.",
            "pickup_slot": "10:00:00|11:00:00",
            "consent_data": "on",
            "consent_terms": "on",
            "terms_version": legal.CURRENT_TERMS.identifier,
        }
        values.update(overrides)
        return values

    def test_checkout_collects_required_and_optional_customer_data(self):
        response = self.client.get(reverse("shop:rzut_checkout"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="phone"')
        self.assertContains(response, 'name="notes"')
        self.assertContains(response, 'name="pickup_slot"')
        self.assertContains(response, "10:00–11:00")
        self.assertContains(response, "12:00–12:30")
        self.assertContains(response, 'name="consent_data"')
        self.assertContains(response, 'name="consent_terms"')
        self.assertContains(
            response,
            "Uwagi nie gwarantują zmiany składu ani modyfikacji alergicznych",
        )

    def test_checkout_shows_current_terms_and_cancellation_before_payment(self):
        response = self.client.get(reverse("shop:rzut_checkout"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2026-08-19-rzuty-v1")
        self.assertContains(
            response,
            "po wysłaniu formularza od razu przejdziesz do Przelewy24",
        )
        self.assertContains(
            response,
            "Zmiana lub anulowanie Zamówienia Rzutu wymaga kontaktu z nami.",
        )
        self.assertContains(response, reverse("regulations"))
        self.assertContains(response, reverse("contact"))

    def test_rzut_page_explains_that_cancellation_requires_contact(self):
        response = self.client.get(reverse("orders"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Zmiana lub anulowanie Zamówienia Rzutu wymaga kontaktu z nami.",
        )
        self.assertContains(response, reverse("contact"))

    @patch("shop.views.register_rzut_transaction", return_value="token-123")
    def test_valid_checkout_reserves_pool_and_redirects_to_p24(
        self,
        register_payment,
    ):
        response = self.client.post(
            reverse("shop:rzut_checkout"),
            self.valid_data(),
        )

        reservation = Reservation.objects.get()
        self.item.refresh_from_db()
        self.assertRedirects(
            response,
            "https://sandbox.przelewy24.pl/trnRequest/token-123",
            fetch_redirect_response=False,
        )
        self.assertEqual(reservation.customer_email, "jan@example.com")
        self.assertEqual(reservation.pickup_starts_at, time(10, 0))
        self.assertEqual(reservation.pickup_ends_at, time(11, 0))
        self.assertEqual(
            reservation.terms_version,
            "2026-08-19-rzuty-v1",
        )
        self.assertIsNotNone(reservation.terms_accepted_at)
        self.assertEqual(self.item.allocated_quantity, 1)
        self.assertNotIn("rzut_cart", self.client.session)
        register_payment.assert_called_once()
        _, url_return, url_status = register_payment.call_args.args
        self.assertIn(reservation.p24_session_id, url_return)
        self.assertTrue(url_status.endswith("/zamowienia/webhook/p24/"))

    @patch("shop.views.register_rzut_transaction", return_value="token-123")
    def test_checkout_rejects_consent_to_an_outdated_terms_version(
        self,
        register_payment,
    ):
        response = self.client.post(
            reverse("shop:rzut_checkout"),
            self.valid_data(terms_version="2026-01-01"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Regulamin został zaktualizowany")
        self.assertContains(response, 'value="2026-08-19-rzuty-v1"')
        self.assertFalse(Reservation.objects.exists())
        self.item.refresh_from_db()
        self.assertEqual(self.item.allocated_quantity, 0)
        register_payment.assert_not_called()

    def test_checkout_requires_pickup_slot_and_both_consents(self):
        response = self.client.post(
            reverse("shop:rzut_checkout"),
            self.valid_data(
                pickup_slot="",
                consent_data="",
                consent_terms="",
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "To pole jest wymagane.", count=3)
        self.assertFalse(Reservation.objects.exists())
        self.item.refresh_from_db()
        self.assertEqual(self.item.allocated_quantity, 0)

    @patch("shop.views.register_rzut_transaction", side_effect=TimeoutError)
    def test_p24_failure_releases_pool_and_preserves_rzut_cart(
        self,
        register_payment,
    ):
        response = self.client.post(
            reverse("shop:rzut_checkout"),
            self.valid_data(),
            follow=True,
        )

        reservation = Reservation.objects.get()
        self.item.refresh_from_db()
        self.assertEqual(response.redirect_chain[0][0], reverse("shop:rzut_cart"))
        self.assertContains(response, "Pula została zwolniona")
        self.assertEqual(reservation.status, Reservation.Status.FAILED)
        self.assertEqual(self.item.allocated_quantity, 0)
        self.assertEqual(
            self.client.session["rzut_cart"]["items"][str(self.item.pk)][
                "quantity"
            ],
            1,
        )
        register_payment.assert_called_once()

    def test_changed_price_returns_customer_to_cart_without_reservation(self):
        RzutItem.objects.filter(pk=self.item.pk).update(
            price=Decimal("28.00")
        )

        response = self.client.post(
            reverse("shop:rzut_checkout"),
            self.valid_data(),
            follow=True,
        )

        self.assertEqual(response.redirect_chain[0][0], reverse("shop:rzut_cart"))
        self.assertContains(response, "Zaakceptuj aktualną sumę")
        self.assertFalse(Reservation.objects.exists())

    def test_closed_rzut_explains_that_cart_changed(self):
        self.rzut.status = OrderEdition.Status.CLOSED
        self.rzut.save(update_fields=["status"])

        response = self.client.post(
            reverse("shop:rzut_checkout"),
            self.valid_data(),
            follow=True,
        )

        self.assertContains(response, "Koszyk Rzutu zmienił się")
        self.assertFalse(Reservation.objects.exists())
