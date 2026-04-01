import json

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.utils.safestring import mark_safe

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

    schema = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": recipe.title,
        "description": recipe.description,
        "prepTime": f"PT{recipe.prep_time}M",
        "recipeIngredient": [
            line.strip()
            for line in recipe.ingredients_text.splitlines()
            if line.strip()
        ],
        "recipeInstructions": [
            {"@type": "HowToStep", "text": step.strip()}
            for step in recipe.steps_text.splitlines()
            if step.strip()
        ],
        "datePublished": recipe.created_at.date().isoformat(),
        "author": {"@type": "Organization", "name": "Kuchenna Komitywa"},
    }
    if recipe.image:
        schema["image"] = request.build_absolute_uri(recipe.image.url)

    schema_json = mark_safe(json.dumps(schema, ensure_ascii=False))

    return render(request, "recipes/detail.html", {
        "recipe": recipe,
        "schema_json": schema_json,
    })
