from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("o-nas/", views.about, name="about"),
    path("kontakt/", views.contact, name="contact"),
    path("polityka-prywatnosci/", views.privacy_policy, name="privacy-policy"),
    path("regulamin/", views.regulations, name="regulations"),
]
