from django.db import migrations, models


def copy_legacy_shop_availability(apps, schema_editor):
    Product = apps.get_model("shop", "Product")
    Product.objects.update(is_available_in_shop=models.F("is_active"))


class Migration(migrations.Migration):
    dependencies = [
        ("shop", "0005_order_editions"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="default_portion",
            field=models.CharField(
                blank=True,
                default="",
                help_text=(
                    'Np. "bochenek ok. 750 g" albo "pudełko 6 szt."'
                ),
                max_length=120,
                verbose_name="Domyślna porcja",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="is_archived",
            field=models.BooleanField(
                default=False,
                verbose_name="Zarchiwizowany",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="is_available_in_shop",
            field=models.BooleanField(
                default=True,
                verbose_name="Dostępny w sklepie",
            ),
        ),
        migrations.RunPython(
            copy_legacy_shop_availability,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="product",
            name="price",
            field=models.DecimalField(
                decimal_places=2,
                help_text=(
                    "Domyślna cena w PLN, kopiowana do nowej Pozycji Rzutu"
                ),
                max_digits=8,
                verbose_name="Cena domyślna",
            ),
        ),
    ]
