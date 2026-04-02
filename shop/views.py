from django.shortcuts import redirect, render


def product_list(request):
    return render(request, "shop/list.html", {})


def product_detail(request, slug):
    return render(request, "shop/detail.html", {})


def cart_view(request):
    return render(request, "shop/cart.html", {})


def cart_add(request, product_id):
    return redirect("shop:cart")


def cart_update(request, product_id):
    return redirect("shop:cart")


def cart_remove(request, product_id):
    return redirect("shop:cart")


def checkout(request):
    return render(request, "shop/checkout.html", {})


def checkout_confirm(request):
    return render(request, "shop/checkout_confirm.html", {})
