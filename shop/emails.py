import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils import timezone

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
        f"- \n"
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
        f"- \n"
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


def _format_pln(value):
    return f"{value:.2f}".replace(".", ",") + " zł"


def _rzut_order_items_text(order):
    return "\n".join(
        f"- {item.product_name} — {item.quantity} × {item.portion}, "
        f"{_format_pln(item.line_total)}"
        for item in order.items.all()
    )


def _rzut_order_public_url(order):
    path = reverse("shop:rzut_order_detail", args=[order.number])
    return f"{settings.PUBLIC_SITE_URL}{path}"


def send_rzut_order_customer_confirmation(order):
    rzut = order.rzut
    body = (
        f"Cześć {order.customer_name}!\n\n"
        "Płatność została potwierdzona, a Twoje Zamówienie Rzutu "
        "jest przyjęte.\n\n"
        f"Numer Zamówienia: {order.number}\n"
        f"Rzut: {rzut.title}\n"
        f"Pozycje Zamówienia:\n{_rzut_order_items_text(order)}\n\n"
        f"Suma: {_format_pln(order.total)}\n"
        f"Odbiór: {rzut.pickup_date:%d.%m.%Y}, "
        f"{order.pickup_starts_at:%H:%M}–{order.pickup_ends_at:%H:%M}\n"
        f"Miejsce: {rzut.pickup_place_name}, {rzut.pickup_address}\n"
        f"Instrukcja: {rzut.pickup_instructions}\n"
        f"Uwagi: {order.customer_notes or 'brak'}\n\n"
        f"Strona Zamówienia Rzutu: {_rzut_order_public_url(order)}\n\n"
        "Do zobaczenia!\n\n"
        "Kuchenna Komitywa\n"
        "https://kuchennakomitywa.pl"
    )
    EmailMessage(
        subject=f"Zamówienie Rzutu {order.number} — Kuchenna Komitywa",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.customer_email],
    ).send(fail_silently=False)


def send_rzut_order_owner_notification(order):
    rzut = order.rzut
    body = (
        "Nowe opłacone Zamówienie Rzutu.\n\n"
        f"Numer Zamówienia: {order.number}\n"
        f"Rzut: {rzut.title}\n"
        f"Klient: {order.customer_name}\n"
        f"E-mail: {order.customer_email}\n"
        f"Telefon: {order.customer_phone or 'brak'}\n"
        f"Pozycje Zamówienia:\n{_rzut_order_items_text(order)}\n\n"
        f"Suma: {_format_pln(order.total)}\n"
        f"Przedział Odbioru: {order.pickup_starts_at:%H:%M}–"
        f"{order.pickup_ends_at:%H:%M}\n"
        f"Uwagi: {order.customer_notes or 'brak'}\n"
        f"Strona Zamówienia Rzutu: {_rzut_order_public_url(order)}"
    )
    EmailMessage(
        subject=f"Nowe Zamówienie Rzutu {order.number}",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.CONTACT_EMAIL],
    ).send(fail_silently=False)


def send_rzut_order_attention_notification(order):
    EmailMessage(
        subject=f"PILNE: sprawdź Zamówienie Rzutu {order.number}",
        body=(
            f"{order.attention_message}\n\n"
            f"Numer Zamówienia: {order.number}\n"
            f"Rzut: {order.rzut.title}\n"
            f"Strona Zamówienia Rzutu: {_rzut_order_public_url(order)}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.CONTACT_EMAIL],
    ).send(fail_silently=False)


def deliver_rzut_order_notifications(order):
    deliveries = [
        (
            "customer_confirmation_sent_at",
            "customer_confirmation_error",
            send_rzut_order_customer_confirmation,
        ),
        (
            "owner_notification_sent_at",
            "owner_notification_error",
            send_rzut_order_owner_notification,
        ),
    ]
    if order.requires_attention:
        deliveries.append((
            "attention_notification_sent_at",
            "attention_notification_error",
            send_rzut_order_attention_notification,
        ))
    for sent_field, error_field, sender in deliveries:
        order.refresh_from_db(fields=[sent_field, error_field])
        if getattr(order, sent_field) is not None:
            continue
        try:
            sender(order)
        except Exception as exc:
            logger.error(
                "Failed to send %s for RzutOrder %d: %s",
                sent_field,
                order.pk,
                exc,
            )
            setattr(order, error_field, str(exc))
            order.save(update_fields=[error_field, "updated_at"])
        else:
            setattr(order, sent_field, timezone.now())
            setattr(order, error_field, "")
            order.save(
                update_fields=[sent_field, error_field, "updated_at"]
            )
