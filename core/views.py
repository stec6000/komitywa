import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse

from content.models import BlogPost
from recipes.models import Recipe
from shop.models import OrderEdition, Product

from .forms import CafeInquiryForm, WorkshopInterestForm
from .models import CafeLocation


logger = logging.getLogger(__name__)


def _kitchen_items():
    """Return the three newest public notes or recipes in one feed."""
    items = []
    posts = BlogPost.objects.published()[:3]
    recipes = (
        Recipe.objects.filter(is_published=True)
        .select_related("category")[:3]
    )

    for post in posts:
        items.append({
            "title": post.title,
            "description": post.excerpt,
            "label": "zapisek z kuchni",
            "url": post.get_absolute_url(),
            "image": None,
            "prep_time": None,
            "published_at": post.published_at or post.created_at,
        })

    for recipe in recipes:
        items.append({
            "title": recipe.title,
            "description": recipe.description,
            "label": recipe.category.name if recipe.category else "przepis",
            "url": reverse("recipes:detail", kwargs={"slug": recipe.slug}),
            "image": recipe.image,
            "prep_time": recipe.prep_time,
            "published_at": recipe.created_at,
        })

    return sorted(
        items,
        key=lambda item: item["published_at"],
        reverse=True,
    )[:3]


def _send_cafe_inquiry_notification(inquiry):
    body = "\n".join(
        [
            f"Lokal: {inquiry.venue_name}",
            f"Osoba kontaktowa: {inquiry.contact_name}",
            f"E-mail: {inquiry.email}",
            f"Telefon: {inquiry.phone or '—'}",
            f"Miasto: {inquiry.city}",
            f"Produkty: {inquiry.interested_products}",
            f"Częstotliwość: {inquiry.get_frequency_display()}",
            "",
            "Wiadomość:",
            inquiry.message,
        ]
    )
    send_mail(
        "Nowe zapytanie od kawiarni — Kuchenna Komitywa",
        body,
        settings.DEFAULT_FROM_EMAIL,
        [settings.CONTACT_EMAIL],
    )


def _send_workshop_notification(interest):
    body = "\n".join(
        [
            f"Imię: {interest.name}",
            f"E-mail: {interest.email}",
            f"Temat: {interest.get_topic_display()}",
            f"Preferowany termin: {interest.get_preferred_timing_display()}",
        ]
    )
    send_mail(
        "Nowe zainteresowanie wspólnym gotowaniem — Kuchenna Komitywa",
        body,
        settings.DEFAULT_FROM_EMAIL,
        [settings.CONTACT_EMAIL],
    )


def home(request):
    latest_recipes = list(
        Recipe.objects.filter(is_published=True)
        .select_related("category")[:4]
    )
    featured_recipe = latest_recipes[0] if latest_recipes else None
    feed_recipes = latest_recipes[1:4] if featured_recipe else latest_recipes[:3]

    current_edition = OrderEdition.objects.current()
    order_products = Product.objects.none()
    if current_edition:
        order_products = current_edition.products.filter(
            is_active=True,
            type="physical",
        ).select_related("category").order_by("sort_order", "title")

    return render(request, "pages/home.html", {
        "cafe_locations": CafeLocation.objects.filter(is_active=True),
        "current_edition": current_edition,
        "feed_recipes": feed_recipes,
        "featured_recipe": featured_recipe,
        "kitchen_items": _kitchen_items(),
        "order_products": order_products,
    })


def orders(request):
    current_edition = OrderEdition.objects.current()
    order_products = Product.objects.none()
    if current_edition:
        order_products = current_edition.products.filter(
            is_active=True,
            type="physical",
        ).select_related("category").order_by("sort_order", "title")

    archived_editions = OrderEdition.objects.filter(
        status=OrderEdition.Status.CLOSED,
        show_in_archive=True,
    ).order_by("-closes_at", "-created_at")

    return render(request, "pages/orders.html", {
        "archived_editions": archived_editions,
        "current_edition": current_edition,
        "order_products": order_products,
    })


def for_cafes(request):
    form = CafeInquiryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        inquiry = form.save()
        try:
            _send_cafe_inquiry_notification(inquiry)
        except Exception:
            logger.exception(
                "Could not send cafe inquiry notification for inquiry_id=%s",
                inquiry.pk,
            )
        messages.success(
            request,
            "Dziękujemy za wiadomość. Odezwemy się w sprawie współpracy.",
        )
        return redirect("for_cafes")

    return render(
        request,
        "pages/for_cafes.html",
        {
            "form": form,
            "cafe_locations": CafeLocation.objects.filter(is_active=True),
        },
    )


def workshops(request):
    form = WorkshopInterestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        interest = form.save()
        try:
            _send_workshop_notification(interest)
        except Exception:
            logger.exception(
                "Could not send workshop notification for interest_id=%s",
                interest.pk,
            )
        messages.success(
            request,
            "Dziękujemy! Zapisaliśmy Twoje zainteresowanie wspólnym gotowaniem.",
        )
        return redirect("workshops")

    return render(
        request,
        "pages/workshops.html",
        {"form": form},
    )


def about(request):
    return render(request, "pages/about.html")


def contact(request):
    return render(request, "pages/contact.html")


def privacy_policy(request):
    return render(request, "pages/privacy.html")


def regulations(request):
    return render(request, "pages/regulations.html")
