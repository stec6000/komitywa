from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .cart import Cart
from .models import Product, ProductCategory


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
    return render(request, "shop/cart.html", {})


def cart_update(request, product_id):
    return redirect("shop:cart")


def cart_remove(request, product_id):
    return redirect("shop:cart")


def checkout(request):
    return render(request, "shop/checkout.html", {})


def checkout_confirm(request):
    return render(request, "shop/checkout_confirm.html", {})
