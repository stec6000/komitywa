from django.shortcuts import render

from recipes.models import Recipe


def home(request):
    latest_recipes = Recipe.objects.filter(
        is_published=True
    ).select_related("category")[:3]
    return render(request, "pages/home.html", {
        "latest_recipes": latest_recipes,
    })


def about(request):
    return render(request, "pages/about.html")


def contact(request):
    return render(request, "pages/contact.html")


def privacy_policy(request):
    return render(request, "pages/privacy.html")


def regulations(request):
    return render(request, "pages/regulations.html")
