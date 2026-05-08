from django.shortcuts import render

from recipes.models import Recipe
from shop.models import Product


def home(request):
    latest_recipes = list(
        Recipe.objects.filter(is_published=True)
        .select_related("category")[:4]
    )
    featured_recipe = latest_recipes[0] if latest_recipes else None
    feed_recipes = latest_recipes[1:4] if featured_recipe else latest_recipes[:3]

    featured_products = Product.objects.filter(
        is_active=True
    ).select_related("category")[:4]

    return render(request, "pages/home.html", {
        "feed_recipes": feed_recipes,
        "featured_recipe": featured_recipe,
        "featured_products": featured_products,
    })


def about(request):
    return render(request, "pages/about.html")


def contact(request):
    return render(request, "pages/contact.html")


def privacy_policy(request):
    return render(request, "pages/privacy.html")


def regulations(request):
    return render(request, "pages/regulations.html")
