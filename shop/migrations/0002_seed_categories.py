from django.db import migrations


def seed_categories(apps, schema_editor):
    ProductCategory = apps.get_model("shop", "ProductCategory")
    categories = [
        {"name": "Ebooki", "slug": "ebooki"},
        {"name": "Dania w sloiku", "slug": "dania-w-sloiku"},
        {"name": "Ciasta", "slug": "ciasta"},
    ]
    for cat in categories:
        ProductCategory.objects.get_or_create(
            slug=cat["slug"], defaults={"name": cat["name"]}
        )


def unseed_categories(apps, schema_editor):
    ProductCategory = apps.get_model("shop", "ProductCategory")
    ProductCategory.objects.filter(
        slug__in=["ebooki", "dania-w-sloiku", "ciasta"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_categories, unseed_categories),
    ]
