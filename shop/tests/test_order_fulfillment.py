from datetime import time, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from shop.models import OrderEdition, Product, RzutItem, RzutOrder, RzutOrderItem


class RzutOrderAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser(
            email="realizacja@example.com",
            password="testpass123",
        )
        cls.rzut = OrderEdition.objects.create(
            title="Rzut sobotni",
            pickup_date=timezone.localdate() + timedelta(days=2),
            pickup_place_name="Kuchenna Komitywa",
            pickup_address="ul. Bukowa 14, Białystok",
            pickup_starts_at=time(10, 0),
            pickup_ends_at=time(13, 0),
            pickup_instructions="Wejście od ogrodu.",
        )
        product = Product.objects.create(
            title="Chleb wiejski",
            description="Chleb na zakwasie.",
            price=Decimal("24.00"),
            default_portion="bochenek",
            is_available_in_shop=False,
        )
        cls.rzut_item = RzutItem.objects.create(
            rzut=cls.rzut,
            product=product,
            price=Decimal("24.00"),
            portion="bochenek",
            pool=10,
        )

    def setUp(self):
        self.client.force_login(self.admin_user)
        self.order = RzutOrder.objects.create(
            is_manual=True,
            rzut=self.rzut,
            customer_name="Jan Kowalski",
            customer_email="jan@example.com",
            customer_phone="500600700",
            customer_notes="Bez torby.",
            pickup_starts_at=time(10, 0),
            pickup_ends_at=time(11, 0),
            subtotal=Decimal("48.00"),
            total=Decimal("48.00"),
            payment_status=RzutOrder.PaymentStatus.PAID,
            payment_method=RzutOrder.PaymentMethod.CASH,
        )
        RzutOrderItem.objects.create(
            order=self.order,
            rzut_item=self.rzut_item,
            product_name="Chleb wiejski",
            portion="bochenek",
            unit_price=Decimal("24.00"),
            quantity=2,
            line_total=Decimal("48.00"),
        )

    def change_url(self):
        return reverse("admin:shop_rzutorder_change", args=[self.order.pk])

    def create_order(self, *, name, email, stage=RzutOrder.FulfillmentStage.NEW):
        return RzutOrder.objects.create(
            is_manual=True,
            rzut=self.rzut,
            customer_name=name,
            customer_email=email,
            customer_phone="",
            customer_notes="",
            pickup_starts_at=time(12, 0),
            pickup_ends_at=time(13, 0),
            subtotal=Decimal("24.00"),
            total=Decimal("24.00"),
            payment_status=RzutOrder.PaymentStatus.PAID,
            payment_method=RzutOrder.PaymentMethod.CASH,
            fulfillment_stage=stage,
        )


class TestRzutOrderFulfillmentAdmin(RzutOrderAdminTestCase):
    def test_admin_corrects_customer_data_and_stage_with_visible_audit(self):
        response = self.client.post(
            self.change_url(),
            {
                "customer_name": "Janina Kowalska",
                "customer_email": "JANINA@EXAMPLE.COM",
                "customer_phone": "+48 111 222 333",
                "customer_notes": "Odbierze córka.",
                "pickup_slot": "11:00:00|12:00:00",
                "internal_note": "Telefonicznie potwierdzono korektę.",
                "payment_status": self.order.payment_status,
                "fulfillment_stage": RzutOrder.FulfillmentStage.PREPARING,
                "items-TOTAL_FORMS": "1",
                "items-INITIAL_FORMS": "1",
                "items-MIN_NUM_FORMS": "0",
                "items-MAX_NUM_FORMS": "0",
                "items-0-id": str(self.order.items.get().pk),
                "events-TOTAL_FORMS": "0",
                "events-INITIAL_FORMS": "0",
                "events-MIN_NUM_FORMS": "0",
                "events-MAX_NUM_FORMS": "0",
                "_continue": "Zapisz i kontynuuj edycję",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Janina Kowalska")
        self.assertContains(response, "janina@example.com")
        self.assertContains(response, "+48 111 222 333")
        self.assertContains(response, "Odbierze córka.")
        self.assertContains(response, "11:00")
        self.assertContains(response, "12:00")
        self.assertContains(response, "Telefonicznie potwierdzono korektę.")
        self.assertContains(response, "W przygotowaniu")
        self.assertContains(response, "Opłacona")
        self.assertContains(response, "48,00")
        self.assertContains(response, "Chleb wiejski")
        self.assertContains(response, "Zmiana danych Zamówienia Rzutu")
        self.assertContains(response, "Zmiana Etapu Realizacji")
        self.assertContains(response, self.admin_user.email)

        public_page = self.client.get(
            reverse("shop:rzut_order_detail", args=[self.order.number])
        )
        self.assertNotContains(
            public_page,
            "Telefonicznie potwierdzono korektę.",
        )

    def test_admin_rejects_skipped_and_terminal_stage_transitions(self):
        response = self.client.post(
            self.change_url(),
            {
                "customer_name": self.order.customer_name,
                "customer_email": self.order.customer_email,
                "customer_phone": self.order.customer_phone,
                "customer_notes": self.order.customer_notes,
                "pickup_slot": "10:00:00|11:00:00",
                "internal_note": "",
                "payment_status": self.order.payment_status,
                "fulfillment_stage": RzutOrder.FulfillmentStage.READY,
                "items-TOTAL_FORMS": "1",
                "items-INITIAL_FORMS": "1",
                "items-MIN_NUM_FORMS": "0",
                "items-MAX_NUM_FORMS": "0",
                "items-0-id": str(self.order.items.get().pk),
                "events-TOTAL_FORMS": "0",
                "events-INITIAL_FORMS": "0",
                "events-MIN_NUM_FORMS": "0",
                "events-MAX_NUM_FORMS": "0",
                "_continue": "Zapisz i kontynuuj edycję",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Nie można zmienić Etapu Realizacji z „Nowe” na „Gotowe”",
        )
        public_page = self.client.get(
            reverse("shop:rzut_order_detail", args=[self.order.number])
        )
        self.assertContains(public_page, "Nowe")
        self.assertContains(public_page, "Opłacona")

    def test_admin_marks_pending_payment_paid_without_changing_fulfillment(self):
        self.order.payment_status = RzutOrder.PaymentStatus.PENDING
        self.order.save(update_fields=["payment_status"])

        response = self.client.post(
            self.change_url(),
            {
                "customer_name": self.order.customer_name,
                "customer_email": self.order.customer_email,
                "customer_phone": self.order.customer_phone,
                "customer_notes": self.order.customer_notes,
                "pickup_slot": "10:00:00|11:00:00",
                "internal_note": "Gotówka przyjęta przy odbiorze.",
                "payment_status": RzutOrder.PaymentStatus.PAID,
                "fulfillment_stage": RzutOrder.FulfillmentStage.NEW,
                "items-TOTAL_FORMS": "1",
                "items-INITIAL_FORMS": "1",
                "items-MIN_NUM_FORMS": "0",
                "items-MAX_NUM_FORMS": "0",
                "items-0-id": str(self.order.items.get().pk),
                "events-TOTAL_FORMS": "0",
                "events-INITIAL_FORMS": "0",
                "events-MIN_NUM_FORMS": "0",
                "events-MAX_NUM_FORMS": "0",
                "_continue": "Zapisz i kontynuuj edycję",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Opłacona")
        self.assertContains(response, "Nowe")
        self.assertContains(response, "Zmiana Statusu Płatności")
        self.assertContains(response, self.admin_user.email)
        public_page = self.client.get(
            reverse("shop:rzut_order_detail", args=[self.order.number])
        )
        self.assertContains(public_page, "Opłacona")
        self.assertContains(public_page, "Nowe")

    def test_admin_cancellation_releases_order_quantities_and_audits(self):
        self.order.fulfillment_stage = RzutOrder.FulfillmentStage.READY
        self.order.save(update_fields=["fulfillment_stage"])
        RzutItem.objects.filter(pk=self.rzut_item.pk).update(
            allocated_quantity=2
        )

        data = {
                "customer_name": self.order.customer_name,
                "customer_email": self.order.customer_email,
                "customer_phone": self.order.customer_phone,
                "customer_notes": self.order.customer_notes,
                "pickup_slot": "10:00:00|11:00:00",
                "internal_note": "Klient anulował telefonicznie.",
                "payment_status": self.order.payment_status,
                "fulfillment_stage": RzutOrder.FulfillmentStage.CANCELLED,
                "items-TOTAL_FORMS": "1",
                "items-INITIAL_FORMS": "1",
                "items-MIN_NUM_FORMS": "0",
                "items-MAX_NUM_FORMS": "0",
                "items-0-id": str(self.order.items.get().pk),
                "events-TOTAL_FORMS": "0",
                "events-INITIAL_FORMS": "0",
                "events-MIN_NUM_FORMS": "0",
                "events-MAX_NUM_FORMS": "0",
                "_continue": "Zapisz i kontynuuj edycję",
            }
        confirmation = self.client.post(self.change_url(), data)
        self.order.refresh_from_db()
        self.rzut_item.refresh_from_db()
        self.assertEqual(confirmation.status_code, 200)
        self.assertContains(confirmation, "Potwierdź anulowanie")
        self.assertContains(confirmation, "Przywróć sztuki do Puli")
        self.assertEqual(
            self.order.fulfillment_stage,
            RzutOrder.FulfillmentStage.READY,
        )
        self.assertEqual(self.rzut_item.allocated_quantity, 2)

        data.update(confirm_cancellation="1")
        invalid = self.client.post(self.change_url(), data)
        self.order.refresh_from_db()
        self.rzut_item.refresh_from_db()
        self.assertContains(invalid, "Wybierz, co zrobić ze sztukami")
        self.assertEqual(
            self.order.fulfillment_stage,
            RzutOrder.FulfillmentStage.READY,
        )
        self.assertEqual(self.rzut_item.allocated_quantity, 2)

        data["restore_pool"] = "1"
        response = self.client.post(
            self.change_url(),
            data,
            follow=True,
        )

        self.order.refresh_from_db()
        self.rzut_item.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.order.fulfillment_stage,
            RzutOrder.FulfillmentStage.CANCELLED,
        )
        self.assertEqual(self.rzut_item.allocated_quantity, 0)
        self.assertEqual(self.rzut_item.pool, 10)
        self.assertContains(response, "Zmiana Etapu Realizacji")
        self.assertContains(response, "pool_restored")

    def test_cancellation_can_keep_prepared_quantity_out_of_pool(self):
        self.order.fulfillment_stage = RzutOrder.FulfillmentStage.PREPARING
        self.order.save(update_fields=["fulfillment_stage"])
        RzutItem.objects.filter(pk=self.rzut_item.pk).update(
            pool=2,
            allocated_quantity=2,
        )
        data = {
            "customer_name": self.order.customer_name,
            "customer_email": self.order.customer_email,
            "customer_phone": self.order.customer_phone,
            "customer_notes": self.order.customer_notes,
            "pickup_slot": "10:00:00|11:00:00",
            "internal_note": "Sztuki już przygotowane.",
            "payment_status": self.order.payment_status,
            "fulfillment_stage": RzutOrder.FulfillmentStage.CANCELLED,
            "items-TOTAL_FORMS": "1",
            "items-INITIAL_FORMS": "1",
            "items-MIN_NUM_FORMS": "0",
            "items-MAX_NUM_FORMS": "0",
            "items-0-id": str(self.order.items.get().pk),
            "events-TOTAL_FORMS": "0",
            "events-INITIAL_FORMS": "0",
            "events-MIN_NUM_FORMS": "0",
            "events-MAX_NUM_FORMS": "0",
            "confirm_cancellation": "1",
            "restore_pool": "0",
            "_continue": "Zapisz i kontynuuj edycję",
        }

        response = self.client.post(self.change_url(), data, follow=True)

        self.rzut_item.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.rzut_item.allocated_quantity, 0)
        self.assertEqual(self.rzut_item.pool, 2)
        self.assertEqual(self.rzut_item.withdrawn_quantity, 2)
        self.assertContains(response, "pool_restored")


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="Kuchenna Komitywa <noreply@example.com>",
    PUBLIC_SITE_URL="https://example.com",
)
class TestReadyNotificationAdmin(RzutOrderAdminTestCase):
    def test_action_previews_selected_recipients_before_sending(self):
        self.order.fulfillment_stage = RzutOrder.FulfillmentStage.PREPARING
        self.order.save(update_fields=["fulfillment_stage"])

        response = self.client.post(
            reverse("admin:shop_rzutorder_changelist"),
            {
                "action": "send_ready_notifications",
                "_selected_action": [str(self.order.pk)],
                "index": "0",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Potwierdź wiadomość „gotowe do odbioru”")
        self.assertContains(response, self.order.number)
        self.assertContains(response, self.order.customer_name)
        self.assertContains(response, self.order.customer_email)
        self.assertContains(response, "W przygotowaniu")
        self.assertContains(response, "Wyślij wiadomość do 1 Klienta")

    def test_confirmed_action_marks_ready_sends_and_records_audit(self):
        self.order.fulfillment_stage = RzutOrder.FulfillmentStage.PREPARING
        self.order.save(update_fields=["fulfillment_stage"])

        response = self.client.post(
            reverse("admin:shop_rzutorder_changelist"),
            {
                "action": "send_ready_notifications",
                "_selected_action": [str(self.order.pk)],
                "confirm_ready": "1",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wysłano wiadomość „gotowe” do 1 Klienta")
        self.assertEqual(len(mail.outbox), 1)

    def test_action_sends_to_many_selected_orders(self):
        self.order.fulfillment_stage = RzutOrder.FulfillmentStage.PREPARING
        self.order.save(update_fields=["fulfillment_stage"])
        second = self.create_order(
            name="Anna Nowak",
            email="anna@example.com",
            stage=RzutOrder.FulfillmentStage.PREPARING,
        )
        action_url = reverse("admin:shop_rzutorder_changelist")
        selection = [str(self.order.pk), str(second.pk)]

        preview = self.client.post(
            action_url,
            {
                "action": "send_ready_notifications",
                "_selected_action": selection,
                "index": "0",
            },
        )
        self.assertContains(preview, "Wyślij wiadomość do 2 Klientów")
        self.assertContains(preview, "anna@example.com")

        response = self.client.post(
            action_url,
            {
                "action": "send_ready_notifications",
                "_selected_action": selection,
                "confirm_ready": "1",
            },
            follow=True,
        )
        self.assertContains(response, "Wysłano wiadomość „gotowe” do 2 Klientów")
        self.assertEqual(
            {message.to[0] for message in mail.outbox},
            {"jan@example.com", "anna@example.com"},
        )
        self.assertEqual(mail.outbox[0].to, [self.order.customer_email])
        self.assertIn("gotowe do odbioru", mail.outbox[0].subject.lower())
        self.assertIn(self.order.number, mail.outbox[0].body)
        self.assertIn("Rzut sobotni", mail.outbox[0].body)
        self.assertIn("11:00", mail.outbox[0].body)
        self.assertIn(
            f"https://example.com{reverse('shop:rzut_order_detail', args=[self.order.number])}",
            mail.outbox[0].body,
        )

        public_page = self.client.get(
            reverse("shop:rzut_order_detail", args=[self.order.number])
        )
        self.assertContains(public_page, "Gotowe")

        audit_page = self.client.get(self.change_url())
        self.assertContains(audit_page, "Wysłanie wiadomości „gotowe”")
        self.assertContains(audit_page, self.admin_user.email)
        self.assertContains(audit_page, "Opłacona")

    @patch(
        "shop.emails.EmailMessage.send",
        side_effect=RuntimeError("SMTP niedostępne"),
    )
    def test_smtp_failure_keeps_ready_stage_and_exposes_retry(self, send_mail):
        self.order.fulfillment_stage = RzutOrder.FulfillmentStage.PREPARING
        self.order.save(update_fields=["fulfillment_stage"])

        response = self.client.post(
            reverse("admin:shop_rzutorder_changelist"),
            {
                "action": "send_ready_notifications",
                "_selected_action": [str(self.order.pk)],
                "confirm_ready": "1",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nie udało się wysłać wiadomości do 1 Klienta")
        public_page = self.client.get(
            reverse("shop:rzut_order_detail", args=[self.order.number])
        )
        self.assertContains(public_page, "Gotowe")
        audit_page = self.client.get(self.change_url())
        self.assertContains(audit_page, "SMTP niedostępne")
        self.assertContains(audit_page, "Błąd wiadomości „gotowe”")
        self.assertContains(audit_page, "ponów wysyłkę")
        send_mail.assert_called_once()

    def test_action_warns_and_excludes_already_notified_order(self):
        self.order.fulfillment_stage = RzutOrder.FulfillmentStage.PREPARING
        self.order.save(update_fields=["fulfillment_stage"])
        action_url = reverse("admin:shop_rzutorder_changelist")
        self.client.post(
            action_url,
            {
                "action": "send_ready_notifications",
                "_selected_action": [str(self.order.pk)],
                "confirm_ready": "1",
            },
        )
        self.assertEqual(len(mail.outbox), 1)

        preview = self.client.post(
            action_url,
            {
                "action": "send_ready_notifications",
                "_selected_action": [str(self.order.pk)],
                "index": "0",
            },
        )

        self.assertEqual(preview.status_code, 200)
        self.assertContains(preview, "Wiadomość została już wysłana")
        self.assertContains(preview, self.order.number)
        self.assertContains(preview, "Brak wiadomości do wysłania")
        self.assertNotContains(preview, 'name="confirm_ready"', html=False)
        self.assertEqual(len(mail.outbox), 1)


class TestPickupChangeAdmin(RzutOrderAdminTestCase):
    def rzut_change_data(self, **overrides):
        data = {
            "title": self.rzut.title,
            "slug": self.rzut.slug,
            "status": self.rzut.status,
            "description": self.rzut.description,
            "pickup_date": self.rzut.pickup_date.isoformat(),
            "pickup_place_name": "Nowa Kuchnia",
            "pickup_address": "ul. Lipowa 8, Białystok",
            "pickup_starts_at": "11:00:00",
            "pickup_ends_at": "14:00:00",
            "pickup_instructions": "Wejście od dziedzińca.",
            "payment_details": self.rzut.payment_details,
            "show_upcoming_menu": "on",
            "show_in_archive": "on",
            "items-TOTAL_FORMS": "1",
            "items-INITIAL_FORMS": "1",
            "items-MIN_NUM_FORMS": "0",
            "items-MAX_NUM_FORMS": "1000",
            "items-0-id": str(self.rzut_item.pk),
            "items-0-product": str(self.rzut_item.product_id),
            "items-0-price": "24.00",
            "items-0-portion": "bochenek",
            "items-0-pool": "10",
            "items-0-per_customer_limit": "",
            "items-0-sort_order": "0",
            "items-0-is_active": "on",
            "items-0-production_note": "",
            "_save": "Zapisz",
        }
        data.update(overrides)
        return data

    def test_pickup_change_with_orders_requires_before_after_confirmation(self):
        response = self.client.post(
            reverse("admin:shop_orderedition_change", args=[self.rzut.pk]),
            self.rzut_change_data(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Potwierdź zmianę danych odbioru")
        self.assertContains(response, "Kuchenna Komitywa")
        self.assertContains(response, "ul. Bukowa 14, Białystok")
        self.assertContains(response, "10:00–13:00")
        self.assertContains(response, "Nowa Kuchnia")
        self.assertContains(response, "ul. Lipowa 8, Białystok")
        self.assertContains(response, "11:00–14:00")
        self.assertContains(response, "1 istniejące Zamówienie Rzutu")
        self.assertContains(response, "Potwierdzam zmianę odbioru")

        public_page = self.client.get(
            reverse("shop:rzut_order_detail", args=[self.order.number])
        )
        self.assertContains(public_page, "ul. Bukowa 14, Białystok")
        self.assertNotContains(public_page, "ul. Lipowa 8, Białystok")

    def test_pickup_change_reports_slots_outside_shortened_window(self):
        late_order = self.create_order(
            name="Anna Późna",
            email="anna@example.com",
        )
        late_order.pickup_starts_at = time(12, 0)
        late_order.pickup_ends_at = time(13, 0)
        late_order.save(update_fields=["pickup_starts_at", "pickup_ends_at"])

        response = self.client.post(
            reverse("admin:shop_orderedition_change", args=[self.rzut.pk]),
            self.rzut_change_data(
                pickup_starts_at="10:00:00",
                pickup_ends_at="12:00:00",
            ),
        )

        self.rzut.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "nie mieści się w nowych godzinach")
        self.assertContains(response, late_order.number)
        self.assertNotContains(response, "Potwierdzam zmianę odbioru")
        self.assertEqual(self.rzut.pickup_ends_at, time(13, 0))

    def test_confirmed_pickup_change_opens_recipient_preview_and_audits(self):
        response = self.client.post(
            reverse("admin:shop_orderedition_change", args=[self.rzut.pk]),
            self.rzut_change_data(confirm_pickup_change="1"),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wyślij wiadomość o zmianie odbioru")
        self.assertContains(response, self.order.number)
        self.assertContains(response, self.order.customer_name)
        self.assertContains(response, self.order.customer_email)
        self.assertContains(response, "Nowa Kuchnia")
        self.assertContains(response, "ul. Lipowa 8, Białystok")
        self.assertContains(response, "11:00–14:00")
        self.assertContains(response, "Wyślij wiadomość do 1 Klienta")

        public_page = self.client.get(
            reverse("shop:rzut_order_detail", args=[self.order.number])
        )
        self.assertContains(public_page, "ul. Lipowa 8, Białystok")
        self.assertContains(public_page, "11:00")
        self.assertContains(public_page, "12:00")
        self.order.refresh_from_db()
        self.assertEqual(self.order.pickup_starts_at, time(11, 0))
        self.assertEqual(self.order.pickup_ends_at, time(12, 0))
        audit_page = self.client.get(self.change_url())
        self.assertContains(audit_page, "Zmiana odbioru Rzutu")
        self.assertContains(audit_page, self.admin_user.email)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="Kuchenna Komitywa <noreply@example.com>",
        PUBLIC_SITE_URL="https://example.com",
    )
    def test_pickup_message_is_bulk_and_excludes_terminal_orders(self):
        second = self.create_order(
            name="Anna Nowak",
            email="anna@example.com",
        )
        cancelled = self.create_order(
            name="Adam Anulowany",
            email="adam@example.com",
            stage=RzutOrder.FulfillmentStage.CANCELLED,
        )
        picked_up = self.create_order(
            name="Piotr Odebrany",
            email="piotr@example.com",
            stage=RzutOrder.FulfillmentStage.PICKED_UP,
        )
        saved = self.client.post(
            reverse("admin:shop_orderedition_change", args=[self.rzut.pk]),
            self.rzut_change_data(confirm_pickup_change="1"),
        )
        notification_url = saved["Location"]

        preview = self.client.get(notification_url)
        self.assertContains(preview, "Wyślij wiadomość do 2 Klientów")
        self.assertContains(preview, self.order.customer_email)
        self.assertContains(preview, second.customer_email)
        self.assertNotContains(preview, cancelled.customer_email)
        self.assertNotContains(preview, picked_up.customer_email)

        self.client.post(
            notification_url,
            {"confirm_pickup_notification": "1"},
        )
        self.assertEqual(
            {message.to[0] for message in mail.outbox},
            {self.order.customer_email, second.customer_email},
        )

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="Kuchenna Komitywa <noreply@example.com>",
        PUBLIC_SITE_URL="https://example.com",
    )
    def test_pickup_smtp_failure_is_visible_and_can_be_retried(self):
        saved = self.client.post(
            reverse("admin:shop_orderedition_change", args=[self.rzut.pk]),
            self.rzut_change_data(confirm_pickup_change="1"),
        )
        notification_url = saved["Location"]

        with patch(
            "shop.emails.EmailMessage.send",
            side_effect=RuntimeError("SMTP niedostępne"),
        ):
            failed = self.client.post(
                notification_url,
                {"confirm_pickup_notification": "1"},
                follow=True,
            )

        self.assertContains(failed, "Nie udało się wysłać wiadomości do 1 Klienta")
        self.assertContains(failed, "SMTP niedostępne")
        self.assertContains(failed, "Wyślij wiadomość do 1 Klienta")

        retried = self.client.post(
            notification_url,
            {"confirm_pickup_notification": "1"},
            follow=True,
        )
        self.assertContains(
            retried,
            "Wysłano wiadomość o zmianie odbioru do 1 Klienta",
        )
        self.assertEqual(len(mail.outbox), 1)
        audit_page = self.client.get(self.change_url())
        self.assertContains(
            audit_page,
            "Błąd wiadomości o zmianie odbioru",
        )
        self.assertContains(
            audit_page,
            "Wysłanie wiadomości o zmianie odbioru",
        )

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="Kuchenna Komitywa <noreply@example.com>",
        PUBLIC_SITE_URL="https://example.com",
    )
    def test_confirmed_pickup_message_sends_once_and_records_audit(self):
        saved = self.client.post(
            reverse("admin:shop_orderedition_change", args=[self.rzut.pk]),
            self.rzut_change_data(confirm_pickup_change="1"),
        )
        notification_url = saved["Location"]

        response = self.client.post(
            notification_url,
            {"confirm_pickup_notification": "1"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Wysłano wiadomość o zmianie odbioru do 1 Klienta",
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.order.customer_email])
        self.assertIn("zmiana odbioru", mail.outbox[0].subject.lower())
        self.assertIn(self.order.number, mail.outbox[0].body)
        self.assertIn("Kuchenna Komitywa", mail.outbox[0].body)
        self.assertIn("ul. Bukowa 14, Białystok", mail.outbox[0].body)
        self.assertIn("Nowa Kuchnia", mail.outbox[0].body)
        self.assertIn("ul. Lipowa 8, Białystok", mail.outbox[0].body)
        self.assertIn("11:00–14:00", mail.outbox[0].body)

        preview = self.client.get(notification_url)
        self.assertContains(preview, "Wysłano")
        self.assertNotContains(
            preview,
            'name="confirm_pickup_notification"',
            html=False,
        )
        audit_page = self.client.get(self.change_url())
        self.assertContains(
            audit_page,
            "Wysłanie wiadomości o zmianie odbioru",
        )
        self.assertContains(audit_page, self.admin_user.email)
