import logging

from django.db import migrations


logger = logging.getLogger(__name__)


def lines(*items):
    return "\n".join(items)


# slug -> dict of corrected fields (title, description, ingredients_text, steps_text)
# Slugs intentionally remain ASCII for URL safety.
RECIPE_UPDATES = {
    "hummus-z-pieczona-ciecierzyca-i-warzywami": {
        "title": "Hummus z pieczoną ciecierzycą i warzywami",
        "description": (
            "Gładki hummus z tahini, cytryną i chrupiącą ciecierzycą z patelni. "
            "Dobry do pieczywa, surowych warzyw i jako szybka kolacja."
        ),
        "ingredients_text": lines(
            "1 puszka ciecierzycy (400 g)",
            "2 łyżki tahini",
            "sok z 1/2 cytryny",
            "1 mały ząbek czosnku",
            "3 łyżki oliwy",
            "3-4 łyżki zimnej wody",
            "1/2 łyżeczki mielonego kminu",
            "1/2 łyżeczki wędzonej papryki",
            "sól i pieprz do smaku",
            "1 marchewka",
            "1/2 ogórka",
            "garść pomidorków koktajlowych",
        ),
        "steps_text": lines(
            "Odcedź ciecierzycę, zachowaj 2 łyżki do podania. Resztę przełóż do blendera z tahini, cytryną, czosnkiem, kminem, 2 łyżkami oliwy i wodą.",
            "Miksuj do bardzo gładkiej konsystencji, dopraw solą i pieprzem. Jeśli hummus jest za gęsty, dolej jeszcze odrobinę wody.",
            "Zachowaną ciecierzycę podsmaż na 1 łyżce oliwy z wędzoną papryką przez 3-4 minuty, aż będzie lekko chrupiąca.",
            "Podawaj hummus z warzywami pokrojonymi w słupki i zrumienioną ciecierzycą na wierzchu.",
        ),
    },
    "curry-z-tofu-brokulem-i-mleczkiem-kokosowym": {
        "title": "Curry z tofu, brokułem i mleczkiem kokosowym",
        "description": (
            "Sycące curry z chrupiącym tofu, brokułem i aksamitnym sosem kokosowym. "
            "Najlepiej smakuje z ryżem jaśminowym i odrobiną limonki."
        ),
        "ingredients_text": lines(
            "180 g ryżu jaśminowego",
            "180 g tofu naturalnego",
            "1/2 brokułu",
            "1 marchewka",
            "1 cebula",
            "2 ząbki czosnku",
            "1 łyżka pasty curry albo 2 łyżeczki curry w proszku",
            "400 ml mleczka kokosowego",
            "100 ml wody",
            "1 łyżka sosu sojowego",
            "1 łyżeczka soku z limonki",
            "1 łyżka oleju",
            "sól do smaku",
        ),
        "steps_text": lines(
            "Ugotuj ryż według instrukcji na opakowaniu. Tofu odciśnij, pokrój w kostkę i oprusz szczyptą soli.",
            "Na patelni rozgrzej olej, zrumień tofu, a potem odłóż je na talerz. Na tej samej patelni zeszklij cebulę, czosnek i marchewkę pokrojoną w cienkie półplasterki.",
            "Dodaj brokuł podzielony na małe różyczki i pastę curry. Wlej mleczko kokosowe, wodę i sos sojowy, a potem gotuj 8-10 minut, aż warzywa zmiękną.",
            "Włóż tofu z powrotem do sosu, dopraw sokiem z limonki i podawaj z gorącym ryżem.",
        ),
    },
    "chili-sin-carne-z-czarna-fasola": {
        "title": "Chili sin carne z czarną fasolą",
        "description": (
            "Gęste chili na bazie pomidorów, fasoli i papryki, z wyraźnym aromatem kminu i kakao. "
            "To prosty obiad, który smakuje jeszcze lepiej następnego dnia."
        ),
        "ingredients_text": lines(
            "150 g ryżu",
            "1 puszka czarnej fasoli",
            "1 puszka krojonych pomidorów",
            "1 czerwona papryka",
            "1 cebula",
            "2 ząbki czosnku",
            "100 g kukurydzy",
            "1 łyżka koncentratu pomidorowego",
            "1 łyżeczka mielonego kminu",
            "1 łyżeczka wędzonej papryki",
            "1/2 łyżeczki chili",
            "1/2 łyżeczki kakao",
            "1 łyżka oleju",
            "sól i pieprz do smaku",
        ),
        "steps_text": lines(
            "Ugotuj ryż. Fasolę odcedź, a paprykę, cebulę i czosnek drobno posiekaj.",
            "Na oleju zeszklij cebulę, dodaj czosnek i paprykę, a po 2 minutach koncentrat oraz przyprawy.",
            "Wlej pomidory, dodaj fasolę i kukurydzę, dopraw kakao, solą oraz pieprzem. Gotuj na małym ogniu przez 15-20 minut, aż sos zgęstnieje.",
            "Podawaj chili z ryżem i ulubionymi ziołami albo świeżą kolendrą.",
        ),
    },
    "smoothie-bowl-z-mango-i-bananem": {
        "title": "Smoothie bowl z mango i bananem",
        "description": (
            "Gęste śniadanie z mrożonych owoców, płatków owsianych i masła orzechowego. "
            "Kilka dodatków wystarczy, żeby zamienić je w pełny posiłek."
        ),
        "ingredients_text": lines(
            "2 mrożone banany",
            "150 g mrożonego mango",
            "100 ml napoju owsianego",
            "2 łyżki płatków owsianych",
            "1 łyżka masła orzechowego",
            "1 łyżeczka soku z limonki",
            "granola do podania",
            "borówki do podania",
            "wiórki kokosowe do podania",
        ),
        "steps_text": lines(
            "Banany i mango przełóż do blendera razem z napojem owsianym, płatkami, masłem orzechowym i sokiem z limonki.",
            "Miksuj krótko, tylko do uzyskania gęstej i kremowej konsystencji. Jeśli trzeba, dodaj łyżkę napoju więcej.",
            "Przełóż smoothie do miski i wyrównaj wierzch łyżką.",
            "Podawaj od razu z granolą, borówkami i wiórkami kokosowymi.",
        ),
    },
    "placuszki-owsiano-bananowe-z-borowkami": {
        "title": "Placuszki owsiano-bananowe z borówkami",
        "description": (
            "Miękkie placuszki bez nabiału, słodzone dojrzałym bananem. "
            "Najlepiej smakują jeszcze ciepłe, z owocami i łyżką jogurtu roślinnego."
        ),
        "ingredients_text": lines(
            "2 dojrzałe banany",
            "150 g zmielonych płatków owsianych",
            "180 ml napoju roślinnego",
            "1 łyżeczka proszku do pieczenia",
            "1/2 łyżeczki cynamonu",
            "szczypta soli",
            "1 łyżka oleju do smażenia",
            "100 g borówek",
            "jogurt roślinny do podania",
        ),
        "steps_text": lines(
            "Banany rozgnieć widelcem, dodaj zmielone płatki, napój roślinny, proszek do pieczenia, cynamon i sól.",
            "Wymieszaj ciasto i odstaw na 5 minut, żeby płatki dobrze napęczniały. Na końcu delikatnie wmieszaj połowę borówek.",
            "Rozgrzej patelnię z niewielką ilością oleju i smaż małe placuszki po 2-3 minuty z każdej strony.",
            "Podawaj z pozostałą porcją borówek i jogurtem roślinnym.",
        ),
    },
    "buddha-bowl-z-tofu-ryzem-i-pieczona-papryka": {
        "title": "Buddha bowl z tofu, ryżem i pieczoną papryką",
        "description": (
            "Miska pełna ryżu, tofu, fasoli i pieczonych warzyw z prostym dressingiem cytrynowo-sojowym. "
            "To wygodny sposób na sycący lunch z jednego talerza."
        ),
        "ingredients_text": lines(
            "150 g ryżu",
            "180 g tofu naturalnego",
            "1 puszka czarnej fasoli",
            "1 czerwona papryka",
            "1 zielona papryka",
            "1 mała cebula",
            "1 łyżka oleju",
            "1 łyżka sosu sojowego",
            "1 łyżeczka soku z cytryny",
            "1/2 łyżeczki wędzonej papryki",
            "sól i pieprz do smaku",
        ),
        "steps_text": lines(
            "Ugotuj ryż. Papryki pokrój w paski, cebulę w piórka, skrop olejem i piecz przez około 20 minut w 210 stopniach.",
            "Tofu pokrój w kostkę, wymieszaj z wędzoną papryką i podsmaż na złoty kolor.",
            "Fasolę odcedź i ogrzej chwilę na patelni albo w rondelku. W kubku wymieszaj sos sojowy z cytryną i odrobiną pieprzu.",
            "Ułóż w misce ryż, fasolę, tofu i pieczone warzywa. Polej dressingiem tuż przed podaniem.",
        ),
    },
    "salatka-z-ciecierzyca-pieczonym-batatem-i-pestkami": {
        "title": "Sałatka z ciecierzycą, pieczonym batatem i pestkami",
        "description": (
            "Sałatka łącząca słodycz pieczonego batata z chrupiącą ciecierzycą i kwaśną żurawiną. "
            "Może być lekkim obiadem albo sycącą kolacją."
        ),
        "ingredients_text": lines(
            "1 średni batat",
            "1 puszka ciecierzycy",
            "2 garście miksu sałat",
            "2 łyżki pestek dyni",
            "2 łyżki suszonej żurawiny",
            "1 łyżka oliwy",
            "1 łyżeczka syropu klonowego",
            "1 łyżeczka musztardy",
            "1 łyżeczka soku z cytryny",
            "sól i pieprz do smaku",
        ),
        "steps_text": lines(
            "Batata pokrój w kostkę, skrop połową łyżki oliwy, dopraw solą i piecz przez 20-25 minut w 200 stopniach.",
            "Ciecierzycę osusz, wymieszaj z resztą oliwy i upraż na suchej patelni albo przez kilka minut w piekarniku.",
            "W kubku połącz syrop klonowy, musztardę, sok z cytryny, szczypty soli i pieprzu.",
            "Na talerzu ułóż sałatę, batata, ciecierzycę, pestki i żurawinę. Polej dressingiem przed podaniem.",
        ),
    },
    "krem-pomidorowy-z-czerwonej-soczewicy": {
        "title": "Krem pomidorowy z czerwonej soczewicy",
        "description": (
            "Gładki krem pomidorowy z dodatkiem czerwonej soczewicy, która nadaje mu sycości i naturalnej gęstości. "
            "Dobra baza na szybki obiad w środku tygodnia."
        ),
        "ingredients_text": lines(
            "1 cebula",
            "2 ząbki czosnku",
            "1 marchewka",
            "1 puszka krojonych pomidorów",
            "80 g czerwonej soczewicy",
            "700 ml bulionu warzywnego",
            "1 łyżka oliwy",
            "1/2 łyżeczki suszonego oregano",
            "szczypta chili",
            "sól i pieprz do smaku",
            "łyżka jogurtu roślinnego do podania",
        ),
        "steps_text": lines(
            "Na oliwie zeszklij cebulę, czosnek i marchewkę pokrojoną w cienkie plasterki.",
            "Dodaj pomidory, soczewicę, bulion, oregano i chili. Gotuj przez 20 minut, aż soczewica będzie bardzo miękka.",
            "Zmiksuj zupę na gładki krem i dopraw solą oraz pieprzem. Jeśli jest zbyt gęsta, dolej trochę wody.",
            "Podawaj z łyżką jogurtu roślinnego i pieczywem.",
        ),
    },
    "chlebek-bananowy-z-orzechami-wloskimi": {
        "title": "Chlebek bananowy z orzechami włoskimi",
        "description": (
            "Wilgotny chlebek bananowy na oleju, z cynamonem i chrupiącymi orzechami. "
            "Sprawdza się jako wypiek do kawy albo słodkie śniadanie."
        ),
        "ingredients_text": lines(
            "3 bardzo dojrzałe banany",
            "220 g mąki pszennej",
            "80 g cukru trzcinowego",
            "80 ml oleju roślinnego",
            "120 ml napoju roślinnego",
            "1 łyżeczka sody",
            "1 łyżeczka proszku do pieczenia",
            "1 łyżeczka cynamonu",
            "60 g orzechów włoskich",
            "szczypta soli",
        ),
        "steps_text": lines(
            "Piekarnik nagrzej do 175 stopni. Banany rozgnieć, wymieszaj z cukrem, olejem i napojem roślinnym.",
            "W drugiej misce połącz mąkę, sodę, proszek do pieczenia, cynamon i sól, a potem dodaj do mokrych składników.",
            "Na końcu wmieszaj posiekane orzechy, przełóż ciasto do małej keksówki i posyp dodatkową garstką orzechów.",
            "Piecz przez 50-55 minut, aż patyczek wbity w środek wyjdzie suchy. Ostudź przed krojeniem.",
        ),
    },
    "makaron-z-pesto-pietruszkowo-bazyliowym": {
        "title": "Makaron z pesto pietruszkowo-bazyliowym",
        "description": (
            "Szybki makaron z domowym pesto na bazie pietruszki, bazylii i słonecznika. "
            "Dodatek groszku i skórki cytrynowej odświeża całość i robi z niego pełny obiad."
        ),
        "ingredients_text": lines(
            "250 g makaronu",
            "1 pęczek natki pietruszki",
            "garść liści bazylii",
            "3 łyżki ziaren słonecznika",
            "1 ząbek czosnku",
            "4 łyżki oliwy",
            "2 łyżki soku z cytryny",
            "100 g zielonego groszku",
            "2 łyżki wody z gotowania makaronu",
            "sól i pieprz do smaku",
        ),
        "steps_text": lines(
            "Ugotuj makaron al dente. Pod koniec gotowania dorzuć groszek na ostatnie 2 minuty.",
            "W blenderze zmiksuj natkę, bazylię, słonecznik, czosnek, oliwę, sok z cytryny, sól i pieprz.",
            "Do gotowego pesto dodaj 2 łyżki gorącej wody z makaronu, żeby sos był bardziej kremowy.",
            "Wymieszaj makaron z groszkiem i pesto, dopraw do smaku i podawaj od razu.",
        ),
    },
    "krem-z-bialej-fasoli-ze-szparagami": {
        "title": "Krem z białej fasoli ze szparagami i pomidorkami",
        "description": (
            "Aksamitny krem z białej fasoli i tofu z odświeżającą nutą cytryny i mięty, "
            "podany z pieczonymi szparagami, pomidorkami i prażonymi migdałami. "
            "Najlepiej smakuje z chrupiącym pieczywem - jako lekka kolacja albo elegancka przekąska na stół."
        ),
        "ingredients_text": lines(
            "1 puszka białej fasoli (400 g), odsączona",
            "1 kostka tofu naturalnego (180-200 g)",
            "100 ml wody",
            "30 g soku z cytryny (około 2 łyżki)",
            "1 ząbek czosnku",
            "6 g soli (1 płaska łyżeczka)",
            "kilka świeżych listków mięty",
            "16 szparagów (najlepiej zielonych)",
            "16 pomidorków koktajlowych",
            "garść prażonych migdałów, grubo posiekanych",
            "chrupiący olej chili lub podsmażona cebulka - do polania",
            "oliwa do skropienia warzyw",
            "sól do warzyw",
            "świeżo mielony pieprz do podania",
        ),
        "steps_text": lines(
            "Nagrzej piekarnik do 180 stopni. Szparagi obierz z twardych końców, ułóż razem z pomidorkami na blasze wyłożonej papierem do pieczenia, skrop oliwą i posyp szczyptą soli.",
            "Piecz warzywa przez około 15 minut, aż szparagi będą miękkie ale wciąż jędrne, a pomidorki zaczną pękać i puszczać sok.",
            "W tym czasie do kielicha blendera włóż odsączoną białą fasolę, tofu, wodę, sok z cytryny, czosnek, sól i listki mięty. Miksuj na wysokich obrotach do uzyskania bardzo gładkiej, kremowej konsystencji - jeżeli krem jest zbyt gęsty, dolej łyżkę wody.",
            "Spróbuj i dopraw do smaku - jeżeli trzeba, dodaj odrobinę soku z cytryny lub szczyptę soli.",
            "Wyłóż krem na płaski talerz i rozprowadź łyżką, robiąc niewielkie zagłębienie na środku.",
            "Na wierzchu ułóż pieczone szparagi i pomidorki, polej chrupiącym olejem chili (lub podsmażoną na złoto cebulką) i posyp prażonymi migdałami oraz świeżo mielonym pieprzem.",
            "Podawaj od razu, najlepiej z chrupiącym chlebem lub grzankami - doskonałe do dzielenia na środku stołu.",
        ),
    },
}


# Tag slug -> display name. Only "na-zimno" gets a space-separated display name;
# the rest stay as-is (already ASCII without diacritics by design).
TAG_NAME_UPDATES = {
    "na-zimno": "na zimno",
}


def restore_polish_diacritics(apps, schema_editor):
    Recipe = apps.get_model("recipes", "Recipe")
    Tag = apps.get_model("recipes", "Tag")

    for slug, fields in RECIPE_UPDATES.items():
        Recipe.objects.filter(slug=slug).update(**fields)

    for slug, name in TAG_NAME_UPDATES.items():
        Tag.objects.filter(slug=slug).update(name=name)


def reverse_noop(apps, schema_editor):
    logger.warning("Reverse not supported")


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0004_add_tags_servings_difficulty_notes"),
    ]

    operations = [
        migrations.RunPython(restore_polish_diacritics, migrations.RunPython.noop),
    ]
