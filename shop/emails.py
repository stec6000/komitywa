import logging

from django.conf import settings
from django.core.mail import EmailMessage

from .models import Product

logger = logging.getLogger(__name__)


def send_order_confirmation(order):
    items_text = ""
    for pid, item in order.cart_snapshot.items():
        try:
            product = Product.objects.get(id=int(pid))
            items_text += (
                f"- {product.title} x{item['quantity']}"
                f" - {item['price']} z\u0142\n"
            )
        except Product.DoesNotExist:
            items_text += (
                f"- Produkt #{pid} x{item['quantity']}"
                f" - {item['price']} z\u0142\n"
            )

    body = (
        f"Cze\u015b\u0107 {order.name}!\n\n"
        f"Dzi\u0119kujemy za zam\u00f3wienie w Kuchennej Komitywie!\n\n"
        f"Numer zam\u00f3wienia: #{order.id}\n"
        f"Produkty:\n{items_text}\n"
        f"Suma: {order.total} z\u0142\n"
        f"Data odbioru: {order.pickup_date}\n\n"
        f"Do zobaczenia!\n\n"
        f"-- \n"
        f"Kuchenna Komitywa\n"
        f"https://kuchennakomitywa.pl"
    )

    email = EmailMessage(
        subject=f"Potwierdzenie zam\u00f3wienia #{order.id}"
        f" - Kuchenna Komitywa",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
    )
    email.send(fail_silently=False)


def send_ebook_delivery(order):
    ebook_products = []
    for pid in order.cart_snapshot.keys():
        try:
            product = Product.objects.get(id=int(pid), type="ebook")
            if product.ebook_file:
                ebook_products.append(product)
        except Product.DoesNotExist:
            continue

    if not ebook_products:
        return

    body = (
        f"Cze\u015b\u0107 {order.name}!\n\n"
        f"W za\u0142\u0105czniku znajdziesz zakupione ebooki.\n"
        f"\u017byczymy smacznej lektury!\n\n"
        f"-- \n"
        f"Kuchenna Komitywa\n"
        f"https://kuchennakomitywa.pl"
    )

    email = EmailMessage(
        subject="Twoje ebooki - Kuchenna Komitywa",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
    )

    for product in ebook_products:
        try:
            email.attach_file(product.ebook_file.path, "application/pdf")
        except Exception as exc:
            logger.error(
                "Failed to attach ebook for order %d, product %d: %s",
                order.id, product.id, exc,
            )

    try:
        email.send(fail_silently=False)
    except Exception as exc:
        logger.error(
            "Failed to send ebook email for order %d: %s",
            order.id, exc,
        )
