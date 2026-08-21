import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("shop", "0023_rzut_order_p24_refunds"),
    ]

    operations = [
        migrations.CreateModel(
            name="RzutEvent",
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
                    "actor_email",
                    models.EmailField(
                        blank=True,
                        default="",
                        max_length=254,
                        verbose_name="E-mail administratora",
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("status_changed", "Zmiana statusu Rzutu"),
                            ("pool_changed", "Zmiana Puli"),
                            (
                                "archive_visibility_changed",
                                "Zmiana widoczności Rzutu w archiwum",
                            ),
                        ],
                        max_length=30,
                        verbose_name="Rodzaj działania",
                    ),
                ),
                (
                    "context",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        verbose_name="Kontekst",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Czas"),
                ),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="rzut_events",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Administrator",
                    ),
                ),
                (
                    "rzut",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="shop.orderedition",
                        verbose_name="Rzut",
                    ),
                ),
            ],
            options={
                "verbose_name": "Zdarzenie Rzutu",
                "verbose_name_plural": "Historia Rzutu",
                "ordering": ["-created_at", "-pk"],
            },
        ),
    ]
