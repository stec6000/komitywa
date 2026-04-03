from django.urls import path

from . import views


app_name = "newsletter"

urlpatterns = [
    path(
        "newsletter/zapisz/",
        views.subscribe,
        name="subscribe",
    ),
    path(
        "newsletter/sprawdz-email/",
        views.check_email,
        name="check_email",
    ),
    path(
        "newsletter/potwierdz/<str:token>/",
        views.confirm,
        name="confirm",
    ),
    path(
        "newsletter/wypisz/<str:token>/",
        views.unsubscribe,
        name="unsubscribe",
    ),
]
