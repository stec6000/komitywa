import json
import logging
import uuid
from decimal import Decimal
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .cart import Cart
from .emails import (
    deliver_rzut_order_notifications,
    send_ebook_delivery,
    send_order_confirmation,
)
from .forms import CheckoutForm, RzutCheckoutForm
from .models import (
    Order,
    Product,
    ProductCategory,
    Reservation,
    RzutItem,
    RzutOrder,
)
from .payment import (
    get_payment_url,
    is_valid_p24_notification,
    register_rzut_transaction,
    register_transaction,
    verify_transaction,
)
from .rzut_cart import DifferentRzutError, InvalidQuantityError, RzutCart
from .reservations import (
    OrderConfirmed,
    ReservationCheckoutData,
    ReservationError,
    ReservationLineRequest,
    confirm_reservation,
    expire_due_reservations,
    fail_reservation,
    start_checkout,
)

logger = logging.getLogger(__name__)


def product_list(request):
    products = Product.objects.available_in_shop().select_related("category")

    active_category = request.GET.get("kategoria", "")
    if active_category:
        products = products.filter(category__slug=active_category)

    paginator = Paginator(products, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    categories = ProductCategory.objects.all()

    return render(request, "shop/list.html", {
        "page_obj": page_obj,
        "categories": categories,
        "active_category": active_category,
    })


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.available_in_shop(),
        slug=slug,
    )
    return render(request, "shop/detail.html", {
        "product": product,
    })


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(
        Product.objects.available_in_shop(),
        id=product_id,
    )
    cart = Cart(request)
    cart.add(product)
    return redirect("shop:cart")


def cart_view(request):
    cart = Cart(request)

    # Fetch active products in cart
    product_ids = [int(k) for k in cart.cart.keys()]
    products = Product.objects.available_in_shop().filter(id__in=product_ids)
    products_map = {str(p.id): p for p in products}

    # Remove stale cart entries (Pitfall 6)
    stale_ids = [
        pid for pid in list(cart.cart.keys()) if pid not in products_map
    ]
    for pid in stale_ids:
        cart.remove(pid)

    # Build cart_items list
    cart_items = []
    for product_id, item in cart.cart.items():
        product = products_map.get(product_id)
        if product:
            quantity = item["quantity"]
            line_total = Decimal(item["price"]) * quantity
            cart_items.append({
                "product": product,
                "quantity": quantity,
                "line_total": line_total,
                "is_ebook": product.type == "ebook",
            })

    total = cart.get_total_price()

    return render(request, "shop/cart.html", {
        "cart_items": cart_items,
        "total": total,
        "cart": cart,
    })


@require_POST
def cart_update(request, product_id):
    quantity = int(request.POST.get("quantity", 1))
    if quantity < 1:
        return redirect("shop:cart")
    cart = Cart(request)
    cart.update_quantity(product_id, quantity)
    return redirect("shop:cart")


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    cart.remove(product_id)
    return redirect("shop:cart")


def rzut_cart_view(request):
    expire_due_reservations()
    cart = RzutCart(request)
    snapshot = cart.snapshot()
    for item_label in snapshot["removed_items"]:
        messages.warning(
            request,
            f"{item_label} nie jest już dostępna i została usunięta "
            "z Koszyka Rzutu.",
        )
    return render(
        request,
        "shop/rzut_cart.html",
        {"cart": cart, **snapshot, "hide_newsletter": True},
    )


@require_POST
def rzut_cart_add(request, rzut_item_id):
    now = timezone.now()
    item = get_object_or_404(
        RzutItem.objects.select_related("rzut", "product"),
        pk=rzut_item_id,
    )
    if not item.can_add_to_cart_at(now):
        raise Http404
    try:
        RzutCart(request).add(item)
    except DifferentRzutError:
        messages.error(
            request,
            "Koszyk Rzutu może zawierać Pozycje Rzutu tylko jednego Rzutu.",
        )
    return redirect("shop:rzut_cart")


@require_POST
def rzut_cart_update(request, rzut_item_id):
    try:
        quantity = int(request.POST.get("quantity", ""))
        RzutCart(request).update(rzut_item_id, quantity)
    except (InvalidQuantityError, ValueError):
        messages.error(
            request,
            "Podaj dodatnią, całkowitą liczbę sztuk.",
        )
    return redirect("shop:rzut_cart")


@require_POST
def rzut_cart_remove(request, rzut_item_id):
    RzutCart(request).remove(rzut_item_id)
    return redirect("shop:rzut_cart")


@require_POST
def rzut_cart_accept_prices(request):
    expected_prices = {
        key.removeprefix("price_"): value
        for key, value in request.POST.items()
        if key.startswith("price_")
    }
    if RzutCart(request).accept_current_prices(expected_prices):
        messages.success(request, "Nowe ceny zostały zaakceptowane.")
    else:
        messages.error(
            request,
            "Ceny ponownie się zmieniły. Sprawdź aktualną sumę.",
        )
    return redirect("shop:rzut_cart")


@require_POST
def rzut_cart_discount(request):
    try:
        RzutCart(request).apply_discount_code(request.POST.get("code", ""))
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Kod Rabatowy został zastosowany.")
    return redirect("shop:rzut_cart")


@require_POST
def rzut_cart_discount_remove(request):
    RzutCart(request).remove_discount_code()
    messages.success(request, "Kod Rabatowy został usunięty.")
    return redirect("shop:rzut_cart")


def rzut_checkout(request):
    expire_due_reservations()
    cart = RzutCart(request)
    snapshot = cart.snapshot()
    if snapshot["removed_items"]:
        messages.warning(
            request,
            "Koszyk Rzutu zmienił się. Sprawdź go przed podaniem danych.",
        )
        return redirect("shop:rzut_cart")
    if not snapshot["lines"] or snapshot["rzut"] is None:
        return redirect("shop:rzut_cart")
    if snapshot["has_price_changes"]:
        messages.error(
            request,
            "Cena co najmniej jednej Pozycji Rzutu zmieniła się. "
            "Zaakceptuj aktualną sumę.",
        )
        return redirect("shop:rzut_cart")
    if snapshot["has_availability_errors"]:
        messages.error(
            request,
            "Wybrana liczba sztuk nie jest już dostępna. Popraw Koszyk Rzutu.",
        )
        return redirect("shop:rzut_cart")
    if snapshot["discount_error"]:
        messages.error(request, snapshot["discount_error"])
        return redirect("shop:rzut_cart")
    form = RzutCheckoutForm(
        snapshot["rzut"],
        request.POST if request.method == "POST" else None,
    )
    if request.method == "POST" and form.is_valid():
        slot = form.cleaned_data["pickup_slot"]
        try:
            checkout_result = start_checkout(
                rzut_id=snapshot["rzut"].pk,
                lines=[
                    ReservationLineRequest(
                        item_id=line["item"].pk,
                        quantity=line["quantity"],
                        expected_price=line["stored_price"],
                    )
                    for line in snapshot["lines"]
                ],
                checkout=ReservationCheckoutData(
                    name=form.cleaned_data["name"],
                    email=form.cleaned_data["email"],
                    phone=form.cleaned_data["phone"],
                    notes=form.cleaned_data["notes"],
                    pickup_starts_at=slot.starts_at,
                    pickup_ends_at=slot.ends_at,
                ),
                discount_code=(
                    snapshot["discount_code"].code
                    if snapshot["discount_code"]
                    else ""
                ),
            )
        except ReservationError as exc:
            messages.error(request, exc.user_message)
            return redirect("shop:rzut_cart")

        if isinstance(checkout_result, OrderConfirmed):
            deliver_rzut_order_notifications(checkout_result.order)
            cart.clear()
            return redirect(
                "shop:rzut_order_detail",
                number=checkout_result.order.number,
            )

        reservation = checkout_result.reservation

        url_return = request.build_absolute_uri(
            f"{reverse('shop:rzut_p24_return')}?"
            + urlencode({"session": reservation.p24_session_id})
        )
        url_status = request.build_absolute_uri(
            reverse("shop:rzut_p24_webhook")
        )
        try:
            token = register_rzut_transaction(
                reservation,
                url_return,
                url_status,
            )
        except Exception as exc:
            logger.error(
                "P24 registration failed for Reservation %d: %s",
                reservation.pk,
                exc,
            )
            fail_reservation(reservation)
            messages.error(
                request,
                "Nie udało się rozpocząć płatności. Pula została "
                "zwolniona, a Koszyk Rzutu zachowany. Spróbuj ponownie.",
            )
            return redirect("shop:rzut_cart")

        cart.clear()
        return redirect(get_payment_url(token))
    return render(
        request,
        "shop/rzut_checkout.html",
        {"form": form, **snapshot, "hide_newsletter": True},
    )


def rzut_p24_return(request):
    session_id = request.GET.get("session", "")
    reservation = get_object_or_404(
        Reservation.objects.select_related("rzut"),
        p24_session_id=session_id,
    )
    order = (
        RzutOrder.objects.filter(reservation=reservation)
        .select_related("rzut")
        .first()
    )
    return render(
        request,
        "shop/rzut_p24_return.html",
        {
            "reservation": reservation,
            "order": order,
            "hide_newsletter": True,
        },
    )


@require_POST
def rzut_reservation_retry(request, session_id):
    reservation = get_object_or_404(
        Reservation.objects.filter(
            status__in=[
                Reservation.Status.EXPIRED,
                Reservation.Status.FAILED,
            ]
        ).prefetch_related("items"),
        p24_session_id=session_id,
    )
    RzutCart(request).restore(reservation)
    messages.success(
        request,
        "Koszyk Rzutu został odtworzony. Sprawdź aktualne ceny i Dostępność "
        "przed ponowną próbą.",
    )
    return redirect("shop:rzut_cart")


def rzut_order_detail(request, number):
    order = get_object_or_404(
        RzutOrder.objects.select_related("rzut").prefetch_related("items"),
        number=number,
    )
    return render(
        request,
        "shop/rzut_order_detail.html",
        {"order": order, "hide_newsletter": True},
    )


@csrf_exempt
@require_POST
def rzut_p24_webhook(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    session_id = data.get("sessionId", "")
    p24_order_id = data.get("orderId", 0)
    amount = data.get("amount", 0)
    if not is_valid_p24_notification(data):
        logger.warning(
            "Rzut P24 webhook: invalid sign for session %s",
            session_id,
        )
        return JsonResponse({"error": "Invalid sign"}, status=400)

    try:
        reservation = Reservation.objects.get(
            p24_session_id=session_id
        )
    except Reservation.DoesNotExist:
        logger.error(
            "Rzut P24 webhook: Reservation not found for session %s",
            session_id,
        )
        return JsonResponse({"error": "Reservation not found"}, status=404)

    expected_amount = int(reservation.total * 100)
    if amount != expected_amount or data.get("currency") != "PLN":
        logger.warning(
            "Rzut P24 webhook: payment mismatch for Reservation %d",
            reservation.pk,
        )
        return JsonResponse({"error": "Payment mismatch"}, status=400)

    try:
        verified = verify_transaction(session_id, p24_order_id, amount)
    except Exception as exc:
        logger.error(
            "Rzut P24 verification failed for Reservation %d: %s",
            reservation.pk,
            exc,
        )
        return JsonResponse({"error": "Verification failed"}, status=500)
    if not verified:
        return JsonResponse({"error": "Payment not verified"}, status=400)

    order, created = confirm_reservation(
        reservation_id=reservation.pk,
        p24_order_id=p24_order_id,
    )
    if created:
        deliver_rzut_order_notifications(order)
    return JsonResponse({"status": "ok", "orderNumber": order.number})


def checkout(request):
    cart = Cart(request)

    if len(cart) == 0:
        return redirect("shop:cart")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            cart_snapshot = {
                str(pid): {
                    "quantity": item["quantity"],
                    "price": item["price"],
                }
                for pid, item in cart.cart.items()
            }
            order = Order.objects.create(
                email=form.cleaned_data["email"],
                name=form.cleaned_data["name"],
                phone=form.cleaned_data["phone"],
                pickup_date=form.cleaned_data["pickup_date"],
                total=cart.get_total_price(),
                cart_snapshot=cart_snapshot,
            )
            # Generate unique P24 session ID (per Pitfall 4)
            order.p24_session_id = (
                f"order-{order.id}-{uuid.uuid4().hex[:8]}"
            )
            order.save(update_fields=["p24_session_id"])

            cart.clear()

            # Register transaction with P24
            url_return = request.build_absolute_uri(
                f"/zamowienie/powrot/?order_id={order.id}"
            )
            url_status = request.build_absolute_uri(
                "/zamowienie/webhook/p24/"
            )
            try:
                token = register_transaction(order, url_return, url_status)
                payment_url = get_payment_url(token)
                return redirect(payment_url)
            except Exception as exc:
                logger.error(
                    "P24 registration failed for order %d: %s",
                    order.id, exc,
                )
                # Restore cart on P24 registration failure
                request.session["cart"] = order.cart_snapshot
                request.session.modified = True
                order.status = "cancelled"
                order.save(update_fields=["status"])
                return redirect("shop:p24_cancel")
    else:
        form = CheckoutForm()

    # Build cart_items for order summary sidebar
    product_ids = [int(k) for k in cart.cart.keys()]
    products = Product.objects.available_in_shop().filter(id__in=product_ids)
    products_map = {str(p.id): p for p in products}

    cart_items = []
    for product_id, item in cart.cart.items():
        product = products_map.get(product_id)
        if product:
            quantity = item["quantity"]
            line_total = Decimal(item["price"]) * quantity
            cart_items.append({
                "product": product,
                "quantity": quantity,
                "line_total": line_total,
            })

    total = cart.get_total_price()
    ebook_only = all(
        products_map.get(pid, None) and products_map[pid].type == "ebook"
        for pid in cart.cart
    )

    return render(request, "shop/checkout.html", {
        "form": form,
        "cart_items": cart_items,
        "total": total,
        "ebook_only": ebook_only,
    })


def checkout_confirm(request):
    return redirect("home")


@csrf_exempt
@require_POST
def p24_webhook(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    session_id = data.get("sessionId", "")
    order_id_p24 = data.get("orderId", 0)
    amount = data.get("amount", 0)

    if not is_valid_p24_notification(data):
        logger.warning(
            "P24 webhook: invalid sign for session %s", session_id
        )
        return JsonResponse({"error": "Invalid sign"}, status=400)

    # Find order
    try:
        order = Order.objects.get(p24_session_id=session_id)
    except Order.DoesNotExist:
        logger.error(
            "P24 webhook: order not found for session %s", session_id
        )
        return JsonResponse({"error": "Order not found"}, status=404)

    # Verify transaction with P24 API
    try:
        verified = verify_transaction(session_id, order_id_p24, amount)
    except Exception as exc:
        logger.error(
            "P24 verify failed for order %d: %s", order.id, exc
        )
        return JsonResponse({"error": "Verification failed"}, status=500)

    if verified:
        order.status = "paid"
        order.save(update_fields=["status"])

        # Send emails (per D-10: log errors, don't crash)
        try:
            send_order_confirmation(order)
        except Exception as exc:
            logger.error(
                "Failed to send confirmation email for order %d: %s",
                order.id, exc,
            )

        try:
            send_ebook_delivery(order)
        except Exception as exc:
            logger.error(
                "Failed to send ebook email for order %d: %s",
                order.id, exc,
            )

    return JsonResponse({"status": "ok"})


def p24_return(request):
    order_id = request.GET.get("order_id")
    context = {}
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            context["order"] = order
        except Order.DoesNotExist:
            context["order_not_found"] = True
    return render(request, "shop/p24_return.html", context)


def p24_cancel(request):
    order_id = request.GET.get("order_id")
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            # Restore cart from snapshot (per D-06)
            request.session["cart"] = order.cart_snapshot
            request.session.modified = True
            # Mark order as cancelled
            if order.status == "pending":
                order.status = "cancelled"
                order.save(update_fields=["status"])
        except Order.DoesNotExist:
            pass
    return render(request, "shop/p24_cancel.html", {})
