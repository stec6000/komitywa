from datetime import time, timedelta
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from shop.models import OrderEdition, Product, Reservation, RzutItem
from shop.reservations import (
    ReservationCheckoutData,
    ReservationLineRequest,
    confirm_reservation,
    create_reservation,
    expire_due_reservations,
    fail_reservation,
)


class ReservationExpiryTestCase(TestCase):
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
            pickup_ends_at=time(12, 0),
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

    def create_reservation(self, *, now=None, quantity=2):
        return create_reservation(
            rzut_id=self.rzut.pk,
            lines=[
                ReservationLineRequest(
                    self.item.pk,
                    quantity,
                    self.item.price,
                )
            ],
            checkout=ReservationCheckoutData(
                name="Jan Kowalski",
                email="jan@example.com",
                phone="+48 500 600 700",
                notes="Odbierze siostra.",
                pickup_starts_at=time(10, 0),
                pickup_ends_at=time(11, 0),
            ),
            now=now,
        )


class TestExpireReservationsCommand(ReservationExpiryTestCase):
    def test_command_expires_due_reservation_and_releases_pool(self):
        reservation = self.create_reservation(
            now=timezone.now() - timedelta(minutes=16)
        )

        stdout = StringIO()
        call_command("expire_rzut_reservations", stdout=stdout)

        reservation.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.EXPIRED)
        self.assertEqual(self.item.allocated_quantity, 0)
        self.assertIn("Wygaszono Rezerwacje: 1", stdout.getvalue())

    def test_command_deletes_only_failed_and_expired_older_than_30_days(self):
        old_failed = self.create_reservation(quantity=1)
        fail_reservation(old_failed)
        old_expired = self.create_reservation(quantity=1)
        expire_due_reservations(now=old_expired.expires_at)
        recent_failed = self.create_reservation(quantity=1)
        fail_reservation(recent_failed)
        confirmed = self.create_reservation(quantity=1)
        confirm_reservation(
            reservation_id=confirmed.pk,
            p24_order_id=987654,
        )
        old_timestamp = timezone.now() - timedelta(days=31)
        Reservation.objects.filter(
            pk__in=[old_failed.pk, old_expired.pk, confirmed.pk]
        ).update(updated_at=old_timestamp)

        stdout = StringIO()
        call_command("expire_rzut_reservations", stdout=stdout)

        self.assertFalse(
            Reservation.objects.filter(
                pk__in=[old_failed.pk, old_expired.pk]
            ).exists()
        )
        self.assertEqual(
            Reservation.objects.filter(
                pk__in=[recent_failed.pk, confirmed.pk]
            ).count(),
            2,
        )
        self.assertIn("Usunięto stare Rezerwacje: 2", stdout.getvalue())

    def test_repeated_command_does_not_release_pool_twice(self):
        reservation = self.create_reservation(
            now=timezone.now() - timedelta(minutes=16)
        )

        call_command("expire_rzut_reservations", stdout=StringIO())
        second_stdout = StringIO()
        call_command("expire_rzut_reservations", stdout=second_stdout)

        reservation.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.EXPIRED)
        self.assertEqual(self.item.allocated_quantity, 0)
        self.assertIn("Wygaszono Rezerwacje: 0", second_stdout.getvalue())

    def test_command_leaves_future_and_terminal_reservations_unchanged(self):
        future = self.create_reservation(quantity=1)
        failed = self.create_reservation(quantity=1)
        fail_reservation(failed)
        confirmed = self.create_reservation(quantity=1)
        confirm_reservation(
            reservation_id=confirmed.pk,
            p24_order_id=987654,
        )

        call_command("expire_rzut_reservations", stdout=StringIO())

        future.refresh_from_db()
        failed.refresh_from_db()
        confirmed.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(future.status, Reservation.Status.ACTIVE)
        self.assertEqual(failed.status, Reservation.Status.FAILED)
        self.assertEqual(confirmed.status, Reservation.Status.CONFIRMED)
        self.assertEqual(self.item.allocated_quantity, 2)


class TestReservationExpiryHttpFallback(ReservationExpiryTestCase):
    def test_opening_rzut_cart_expires_due_reservations(self):
        reservation = self.create_reservation(
            now=timezone.now() - timedelta(minutes=16)
        )

        response = self.client.get(reverse("shop:rzut_cart"))

        reservation.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(reservation.status, Reservation.Status.EXPIRED)
        self.assertEqual(self.item.allocated_quantity, 0)

    def test_opening_checkout_expires_due_reservations(self):
        reservation = self.create_reservation(
            now=timezone.now() - timedelta(minutes=16)
        )
        self.client.post(
            reverse("shop:rzut_cart_add", args=[self.item.pk])
        )

        response = self.client.get(reverse("shop:rzut_checkout"))

        reservation.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(reservation.status, Reservation.Status.EXPIRED)
        self.assertEqual(self.item.allocated_quantity, 0)


class TestReservationRetry(ReservationExpiryTestCase):
    def test_customer_can_restore_cart_from_expired_reservation(self):
        reservation = self.create_reservation(
            now=timezone.now() - timedelta(minutes=16)
        )
        call_command("expire_rzut_reservations", stdout=StringIO())

        return_response = self.client.get(
            reverse("shop:rzut_p24_return")
            + f"?session={reservation.p24_session_id}"
        )
        retry_url = reverse(
            "shop:rzut_reservation_retry",
            args=[reservation.p24_session_id],
        )
        retry_response = self.client.post(retry_url)

        reservation.refresh_from_db()
        self.assertContains(return_response, retry_url)
        self.assertContains(return_response, "Przywróć Koszyk Rzutu")
        self.assertRedirects(retry_response, reverse("shop:rzut_cart"))
        self.assertEqual(reservation.status, Reservation.Status.EXPIRED)
        self.assertEqual(
            self.client.session["rzut_cart"]["items"][str(self.item.pk)],
            {"quantity": 2, "price": "26.00"},
        )

    @patch("shop.views.register_rzut_transaction", return_value="token-456")
    def test_retry_creates_new_reservation_after_current_validation(
        self,
        register_payment,
    ):
        expired = self.create_reservation(
            now=timezone.now() - timedelta(minutes=16)
        )
        call_command("expire_rzut_reservations", stdout=StringIO())
        self.client.post(
            reverse(
                "shop:rzut_reservation_retry",
                args=[expired.p24_session_id],
            )
        )

        response = self.client.post(
            reverse("shop:rzut_checkout"),
            {
                "name": "Jan Kowalski",
                "email": "jan@example.com",
                "phone": "",
                "notes": "",
                "pickup_slot": "10:00:00|11:00:00",
                "consent_data": "on",
                "consent_terms": "on",
            },
        )

        expired.refresh_from_db()
        current = Reservation.objects.exclude(pk=expired.pk).get()
        self.item.refresh_from_db()
        self.assertRedirects(
            response,
            "https://sandbox.przelewy24.pl/trnRequest/token-456",
            fetch_redirect_response=False,
        )
        self.assertEqual(expired.status, Reservation.Status.EXPIRED)
        self.assertEqual(current.status, Reservation.Status.ACTIVE)
        self.assertNotEqual(current.p24_session_id, expired.p24_session_id)
        self.assertEqual(self.item.allocated_quantity, 2)
        register_payment.assert_called_once()

    def test_retry_does_not_silently_accept_changed_price(self):
        expired = self.create_reservation(
            now=timezone.now() - timedelta(minutes=16)
        )
        call_command("expire_rzut_reservations", stdout=StringIO())
        RzutItem.objects.filter(pk=self.item.pk).update(
            price=Decimal("28.00")
        )
        self.client.post(
            reverse(
                "shop:rzut_reservation_retry",
                args=[expired.p24_session_id],
            )
        )

        response = self.client.get(reverse("shop:rzut_checkout"), follow=True)

        self.assertContains(response, "Zaakceptuj aktualną sumę")
        self.assertEqual(Reservation.objects.count(), 1)

    def test_retry_rechecks_current_availability(self):
        expired = self.create_reservation(
            now=timezone.now() - timedelta(minutes=16),
            quantity=10,
        )
        call_command("expire_rzut_reservations", stdout=StringIO())
        create_reservation(
            rzut_id=self.rzut.pk,
            lines=[ReservationLineRequest(self.item.pk, 10, self.item.price)],
            checkout=ReservationCheckoutData(
                name="Anna Nowak",
                email="anna@example.com",
                phone="",
                notes="",
                pickup_starts_at=time(10, 0),
                pickup_ends_at=time(11, 0),
            ),
        )
        self.client.post(
            reverse(
                "shop:rzut_reservation_retry",
                args=[expired.p24_session_id],
            )
        )

        response = self.client.get(reverse("shop:rzut_checkout"), follow=True)

        self.assertContains(response, "nie jest już dostępna")
        self.assertEqual(Reservation.objects.count(), 2)

    def test_customer_can_restore_cart_from_failed_reservation(self):
        failed = self.create_reservation(quantity=1)
        fail_reservation(failed)
        cart_session = self.client.session
        cart_session.pop("rzut_cart", None)
        cart_session.save()

        response = self.client.post(
            reverse(
                "shop:rzut_reservation_retry",
                args=[failed.p24_session_id],
            )
        )

        failed.refresh_from_db()
        self.assertRedirects(response, reverse("shop:rzut_cart"))
        self.assertEqual(failed.status, Reservation.Status.FAILED)
        self.assertEqual(
            self.client.session["rzut_cart"]["items"][str(self.item.pk)][
                "quantity"
            ],
            1,
        )


class TestReservationAdmin(ReservationExpiryTestCase):
    def test_admin_distinguishes_each_reservation_status(self):
        self.create_reservation(quantity=1)
        expired = self.create_reservation(
            now=timezone.now() - timedelta(minutes=16),
            quantity=1,
        )
        expire_due_reservations(now=expired.expires_at)
        failed = self.create_reservation(quantity=1)
        fail_reservation(failed)
        confirmed = self.create_reservation(quantity=1)
        confirm_reservation(
            reservation_id=confirmed.pk,
            p24_order_id=987654,
        )
        admin_user = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="testpass123",
        )
        self.client.force_login(admin_user)

        response = self.client.get(
            reverse("admin:shop_reservation_changelist")
        )

        self.assertEqual(response.status_code, 200)
        for label in ["Aktywna", "Potwierdzona", "Wygasła", "Nieudana"]:
            self.assertContains(
                response,
                f'<td class="field-status">{label}</td>',
                html=True,
            )

    def test_admin_cannot_delete_reservation_outside_its_lifecycle(self):
        reservation = self.create_reservation(quantity=1)
        admin_user = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="testpass123",
        )
        self.client.force_login(admin_user)

        changelist = self.client.get(
            reverse("admin:shop_reservation_changelist")
        )
        delete_response = self.client.post(
            reverse(
                "admin:shop_reservation_delete",
                args=[reservation.pk],
            )
        )

        self.assertNotContains(changelist, "delete_selected")
        self.assertEqual(delete_response.status_code, 403)
        self.assertTrue(Reservation.objects.filter(pk=reservation.pk).exists())
