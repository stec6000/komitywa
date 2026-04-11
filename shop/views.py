import json
import logging
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .cart import Cart
from .emails import send_ebook_delivery, send_order_confirmation
from .forms import CheckoutForm
from .models import Order, Product, ProductCategory
from .payment import (
    calculate_sign,
    get_payment_url,
    register_transaction,
    verify_transaction,
)

logger = logging.getLogger(__name__)


def product_list(request):
    products = Product.objects.filter(is_active=True).select_related("category")

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
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, "shop/detail.html", {
        "product": product,
    })


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = Cart(request)
    cart.add(product)
    return redirect("shop:cart")


def cart_view(request):
    cart = Cart(request)

    # Fetch active products in cart
    product_ids = [int(k) for k in cart.cart.keys()]
    products = Product.objects.filter(id__in=product_ids, is_active=True)
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
    products = Product.objects.filter(id__in=product_ids, is_active=True)
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

    session_id = data.get("sessionId", "")
    order_id_p24 = data.get("orderId", 0)
    amount = data.get("amount", 0)

    # Verify webhook sign
    received_sign = data.get("sign", "")
    expected_sign = calculate_sign({
        "merchantId": data.get("merchantId"),
        "posId": data.get("posId"),
        "sessionId": session_id,
        "amount": amount,
        "originAmount": data.get("originAmount"),
        "currency": data.get("currency"),
        "orderId": order_id_p24,
        "methodId": data.get("methodId"),
        "statement": data.get("statement"),
        "crc": settings.P24_CRC_KEY,
    })

    if received_sign != expected_sign:
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
