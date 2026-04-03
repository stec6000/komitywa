import os
import shutil
import tempfile
from decimal import Decimal
from unittest.mock import PropertyMock, patch

from django.core import mail
from django.test import TestCase, override_settings

from shop.models import Order, Product, ProductCategory


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="test@test.com",
)
class TestOrderConfirmationEmail(TestCase):
    def setUp(self):
        self.category, _ = ProductCategory.objects.get_or_create(
            slug="test-cat", defaults={"name": "Test"}
        )
        self.product = Product.objects.create(
            title="Testowy Produkt",
            slug="testowy-produkt",
            category=self.category,
            type="physical",
            description="Opis",
            price=Decimal("29.99"),
        )
        self.order = Order.objects.create(
            email="klient@example.com",
            name="Anna Nowak",
            pickup_date="piatek 10 stycznia",
            total=Decimal("59.98"),
            cart_snapshot={
                str(self.product.id): {
                    "quantity": 2,
                    "price": "29.99",
                }
            },
        )

    def test_sends_email(self):
        from shop.emails import send_order_confirmation

        send_order_confirmation(self.order)
        self.assertEqual(len(mail.outbox), 1)

    def test_correct_subject(self):
        from shop.emails import send_order_confirmation

        send_order_confirmation(self.order)
        self.assertIn(
            "Potwierdzenie zam\u00f3wienia", mail.outbox[0].subject
        )

    def test_correct_recipient(self):
        from shop.emails import send_order_confirmation

        send_order_confirmation(self.order)
        self.assertIn("klient@example.com", mail.outbox[0].to)

    def test_body_contains_polish_diacritics(self):
        from shop.emails import send_order_confirmation

        send_order_confirmation(self.order)
        body = mail.outbox[0].body
        self.assertIn("Cze\u015b\u0107", body)
        self.assertIn("Dzi\u0119kujemy", body)
        self.assertIn("zam\u00f3wieni", body)


class TestEbookDeliveryEmail(TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.category, _ = ProductCategory.objects.get_or_create(
            slug="ebooki", defaults={"name": "Ebooki"}
        )
        # Create ebook dir and PDF inside tmp media root
        ebooks_dir = os.path.join(self.tmp_dir, "ebooks")
        os.makedirs(ebooks_dir, exist_ok=True)
        self.pdf_path = os.path.join(ebooks_dir, "test-ebook.pdf")
        with open(self.pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 test content")

        self.product = Product.objects.create(
            title="Testowy Ebook",
            slug="testowy-ebook",
            category=self.category,
            type="ebook",
            description="Opis ebooka",
            price=Decimal("39.99"),
            ebook_file="ebooks/test-ebook.pdf",
        )
        self.order = Order.objects.create(
            email="klient@example.com",
            name="Anna Nowak",
            pickup_date="",
            total=Decimal("39.99"),
            cart_snapshot={
                str(self.product.id): {
                    "quantity": 1,
                    "price": "39.99",
                }
            },
        )

    def tearDown(self):
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="test@test.com",
    )
    def test_sends_email_with_attachment(self):
        from shop.emails import send_ebook_delivery

        # Patch ebook_file.path to point to our real temp file
        with patch.object(
            type(self.product.ebook_file),
            "path",
            new_callable=PropertyMock,
            return_value=self.pdf_path,
        ):
            send_ebook_delivery(self.order)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(len(mail.outbox[0].attachments) > 0)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="test@test.com",
)
class TestEbookDeliveryNoEbooks(TestCase):
    def setUp(self):
        self.category, _ = ProductCategory.objects.get_or_create(
            slug="fizyczne", defaults={"name": "Fizyczne"}
        )
        self.product = Product.objects.create(
            title="Fizyczny Produkt",
            slug="fizyczny-produkt",
            category=self.category,
            type="physical",
            description="Opis",
            price=Decimal("19.99"),
        )
        self.order = Order.objects.create(
            email="klient@example.com",
            name="Anna Nowak",
            pickup_date="piatek",
            total=Decimal("19.99"),
            cart_snapshot={
                str(self.product.id): {
                    "quantity": 1,
                    "price": "19.99",
                }
            },
        )

    def test_does_nothing_for_physical_only(self):
        from shop.emails import send_ebook_delivery

        send_ebook_delivery(self.order)
        self.assertEqual(len(mail.outbox), 0)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="test@test.com",
)
class TestEbookDeliveryAttachmentFailure(TestCase):
    def setUp(self):
        self.category, _ = ProductCategory.objects.get_or_create(
            slug="ebooki-fail", defaults={"name": "Ebooki Fail"}
        )
        self.product = Product.objects.create(
            title="Broken Ebook",
            slug="broken-ebook",
            category=self.category,
            type="ebook",
            description="Opis",
            price=Decimal("29.99"),
            ebook_file="nonexistent/path.pdf",
        )
        self.order = Order.objects.create(
            email="klient@example.com",
            name="Anna Nowak",
            pickup_date="",
            total=Decimal("29.99"),
            cart_snapshot={
                str(self.product.id): {
                    "quantity": 1,
                    "price": "29.99",
                }
            },
        )

    def test_does_not_raise_on_attachment_failure(self):
        from shop.emails import send_ebook_delivery

        # Should not raise even though ebook_file path is invalid
        send_ebook_delivery(self.order)

    @patch("shop.emails.logger")
    def test_logs_error_on_attachment_failure(self, mock_logger):
        from shop.emails import send_ebook_delivery

        send_ebook_delivery(self.order)
        mock_logger.error.assert_called()
