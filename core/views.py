from django.shortcuts import render


def home(request):
    return render(request, "pages/home.html")


def about(request):
    return render(request, "pages/about.html")


def contact(request):
    return render(request, "pages/contact.html")


def privacy_policy(request):
    return render(request, "pages/privacy.html")


def regulations(request):
    return render(request, "pages/regulations.html")
