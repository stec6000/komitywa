from django.db import migrations


def update_site(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    Site.objects.filter(id=1).update(
        domain="kuchennakomitywa.pl",
        name="Kuchenna Komitywa",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("sites", "0001_initial"),
    ]
    operations = [
        migrations.RunPython(update_site, migrations.RunPython.noop),
    ]
