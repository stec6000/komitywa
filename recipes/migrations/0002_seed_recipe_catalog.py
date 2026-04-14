import shutil
from pathlib import Path

from django.conf import settings
from django.db import migrations


def lines(*items):
    return "\n".join(items)


CATEGORIES = [
    {"name": "Sniadania", "slug": "sniadania"},
    {"name": "Obiady", "slug": "obiady"},
    {"name": "Przekaski", "slug": "przekaski"},
    {"name": "Salatki", "slug": "salatki"},
    {"name": "Zupy", "slug": "zupy"},
    {"name": "Wypieki", "slug": "wypieki"},
]


RECIPES = [
    {
        "title": "Hummus z pieczona ciecierzyca i warzywami",
        "slug": "hummus-z-pieczona-ciecierzyca-i-warzywami",
        "category_slug": "przekaski",
        "description": (
            "Gladki hummus z tahini, cytryna i chrupiaca ciecierzyca z patelni. "
            "Dobry do pieczywa, surowych warzyw i jako szybka kolacja."
        ),
        "ingredients_text": lines(
            "1 puszka ciecierzycy (400 g)",
            "2 lyzki tahini",
            "sok z 1/2 cytryny",
            "1 maly zabek czosnku",
            "3 lyzki oliwy",
            "3-4 lyzki zimnej wody",
            "1/2 lyzeczki mielonego kminu",
            "1/2 lyzeczki wedzonej papryki",
            "sol i pieprz do smaku",
            "1 marchewka",
            "1/2 ogorka",
            "garsc pomidorkow koktajlowych",
        ),
        "steps_text": lines(
            "Odcedz ciecierzyce, zachowaj 2 lyzki do podania. Reszte przeloz do blendera z tahini, cytryna, czosnkiem, kminem, 2 lyzkami oliwy i woda.",
            "Miksuj do bardzo gladkiej konsystencji, dopraw sola i pieprzem. Jesli hummus jest za gesty, dolej jeszcze odrobine wody.",
            "Zachowana ciecierzyce podsmaz na 1 lyzce oliwy z wedzona papryka przez 3-4 minuty, az bedzie lekko chrupiaca.",
            "Podawaj hummus z warzywami pokrojonymi w slupki i zrumieniona ciecierzyca na wierzchu.",
        ),
        "prep_time": 20,
        "image_name": "hummus-z-warzywami.jpg",
    },
    {
        "title": "Curry z tofu, brokulem i mleczkiem kokosowym",
        "slug": "curry-z-tofu-brokulem-i-mleczkiem-kokosowym",
        "category_slug": "obiady",
        "description": (
            "Sycace curry z chrupiacym tofu, brokulem i aksamitnym sosem kokosowym. "
            "Najlepiej smakuje z ryzem jasminowym i odrobina limonki."
        ),
        "ingredients_text": lines(
            "180 g ryzu jasminowego",
            "180 g tofu naturalnego",
            "1/2 brokulu",
            "1 marchewka",
            "1 cebula",
            "2 zabki czosnku",
            "1 lyzka pasty curry albo 2 lyzeczki curry w proszku",
            "400 ml mleczka kokosowego",
            "100 ml wody",
            "1 lyzka sosu sojowego",
            "1 lyzeczka soku z limonki",
            "1 lyzka oleju",
            "sol do smaku",
        ),
        "steps_text": lines(
            "Ugotuj ryz wedlug instrukcji na opakowaniu. Tofu odcisnij, pokroj w kostke i oprusz szczypta soli.",
            "Na patelni rozgrzej olej, zrumien tofu, a potem odloz je na talerz. Na tej samej patelni zeszklij cebule, czosnek i marchewke pokrojona w cienkie polplastry.",
            "Dodaj brokul podzielony na male rozyczki i paste curry. Wlej mleczko kokosowe, wode i sos sojowy, a potem gotuj 8-10 minut, az warzywa zmiekna.",
            "Wloz tofu z powrotem do sosu, dopraw sokiem z limonki i podawaj z goracym ryzem.",
        ),
        "prep_time": 35,
        "image_name": "curry-z-tofu-i-brokulem.jpg",
    },
    {
        "title": "Chili sin carne z czarna fasola",
        "slug": "chili-sin-carne-z-czarna-fasola",
        "category_slug": "obiady",
        "description": (
            "Geste chili na bazie pomidorow, fasoli i papryki, z wyraznym aromatem kminu i kakao. "
            "To prosty obiad, ktory smakuje jeszcze lepiej nastepnego dnia."
        ),
        "ingredients_text": lines(
            "150 g ryzu",
            "1 puszka czarnej fasoli",
            "1 puszka krojonych pomidorow",
            "1 czerwona papryka",
            "1 cebula",
            "2 zabki czosnku",
            "100 g kukurydzy",
            "1 lyzka koncentratu pomidorowego",
            "1 lyzeczka mielonego kminu",
            "1 lyzeczka wedzonej papryki",
            "1/2 lyzeczki chili",
            "1/2 lyzeczki kakao",
            "1 lyzka oleju",
            "sol i pieprz do smaku",
        ),
        "steps_text": lines(
            "Ugotuj ryz. Fasole odcedz, a papryke, cebule i czosnek drobno posiekaj.",
            "Na oleju zeszklij cebule, dodaj czosnek i papryke, a po 2 minutach koncentrat oraz przyprawy.",
            "Wlej pomidory, dodaj fasole i kukurydze, dopraw kakao, sola oraz pieprzem. Gotuj na malym ogniu przez 15-20 minut, az sos zgestnieje.",
            "Podawaj chili z ryzem i ulubionymi ziolami albo swieza kolendra.",
        ),
        "prep_time": 40,
        "image_name": "chili-sin-carne.jpg",
    },
    {
        "title": "Smoothie bowl z mango i bananem",
        "slug": "smoothie-bowl-z-mango-i-bananem",
        "category_slug": "sniadania",
        "description": (
            "Geste sniadanie z mrozonych owocow, platkow owsianych i masla orzechowego. "
            "Kilka dodatkow wystarczy, zeby zamienic je w pelny posilek."
        ),
        "ingredients_text": lines(
            "2 mrozone banany",
            "150 g mrozonego mango",
            "100 ml napoju owsianego",
            "2 lyzki platkow owsianych",
            "1 lyzka masla orzechowego",
            "1 lyzeczka soku z limonki",
            "granola do podania",
            "borowki do podania",
            "wiorki kokosowe do podania",
        ),
        "steps_text": lines(
            "Banany i mango przeloz do blendera razem z napojem owsianym, platkami, maslem orzechowym i sokiem z limonki.",
            "Miksuj krotko, tylko do uzyskania gestej i kremowej konsystencji. Jesli trzeba, dodaj lyzke napoju wiecej.",
            "Przeloz smoothie do miski i wyrownaj wierzch lyzka.",
            "Podawaj od razu z granola, borowkami i wiorkami kokosowymi.",
        ),
        "prep_time": 10,
        "image_name": "smoothie-bowl.jpg",
    },
    {
        "title": "Placuszki owsiano-bananowe z borowkami",
        "slug": "placuszki-owsiano-bananowe-z-borowkami",
        "category_slug": "sniadania",
        "description": (
            "Miekkie placuszki bez nabialu, slodzone dojrzalym bananem. "
            "Najlepiej smakuja jeszcze cieple, z owocami i lyzka jogurtu roslinnego."
        ),
        "ingredients_text": lines(
            "2 dojrzale banany",
            "150 g zmielonych platkow owsianych",
            "180 ml napoju roslinnego",
            "1 lyzeczka proszku do pieczenia",
            "1/2 lyzeczki cynamonu",
            "szczypta soli",
            "1 lyzka oleju do smazenia",
            "100 g borowek",
            "jogurt roslinny do podania",
        ),
        "steps_text": lines(
            "Banany rozgniec widelcem, dodaj zmielone platki, napoj roslinny, proszek do pieczenia, cynamon i sol.",
            "Wymieszaj ciasto i odstaw na 5 minut, zeby platki dobrze napecznialy. Na koncu delikatnie wmieszaj polowe borowek.",
            "Rozgrzej patelnie z niewielka iloscia oleju i smaz male placuszki po 2-3 minuty z kazdej strony.",
            "Podawaj z pozostala porcja borowek i jogurtem roslinnym.",
        ),
        "prep_time": 20,
        "image_name": "placuszki-z-borowkami.jpg",
    },
    {
        "title": "Buddha bowl z tofu, ryzem i pieczona papryka",
        "slug": "buddha-bowl-z-tofu-ryzem-i-pieczona-papryka",
        "category_slug": "obiady",
        "description": (
            "Miska pelna ryzu, tofu, fasoli i pieczonych warzyw z prostym dressingiem cytrynowo-sojowym. "
            "To wygodny sposob na sycacy lunch z jednego talerza."
        ),
        "ingredients_text": lines(
            "150 g ryzu",
            "180 g tofu naturalnego",
            "1 puszka czarnej fasoli",
            "1 czerwona papryka",
            "1 zielona papryka",
            "1 mala cebula",
            "1 lyzka oleju",
            "1 lyzka sosu sojowego",
            "1 lyzeczka soku z cytryny",
            "1/2 lyzeczki wedzonej papryki",
            "sol i pieprz do smaku",
        ),
        "steps_text": lines(
            "Ugotuj ryz. Papryki pokroj w paski, cebule w piorka, skrop olejem i piecz przez okolo 20 minut w 210 stopniach.",
            "Tofu pokroj w kostke, wymieszaj z wedzona papryka i podsmaz na zloty kolor.",
            "Fasole odcedz i ogrzej chwile na patelni albo w rondelku. W kubku wymieszaj sos sojowy z cytryna i odrobina pieprzu.",
            "Uloz w misce ryz, fasole, tofu i pieczone warzywa. Polej dressingiem tuz przed podaniem.",
        ),
        "prep_time": 30,
        "image_name": "buddha-bowl-z-tofu.jpg",
    },
    {
        "title": "Salatka z ciecierzyca, pieczonym batatem i pestkami",
        "slug": "salatka-z-ciecierzyca-pieczonym-batatem-i-pestkami",
        "category_slug": "salatki",
        "description": (
            "Salatka laczaca slodycz pieczonego batata z chrupiaca ciecierzyca i kwasna zurawina. "
            "Moze byc lekkim obiadem albo sycaca kolacja."
        ),
        "ingredients_text": lines(
            "1 sredni batat",
            "1 puszka ciecierzycy",
            "2 garscie miksu salat",
            "2 lyzki pestek dyni",
            "2 lyzki suszonej zurawiny",
            "1 lyzka oliwy",
            "1 lyzeczka syropu klonowego",
            "1 lyzeczka musztardy",
            "1 lyzeczka soku z cytryny",
            "sol i pieprz do smaku",
        ),
        "steps_text": lines(
            "Batata pokroj w kostke, skrop polowa lyzki oliwy, dopraw sola i piecz przez 20-25 minut w 200 stopniach.",
            "Ciecierzyce osusz, wymieszaj z reszta oliwy i upraz na suchej patelni albo przez kilka minut w piekarniku.",
            "W kubku polacz syrop klonowy, musztarde, sok z cytryny, szczypty soli i pieprzu.",
            "Na talerzu uloz salate, batata, ciecierzyce, pestki i zurawine. Polej dressingiem przed podaniem.",
        ),
        "prep_time": 30,
        "image_name": "salatka-z-ciecierzyca.jpg",
    },
    {
        "title": "Krem pomidorowy z czerwonej soczewicy",
        "slug": "krem-pomidorowy-z-czerwonej-soczewicy",
        "category_slug": "zupy",
        "description": (
            "Gladki krem pomidorowy z dodatkiem czerwonej soczewicy, ktora nadaje mu sycosci i naturalnej gestosci. "
            "Dobra baza na szybki obiad w srodku tygodnia."
        ),
        "ingredients_text": lines(
            "1 cebula",
            "2 zabki czosnku",
            "1 marchewka",
            "1 puszka krojonych pomidorow",
            "80 g czerwonej soczewicy",
            "700 ml bulionu warzywnego",
            "1 lyzka oliwy",
            "1/2 lyzeczki suszonego oregano",
            "szczypta chili",
            "sol i pieprz do smaku",
            "lyzka jogurtu roslinnego do podania",
        ),
        "steps_text": lines(
            "Na oliwie zeszklij cebule, czosnek i marchewke pokrojona w cienkie plasterki.",
            "Dodaj pomidory, soczewice, bulion, oregano i chili. Gotuj przez 20 minut, az soczewica bedzie bardzo miekka.",
            "Zmiksuj zupe na gladki krem i dopraw sola oraz pieprzem. Jesli jest zbyt gesta, dolej troche wody.",
            "Podawaj z lyzka jogurtu roslinnego i pieczywem.",
        ),
        "prep_time": 35,
        "image_name": "krem-pomidorowy.jpg",
    },
    {
        "title": "Chlebek bananowy z orzechami wloskimi",
        "slug": "chlebek-bananowy-z-orzechami-wloskimi",
        "category_slug": "wypieki",
        "description": (
            "Wilgotny chlebek bananowy na oleju, z cynamonem i chrupiacymi orzechami. "
            "Sprawdza sie jako wypiek do kawy albo slodkie sniadanie."
        ),
        "ingredients_text": lines(
            "3 bardzo dojrzale banany",
            "220 g maki pszennej",
            "80 g cukru trzcinowego",
            "80 ml oleju roslinnego",
            "120 ml napoju roslinnego",
            "1 lyzeczka sody",
            "1 lyzeczka proszku do pieczenia",
            "1 lyzeczka cynamonu",
            "60 g orzechow wloskich",
            "szczypta soli",
        ),
        "steps_text": lines(
            "Piekarnik nagrzej do 175 stopni. Banany rozgniec, wymieszaj z cukrem, olejem i napojem roslinnym.",
            "W drugiej misce polacz make, sode, proszek do pieczenia, cynamon i sol, a potem dodaj do mokrych skladnikow.",
            "Na koncu wmieszaj posiekane orzechy, przeloz ciasto do malej keksowki i posyp dodatkowa garstka orzechow.",
            "Piecz przez 50-55 minut, az patyczek wbity w srodek wyjdzie suchy. Ostud przed krojeniem.",
        ),
        "prep_time": 70,
        "image_name": "chlebek-bananowy.jpg",
    },
    {
        "title": "Makaron z pesto pietruszkowo-bazyliowym",
        "slug": "makaron-z-pesto-pietruszkowo-bazyliowym",
        "category_slug": "obiady",
        "description": (
            "Szybki makaron z domowym pesto na bazie pietruszki, bazylii i slonecznika. "
            "Dodatek groszku i skorki cytrynowej odswieza calosc i robi z niego pelny obiad."
        ),
        "ingredients_text": lines(
            "250 g makaronu",
            "1 peczek natki pietruszki",
            "garsc lisci bazylii",
            "3 lyzki ziaren slonecznika",
            "1 zabek czosnku",
            "4 lyzki oliwy",
            "2 lyzki soku z cytryny",
            "100 g zielonego groszku",
            "2 lyzki wody z gotowania makaronu",
            "sol i pieprz do smaku",
        ),
        "steps_text": lines(
            "Ugotuj makaron al dente. Pod koniec gotowania dorzuc groszek na ostatnie 2 minuty.",
            "W blenderze zmiksuj natke, bazylie, slonecznik, czosnek, oliwe, sok z cytryny, sol i pieprz.",
            "Do gotowego pesto dodaj 2 lyzki goracej wody z makaronu, zeby sos byl bardziej kremowy.",
            "Wymieszaj makaron z groszkiem i pesto, dopraw do smaku i podawaj od razu.",
        ),
        "prep_time": 25,
        "image_name": "makaron-z-pesto.jpg",
    },
]


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


def seed_recipe_catalog(apps, schema_editor):
    Category = apps.get_model("recipes", "Category")
    Recipe = apps.get_model("recipes", "Recipe")

    categories_by_slug = {}
    for category in CATEGORIES:
        category_obj, _ = Category.objects.update_or_create(
            slug=category["slug"],
            defaults={"name": category["name"]},
        )
        categories_by_slug[category["slug"]] = category_obj

    seed_dir = Path(__file__).resolve().parent.parent / "seed_images"

    for recipe in RECIPES:
        image_path = copy_seed_image(seed_dir, recipe["image_name"])
        Recipe.objects.update_or_create(
            slug=recipe["slug"],
            defaults={
                "title": recipe["title"],
                "category": categories_by_slug[recipe["category_slug"]],
                "description": recipe["description"],
                "ingredients_text": recipe["ingredients_text"],
                "steps_text": recipe["steps_text"],
                "prep_time": recipe["prep_time"],
                "image": image_path,
                "is_published": True,
            },
        )


def unseed_recipe_catalog(apps, schema_editor):
    Category = apps.get_model("recipes", "Category")
    Recipe = apps.get_model("recipes", "Recipe")

    Recipe.objects.filter(
        slug__in=[recipe["slug"] for recipe in RECIPES]
    ).delete()

    for image_name in [recipe["image_name"] for recipe in RECIPES]:
        target = Path(settings.MEDIA_ROOT) / "recipes" / image_name
        if target.exists():
            target.unlink()

    target_dir = Path(settings.MEDIA_ROOT) / "recipes"
    if target_dir.exists() and not any(target_dir.iterdir()):
        target_dir.rmdir()

    for category in CATEGORIES:
        Category.objects.filter(
            slug=category["slug"],
            recipes__isnull=True,
        ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_recipe_catalog, unseed_recipe_catalog),
    ]
