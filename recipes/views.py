from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404

from .models import Category, Recipe


def recipe_list(request):
    recipes = Recipe.objects.filter(is_published=True).select_related("category")

    active_category = request.GET.get("kategoria", "")
    if active_category:
        recipes = recipes.filter(category__slug=active_category)

    query = request.GET.get("q", "").strip()
    if query:
        recipes = recipes.filter(
            Q(title__icontains=query) | Q(ingredients_text__icontains=query)
        )

    paginator = Paginator(recipes, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    return render(request, "recipes/list.html", {
        "page_obj": page_obj,
        "categories": categories,
        "active_category": active_category,
        "query": query,
    })


def recipe_detail(request, slug):
    recipe = get_object_or_404(Recipe, slug=slug, is_published=True)
    return render(request, "recipes/detail.html", {"recipe": recipe})
