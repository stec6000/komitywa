from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("zamowienia/", views.orders, name="orders"),
    path(
        "zamowienia/<slug:rzut_slug>/<slug:product_slug>/",
        views.rzut_item_detail,
        name="rzut_item_detail",
    ),
    path("dla-kawiarni/", views.for_cafes, name="for_cafes"),
    path("wspolne-gotowanie/", views.workshops, name="workshops"),
    path("o-nas/", views.about, name="about"),
    path("kontakt/", views.contact, name="contact"),
    path("polityka-prywatnosci/", views.privacy_policy, name="privacy-policy"),
    path("regulamin/", views.regulations, name="regulations"),
]
