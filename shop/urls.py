from django.urls import path

from shop import views


app_name = "shop"

urlpatterns = [
    path("sklep/", views.product_list, name="list"),
    path("sklep/<slug:slug>/", views.product_detail, name="detail"),
    path("koszyk/", views.cart_view, name="cart"),
    path("zamowienia/koszyk/", views.rzut_cart_view, name="rzut_cart"),
    path(
        "zamowienia/checkout/",
        views.rzut_checkout,
        name="rzut_checkout",
    ),
    path(
        "zamowienia/powrot/",
        views.rzut_p24_return,
        name="rzut_p24_return",
    ),
    path(
        "zamowienia/zamowienie/<str:number>/",
        views.rzut_order_detail,
        name="rzut_order_detail",
    ),
    path(
        "zamowienia/webhook/p24/",
        views.rzut_p24_webhook,
        name="rzut_p24_webhook",
    ),
    path(
        "zamowienia/koszyk/dodaj/<int:rzut_item_id>/",
        views.rzut_cart_add,
        name="rzut_cart_add",
    ),
    path(
        "zamowienia/koszyk/aktualizuj/<int:rzut_item_id>/",
        views.rzut_cart_update,
        name="rzut_cart_update",
    ),
    path(
        "zamowienia/koszyk/usun/<int:rzut_item_id>/",
        views.rzut_cart_remove,
        name="rzut_cart_remove",
    ),
    path(
        "zamowienia/koszyk/ceny/akceptuj/",
        views.rzut_cart_accept_prices,
        name="rzut_cart_accept_prices",
    ),
    path(
        "koszyk/dodaj/<int:product_id>/",
        views.cart_add,
        name="cart_add",
    ),
    path(
        "koszyk/aktualizuj/<int:product_id>/",
        views.cart_update,
        name="cart_update",
    ),
    path(
        "koszyk/usun/<int:product_id>/",
        views.cart_remove,
        name="cart_remove",
    ),
    path("zamowienie/", views.checkout, name="checkout"),
    path(
        "zamowienie/potwierdzenie/",
        views.checkout_confirm,
        name="checkout_confirm",
    ),
    path(
        "zamowienie/webhook/p24/",
        views.p24_webhook,
        name="p24_webhook",
    ),
    path(
        "zamowienie/powrot/",
        views.p24_return,
        name="p24_return",
    ),
    path(
        "zamowienie/anulowano/",
        views.p24_cancel,
        name="p24_cancel",
    ),
]
