from django.urls import path

from shop import views


app_name = "shop"

urlpatterns = [
    path("sklep/", views.product_list, name="list"),
    path("sklep/<slug:slug>/", views.product_detail, name="detail"),
    path("koszyk/", views.cart_view, name="cart"),
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
]
