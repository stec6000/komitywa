import decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


def copy_legacy_assignments(apps, schema_editor):
    Product = apps.get_model("shop", "Product")
    RzutItem = apps.get_model("shop", "RzutItem")

    items = [
        RzutItem(
            rzut_id=product.edition_id,
            product_id=product.pk,
            price=product.price,
            portion=product.default_portion,
            pool=1,
            sort_order=product.sort_order,
            is_active=False,
        )
        for product in Product.objects.exclude(edition_id=None).iterator()
    ]
    RzutItem.objects.bulk_create(items)


class Migration(migrations.Migration):
    dependencies = [
        ("shop", "0006_product_catalog_fields"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="orderedition",
            options={
                "ordering": ["-opens_at", "-created_at"],
                "verbose_name": "Rzut",
                "verbose_name_plural": "Rzuty",
            },
        ),
        migrations.AlterField(
            model_name="orderedition",
            name="title",
            field=models.CharField(
                max_length=200,
                verbose_name="Nazwa Rzutu",
            ),
        ),
        migrations.CreateModel(
            name="RzutItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=8,
                        validators=[
                            django.core.validators.MinValueValidator(
                                decimal.Decimal("0.00")
                            )
                        ],
                        verbose_name="Cena",
                    ),
                ),
                (
                    "portion",
                    models.CharField(
                        help_text=(
                            'Np. "bochenek ok. 750 g" albo '
                            '"pudełko 6 szt."'
                        ),
                        max_length=120,
                        verbose_name="Porcja",
                    ),
                ),
                (
                    "pool",
                    models.PositiveIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1)
                        ],
                        verbose_name="Pula",
                    ),
                ),
                (
                    "per_customer_limit",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text=(
                            "Pozostaw puste, aby nie nakładać dodatkowego "
                            "limitu."
                        ),
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(1)
                        ],
                        verbose_name="Limit Klienta",
                    ),
                ),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=0,
                        verbose_name="Kolejność",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        verbose_name="Aktywna",
                    ),
                ),
                (
                    "production_note",
                    models.TextField(
                        blank=True,
                        default="",
                        verbose_name="Notatka produkcyjna",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "rzut",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="items",
                        to="shop.orderedition",
                        verbose_name="Rzut",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="rzut_items",
                        to="shop.product",
                        verbose_name="Produkt",
                    ),
                ),
            ],
            options={
                "verbose_name": "Pozycja Rzutu",
                "verbose_name_plural": "Pozycje Rzutu",
                "ordering": ["sort_order", "product__title"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("rzut", "product"),
                        name="unique_product_per_rzut",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("price__gte", 0)),
                        name="rzut_item_price_nonnegative",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("pool__gte", 1)),
                        name="rzut_item_pool_positive",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("per_customer_limit__isnull", True),
                            ("per_customer_limit__gte", 1),
                            _connector="OR",
                        ),
                        name="rzut_item_customer_limit_positive",
                    ),
                ],
            },
        ),
        migrations.RunPython(
            copy_legacy_assignments,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
