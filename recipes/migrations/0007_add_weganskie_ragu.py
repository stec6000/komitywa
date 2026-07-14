import shutil
from pathlib import Path

from django.conf import settings
from django.db import migrations


def lines(*items):
    return "\n".join(items)


RECIPE = {
    "title": "Wegańskie ragù z tofu",
    "slug": "weganskie-ragu-z-tofu",
    "category_slug": "obiady",
    "tag_slugs": ["tofu", "pieczone"],
    "description": (
        "Roślinne ragù na bazie pieczonego \"mielonego\" z tofu w aromatycznym "
        "sosie pomidorowym. Idealne do makaronu."
    ),
    "ingredients_text": lines(
        "Tofu mielone:",
        "400 g tofu naturalnego",
        "2 łyżeczki czosnku granulowanego",
        "2 łyżeczki cebuli suszonej",
        "1 łyżeczka wędzonej papryki",
        "1 łyżeczka majeranku",
        "1 łyżeczka suszonego tymianku",
        "1 łyżeczka suszonej natki pietruszki",
        "2 łyżki sosu sojowego",
        "2 łyżki oleju",
        "2 łyżki płatków drożdżowych",
        "Sos:",
        "1 cebula",
        "1 marchewka",
        "2 ząbki czosnku",
        "2 puszki pomidorów",
        "sól i pieprz do smaku",
        "makaron do podania (opcjonalnie)",
    ),
    "steps_text": lines(
        "Tofu pokrusz w dłoniach do miski, dodaj wszystkie przyprawy, sos sojowy, olej i płatki drożdżowe, dokładnie wymieszaj.",
        "Rozłóż płasko na blaszce i piecz 20-25 minut w 180°C (termoobieg).",
        "Na patelni podsmaż pokrojoną cebulę, startą marchewkę i posiekany czosnek, aż zmiękną.",
        "Dodaj 2 puszki pomidorów, dopraw solą i pieprzem.",
        "Dodaj upieczone tofu i duś około 10 minut.",
        "Podawaj z ulubionym makaronem.",
    ),
    "prep_time": 45,
    "servings": 4,
    "difficulty": "latwy",
    "notes": (
        "Jedna porcja ragù to ok. 305 kcal (bez makaronu). Z porcją makaronu "
        "(80 g suchego) wychodzi ok. 590 kcal. Całość: ok. 1220 kcal na 4 porcje."
    ),
    "image_name": "weganskie-ragu-z-tofu.jpg",
}


def copy_seed_image(seed_dir, image_name):
    source = seed_dir / image_name
    if not source.exists():
        raise FileNotFoundError(
            f"Brakuje seed image '{image_name}' w katalogu {seed_dir}"
        )

    target_dir = Path(settings.MEDIA_ROOT) / "recipes"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / image_name

    if not target.exists() or source.stat().st_size != target.stat().st_size:
        shutil.copyfile(source, target)

    return f"recipes/{image_name}"


def add_weganskie_ragu(apps, schema_editor):
    Category = apps.get_model("recipes", "Category")
    Recipe = apps.get_model("recipes", "Recipe")
    Tag = apps.get_model("recipes", "Tag")

    category = Category.objects.get(slug=RECIPE["category_slug"])

    seed_dir = Path(__file__).resolve().parent.parent / "seed_images"
    image_path = copy_seed_image(seed_dir, RECIPE["image_name"])

    recipe, _ = Recipe.objects.update_or_create(
        slug=RECIPE["slug"],
        defaults={
            "title": RECIPE["title"],
            "category": category,
            "description": RECIPE["description"],
            "ingredients_text": RECIPE["ingredients_text"],
            "steps_text": RECIPE["steps_text"],
            "prep_time": RECIPE["prep_time"],
            "servings": RECIPE["servings"],
            "difficulty": RECIPE["difficulty"],
            "notes": RECIPE["notes"],
            "image": image_path,
            "is_published": True,
        },
    )

    recipe.tags.set([Tag.objects.get(slug=slug) for slug in RECIPE["tag_slugs"]])


def remove_weganskie_ragu(apps, schema_editor):
    Recipe = apps.get_model("recipes", "Recipe")

    recipe = Recipe.objects.filter(slug=RECIPE["slug"]).first()
    if recipe is not None:
        recipe.tags.clear()

    Recipe.objects.filter(slug=RECIPE["slug"]).delete()

    target = Path(settings.MEDIA_ROOT) / "recipes" / RECIPE["image_name"]
    if target.exists():
        target.unlink()


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0006_alter_recipe_description_and_more"),
    ]

    operations = [
        migrations.RunPython(add_weganskie_ragu, remove_weganskie_ragu),
    ]
