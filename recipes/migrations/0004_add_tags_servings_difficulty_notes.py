from django.db import migrations, models


STARTER_TAGS = [
    {"slug": "tofu", "name": "tofu"},
    {"slug": "bezglutenowe", "name": "bezglutenowe"},
    {"slug": "szybkie", "name": "szybkie"},
    {"slug": "pieczone", "name": "pieczone"},
    {"slug": "na-zimno", "name": "na-zimno"},
    {"slug": "ciecierzyca", "name": "ciecierzyca"},
    {"slug": "fasola", "name": "fasola"},
    {"slug": "soczewica", "name": "soczewica"},
]


# slug -> (servings, difficulty, [tag_slugs])
RECIPE_BACKFILL = {
    "hummus-z-pieczona-ciecierzyca-i-warzywami": (4, "latwy", ["ciecierzyca", "bezglutenowe", "na-zimno"]),
    "curry-z-tofu-brokulem-i-mleczkiem-kokosowym": (3, "sredni", ["tofu", "bezglutenowe"]),
    "chili-sin-carne-z-czarna-fasola": (4, "latwy", ["fasola", "bezglutenowe"]),
    "smoothie-bowl-z-mango-i-bananem": (1, "latwy", ["szybkie", "bezglutenowe", "na-zimno"]),
    "placuszki-owsiano-bananowe-z-borowkami": (2, "latwy", ["szybkie"]),
    "buddha-bowl-z-tofu-ryzem-i-pieczona-papryka": (2, "latwy", ["tofu", "pieczone", "bezglutenowe"]),
    "salatka-z-ciecierzyca-pieczonym-batatem-i-pestkami": (2, "latwy", ["ciecierzyca", "pieczone", "bezglutenowe"]),
    "krem-pomidorowy-z-czerwonej-soczewicy": (4, "latwy", ["soczewica", "bezglutenowe", "szybkie"]),
    "chlebek-bananowy-z-orzechami-wloskimi": (8, "sredni", ["pieczone"]),
    "makaron-z-pesto-pietruszkowo-bazyliowym": (2, "latwy", ["szybkie"]),
    "krem-z-bialej-fasoli-ze-szparagami": (2, "latwy", ["fasola", "tofu", "pieczone", "bezglutenowe"]),
}


def seed_tags_and_backfill(apps, schema_editor):
    Tag = apps.get_model("recipes", "Tag")
    Recipe = apps.get_model("recipes", "Recipe")

    tag_by_slug = {}
    for tag in STARTER_TAGS:
        obj, _ = Tag.objects.update_or_create(
            slug=tag["slug"],
            defaults={"name": tag["name"]},
        )
        tag_by_slug[tag["slug"]] = obj

    for slug, (servings, difficulty, tag_slugs) in RECIPE_BACKFILL.items():
        try:
            recipe = Recipe.objects.get(slug=slug)
        except Recipe.DoesNotExist:
            # Idempotent: skip if a recipe was renamed/removed in a future state.
            continue
        recipe.servings = servings
        recipe.difficulty = difficulty
        recipe.save(update_fields=["servings", "difficulty"])
        recipe.tags.set([tag_by_slug[s] for s in tag_slugs])


def unseed_tags_and_backfill(apps, schema_editor):
    Tag = apps.get_model("recipes", "Tag")
    Recipe = apps.get_model("recipes", "Recipe")
    # Clear M2M links on recipes and delete starter tags.
    for recipe in Recipe.objects.filter(slug__in=RECIPE_BACKFILL.keys()):
        recipe.tags.clear()
    Tag.objects.filter(slug__in=[t["slug"] for t in STARTER_TAGS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0003_add_krem_z_bialej_fasoli"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True)),
                ("slug", models.SlugField(max_length=50, unique=True)),
            ],
            options={
                "verbose_name": "Tag",
                "verbose_name_plural": "Tagi",
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="recipe",
            name="tags",
            field=models.ManyToManyField(
                blank=True,
                related_name="recipes",
                to="recipes.tag",
            ),
        ),
        migrations.AddField(
            model_name="recipe",
            name="servings",
            field=models.PositiveSmallIntegerField(default=1, help_text="Liczba porcji"),
        ),
        migrations.AddField(
            model_name="recipe",
            name="difficulty",
            field=models.CharField(
                choices=[("latwy", "latwy"), ("sredni", "sredni"), ("trudny", "trudny")],
                default="latwy",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="recipe",
            name="notes",
            field=models.TextField(blank=True, default="", help_text="Opcjonalne notatki autora"),
        ),
        migrations.RunPython(seed_tags_and_backfill, unseed_tags_and_backfill),
    ]
