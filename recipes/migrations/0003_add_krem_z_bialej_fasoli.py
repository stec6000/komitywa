import shutil
from pathlib import Path

from django.conf import settings
from django.db import migrations


def lines(*items):
    return "\n".join(items)


RECIPE = {
    "title": "Krem z bialej fasoli ze szparagami i pomidorkami",
    "slug": "krem-z-bialej-fasoli-ze-szparagami",
    "category_slug": "przekaski",
    "description": (
        "Aksamitny krem z bialej fasoli i tofu z odswiezajaca nuta cytryny i miety, "
        "podany z pieczonymi szparagami, pomidorkami i prazonymi migdalami. "
        "Najlepiej smakuje z chrupiacym pieczywem -- jako lekka kolacja albo elegancka przekaska na stol."
    ),
    "ingredients_text": lines(
        "1 puszka bialej fasoli (400 g), odsaczona",
        "1 kostka tofu naturalnego (180-200 g)",
        "100 ml wody",
        "30 g soku z cytryny (okolo 2 lyzki)",
        "1 zabek czosnku",
        "6 g soli (1 plaska lyzeczka)",
        "kilka swiezych listkow miety",
        "16 szparagow (najlepiej zielonych)",
        "16 pomidorkow koktajlowych",
        "garsc prazonych migdalow, grubo posiekanych",
        "chrupiacy olej chili lub podsmazona cebulka -- do polania",
        "oliwa do skropienia warzyw",
        "sol do warzyw",
        "swiezo mielony pieprz do podania",
    ),
    "steps_text": lines(
        "Nagrzej piekarnik do 180 stopni. Szparagi obierz z twardych koncow, uloz razem z pomidorkami na blasze wylozonej papierem do pieczenia, skrop oliwa i posyp szczypta soli.",
        "Piecz warzywa przez okolo 15 minut, az szparagi beda miekkie ale wciaz jedrne, a pomidorki zaczna pekac i puszczac sok.",
        "W tym czasie do kielicha blendera wloz odsaczona biala fasole, tofu, wode, sok z cytryny, czosnek, sol i listki miety. Miksuj na wysokich obrotach do uzyskania bardzo gladkiej, kremowej konsystencji -- jezeli krem jest zbyt gesty, dolej lyzke wody.",
        "Sprobuj i dopraw do smaku -- jezeli trzeba, dodaj odrobine soku z cytryny lub szczypte soli.",
        "Wyloz krem na plaski talerz i rozprowadz lyzka, robiac niewielkie zaglebienie na srodku.",
        "Na wierzchu uloz pieczone szparagi i pomidorki, polej chrupiacym olejem chili (lub podsmazona na zloto cebulka) i posyp prazonymi migdalami oraz swiezo mielonym pieprzem.",
        "Podawaj od razu, najlepiej z chrupiacym chlebem lub grzankami -- doskonale do dzielenia na srodku stolu.",
    ),
    "prep_time": 25,
    "image_name": "krem-z-bialej-fasoli.jpg",
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


def add_krem_z_bialej_fasoli(apps, schema_editor):
    Category = apps.get_model("recipes", "Category")
    Recipe = apps.get_model("recipes", "Recipe")

    category = Category.objects.get(slug=RECIPE["category_slug"])

    seed_dir = Path(__file__).resolve().parent.parent / "seed_images"
    image_path = copy_seed_image(seed_dir, RECIPE["image_name"])

    Recipe.objects.update_or_create(
        slug=RECIPE["slug"],
        defaults={
            "title": RECIPE["title"],
            "category": category,
            "description": RECIPE["description"],
            "ingredients_text": RECIPE["ingredients_text"],
            "steps_text": RECIPE["steps_text"],
            "prep_time": RECIPE["prep_time"],
            "image": image_path,
            "is_published": True,
        },
    )


def remove_krem_z_bialej_fasoli(apps, schema_editor):
    Recipe = apps.get_model("recipes", "Recipe")
    Recipe.objects.filter(slug=RECIPE["slug"]).delete()

    target = Path(settings.MEDIA_ROOT) / "recipes" / RECIPE["image_name"]
    if target.exists():
        target.unlink()


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0002_seed_recipe_catalog"),
    ]

    operations = [
        migrations.RunPython(add_krem_z_bialej_fasoli, remove_krem_z_bialej_fasoli),
    ]
