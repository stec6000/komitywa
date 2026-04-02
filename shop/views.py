from decimal import Decimal

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .cart import Cart
from .forms import CheckoutForm
from .models import Order, Product, ProductCategory


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
            Order.objects.create(
                email=form.cleaned_data["email"],
                name=form.cleaned_data["name"],
                phone=form.cleaned_data["phone"],
                pickup_date=form.cleaned_data["pickup_date"],
                total=cart.get_total_price(),
                cart_snapshot=cart_snapshot,
            )
            cart.clear()
            return redirect("shop:checkout_confirm")
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

    return render(request, "shop/checkout.html", {
        "form": form,
        "cart_items": cart_items,
        "total": total,
    })


def checkout_confirm(request):
    return render(request, "shop/checkout_confirm.html", {})
