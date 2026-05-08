---
phase: quick
plan: 260508-hne
type: execute
wave: 1
depends_on: []
files_modified:
  - recipes/seed_images/krem-z-bialej-fasoli.jpg
  - recipes/seed_images/README.md
  - recipes/migrations/0003_add_krem_z_bialej_fasoli.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "Recipe count w bazie roenie z 10 do 11 po wykonaniu migracji"
    - "Nowy przepis 'Krem z bialej fasoli ze szparagami i pomidorkami' jest opublikowany (is_published=True)"
    - "Zdjecie przepisu jest dostepne pod MEDIA_ROOT/recipes/krem-z-bialej-fasoli.jpg"
    - "Zaden tekst w nowym przepisie nie zawiera polskich znakow diakrytycznych"
    - "Przepis jest widoczny na liscie /przepisy/ i pod /przepisy/krem-z-bialej-fasoli-ze-szparagami/"
    - "Migracja jest idempotentna -- ponowne uruchomienie nie tworzy duplikatu"
  artifacts:
    - path: "recipes/seed_images/krem-z-bialej-fasoli.jpg"
      provides: "Zdjecie przepisu w formacie JPEG (skonwertowane z PNG)"
    - path: "recipes/migrations/0003_add_krem_z_bialej_fasoli.py"
      provides: "Data migration dodajaca nowy przepis (RunPython, idempotentny)"
      contains: "krem-z-bialej-fasoli-ze-szparagami"
    - path: "recipes/seed_images/README.md"
      provides: "Zaktualizowany manifest seed images z nowym wpisem"
  key_links:
    - from: "recipes/migrations/0003_add_krem_z_bialej_fasoli.py"
      to: "recipes/seed_images/krem-z-bialej-fasoli.jpg"
      via: "shutil.copyfile w copy_seed_image"
      pattern: "krem-z-bialej-fasoli\\.jpg"
    - from: "recipes/migrations/0003_add_krem_z_bialej_fasoli.py"
      to: "recipes/migrations/0002_seed_recipe_catalog.py"
      via: "Migration.dependencies"
      pattern: "0002_seed_recipe_catalog"
---

<objective>
Dodaj nowy przepis "Krem z bialej fasoli ze szparagami i pomidorkami" do katalogu przepisow poprzez data migration recipes/0003, dokladnie wzorujac sie na istniejacym 0002_seed_recipe_catalog. Skopiuj/skonwertuj zdjecie z /home/tomo/Pobrane na recipes/seed_images/krem-z-bialej-fasoli.jpg i zarejestruj migracje. Calosc po polsku bez znakow diakrytycznych, zgodnie z konwencja istniejacych przepisow.

Purpose: Rozszerzyc katalog o kolejny wegetarianski przepis (10 -> 11), pokazac elegancko zaaranzowane danie do podania z chlebem.
Output: Plik migracji + zdjecie JPEG + zaktualizowany README seed_images.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md
@recipes/models.py
@recipes/migrations/0002_seed_recipe_catalog.py
@recipes/seed_images/README.md

<interfaces>
<!-- Wzor: pelny RunPython migration matching 0002 structure -->
<!-- Recipe model fields (from recipes/models.py): -->
<!--   title, slug, category (FK Category by slug), description, -->
<!--   ingredients_text, steps_text, prep_time (PositiveSmallIntegerField, minuty), -->
<!--   image (ImageField, upload_to='recipes/'), is_published (default True) -->
<!--   NIE MA pol: servings, tags, difficulty -- nie wymyslaj. -->

<!-- Helper z 0002 do reuzycia (skopiowac inline lub re-zaimportowac z 0002): -->
<!-- def lines(*items): return "\n".join(items) -->
<!-- def copy_seed_image(seed_dir, image_name): shutil.copyfile do MEDIA_ROOT/recipes/ -->

<!-- Istniejace kategorie (slug-only, juz seedowane przez 0002): -->
<!--   sniadania, obiady, przekaski, salatki, zupy, wypieki -->
<!-- Wybor: "przekaski" (danie do podania z chlebem, tapas-style). -->

<!-- Konwencja stylu zgodna z 0002: -->
<!--   - kazdy ingredient w osobnej linii (unique sentence per line), -->
<!--   - kazdy krok w osobnej linii, kroki konkretne i zwiezle, -->
<!--   - description: 2 zdania w prozaicznym tonie -- charakter dania + wskazowka serwowania, -->
<!--   - BEZ znakow diakrytycznych (a/e/o/n/c/s/z/l zamiast a/e/o/n/c/s/z/z/l). -->
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Skonwertuj PNG na JPEG i zapisz w recipes/seed_images/</name>
  <files>recipes/seed_images/krem-z-bialej-fasoli.jpg, recipes/seed_images/README.md</files>
  <action>
Zrodlowy plik PNG: /home/tomo/Pobrane/ChatGPT Image 8 maj 2026, 12_36_25.png (PNG, 1122x1402 RGB).

Konwencja seed_images to JPG. Skonwertuj PNG na JPEG za pomoca Pillow (juz w requirements.txt, dostepny w .venv). Uzyj jednorazowego skryptu zamiast `cp` -- plik jest PNG-em, nie JPEG-em.

Wykonaj jednorazowy skrypt (z .venv):

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
from PIL import Image

src = Path("/home/tomo/Pobrane/ChatGPT Image 8 maj 2026, 12_36_25.png")
dst = Path("recipes/seed_images/krem-z-bialej-fasoli.jpg")
dst.parent.mkdir(parents=True, exist_ok=True)

img = Image.open(src).convert("RGB")
# Optionally downscale to similar dimensions to inne seed images (~1400px po dluzszej krawedzi).
max_side = 1400
w, h = img.size
if max(w, h) > max_side:
    scale = max_side / max(w, h)
    img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
img.save(dst, format="JPEG", quality=85, optimize=True, progressive=True)
print(f"Saved {dst} -- size: {dst.stat().st_size} bytes, dims: {img.size}")
PY
```

Nastepnie zaktualizuj `recipes/seed_images/README.md`:
- W sekcji "Source:" zostaw istniejacy tekst Pexels (nie usuwaj historii).
- Dodaj na koncu listy "Assets:" nowy wpis:
  `- \`krem-z-bialej-fasoli.jpg\` - User-supplied image (ChatGPT-generated, 2026-05-08).`

Zachowaj istniejacy format README (myslniki, backticks, jeden wpis na linie).
  </action>
  <verify>
    <automated>test -f recipes/seed_images/krem-z-bialej-fasoli.jpg && file recipes/seed_images/krem-z-bialej-fasoli.jpg | grep -q "JPEG image data" && grep -q "krem-z-bialej-fasoli.jpg" recipes/seed_images/README.md</automated>
  </verify>
  <done>JPEG file exists w recipes/seed_images/, jest poprawnym JPEG-em (file potwierdza), README ma nowy wpis.</done>
</task>

<task type="auto">
  <name>Task 2: Utworz migracje 0003_add_krem_z_bialej_fasoli.py</name>
  <files>recipes/migrations/0003_add_krem_z_bialej_fasoli.py</files>
  <action>
Utworz nowa data migration sciscle wzorujac sie strukturalnie na `recipes/migrations/0002_seed_recipe_catalog.py`. Migracja MUSI byc idempotentna (uzyj `Recipe.objects.update_or_create(slug=..., defaults={...})`) i bezpieczna do ponownego uruchomienia.

Wymagania:
- `dependencies = [("recipes", "0002_seed_recipe_catalog")]`
- Forward function `add_krem_z_bialej_fasoli(apps, schema_editor)` -- pobiera `Recipe = apps.get_model("recipes", "Recipe")` i `Category = apps.get_model("recipes", "Category")`, znajduje kategorie "przekaski" przez `Category.objects.get(slug="przekaski")` (juz istnieje po 0002), kopiuje seed image i wola `update_or_create`.
- Reverse function `remove_krem_z_bialej_fasoli(apps, schema_editor)` -- usuwa wpis o slugu `krem-z-bialej-fasoli-ze-szparagami` i kasuje plik z MEDIA_ROOT/recipes/krem-z-bialej-fasoli.jpg jezeli istnieje.
- Skopiuj inline pomocnicze funkcje (`lines`, `copy_seed_image`) zamiast importowac z 0002 (Django zniecheca importy miedzy migracjami).
- `RunPython(add_..., remove_...)`.

Wartosc dictu RECIPE (cala tresc bez polskich diakrytykow -- strict ASCII Polish):

```python
RECIPE = {
    "title": "Krem z bialej fasoli ze szparagami i pomidorkami",
    "slug": "krem-z-bialej-fasoli-ze-szparagami",
    "category_slug": "przekaski",
    "description": (
        "Aksamitny krem z bialej fasoli i tofu z odswiezajaca nuta cytryny i mietta, "
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
```

UWAGA na diakrytyki -- powyzszy tekst jest jiz oczyszczony, zachowaj go 1:1. (Sprawdz: brak a/e/o/n/c/s/z/z/l po wkleceniu.)

Pelna struktura migracji:

```python
import shutil
from pathlib import Path

from django.conf import settings
from django.db import migrations


def lines(*items):
    return "\n".join(items)


RECIPE = { ... }   # <- jak wyzej


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
```

KRYTYCZNE -- przed zapisem pliku przeszukaj caly tekst migracji (description, ingredients_text, steps_text, comments) i potwierdz brak znakow: a e o n c s z z l. Uzyj polecenia weryfikujacego (patrz verify) zanim oznaczysz task za zrobiony.

Konwencja stringow: double quotes wszedzie (zgodnie z CLAUDE.md).
  </action>
  <verify>
    <automated>test -f recipes/migrations/0003_add_krem_z_bialej_fasoli.py && python -c "import re,sys; t=open('recipes/migrations/0003_add_krem_z_bialej_fasoli.py').read(); bad=[c for c in 'aeoncszzl' if c in t]; sys.exit(0 if not bad else 1)" && grep -q "krem-z-bialej-fasoli-ze-szparagami" recipes/migrations/0003_add_krem_z_bialej_fasoli.py && grep -q "0002_seed_recipe_catalog" recipes/migrations/0003_add_krem_z_bialej_fasoli.py</automated>
  </verify>
  <done>Plik migracji istnieje, brak polskich diakrytykow w calym pliku, slug i dependency obecne, kod parsuje sie jako poprawny Python (`python -c "import ast; ast.parse(open('recipes/migrations/0003_add_krem_z_bialej_fasoli.py').read())"`).</done>
</task>

<task type="auto">
  <name>Task 3: Uruchom migracje i potwierdz Recipe count 10 -> 11</name>
  <files>(no file changes -- runtime verification only)</files>
  <action>
Po utworzeniu migracji uruchom ja z .venv i potwierdz, ze:
1. Migracja przechodzi bez bledow.
2. Liczba Recipe w bazie roenie z 10 do 11.
3. Nowy przepis ma is_published=True i poprawnie ustawiony image.
4. Powtorne uruchomienie migracji nie tworzy duplikatu (idempotentnosc).

Komendy do wykonania (kazda osobno, sprawdzic exit code):

```bash
# 1. Sprawdz stan przed migracja (oczekiwana: 10 przepisow).
.venv/bin/python manage.py shell -c "from recipes.models import Recipe; print('BEFORE:', Recipe.objects.count())"

# 2. Pokaz nieuruchomione migracje (powinno zawierac 0003_add_krem_z_bialej_fasoli).
.venv/bin/python manage.py showmigrations recipes

# 3. Uruchom migracje.
.venv/bin/python manage.py migrate recipes

# 4. Potwierdz licze 11 i ze nowy przepis istnieje + ma image.
.venv/bin/python manage.py shell -c "from recipes.models import Recipe; r = Recipe.objects.get(slug='krem-z-bialej-fasoli-ze-szparagami'); print('AFTER:', Recipe.objects.count()); print('TITLE:', r.title); print('IMAGE:', r.image.name); print('PUBLISHED:', r.is_published); print('CATEGORY:', r.category.slug if r.category else None)"

# 5. (Sanity) -- ponowne uruchomienie nie zmienia liczby (idempotentnosc).
.venv/bin/python manage.py migrate recipes
.venv/bin/python manage.py shell -c "from recipes.models import Recipe; assert Recipe.objects.count() == 11, Recipe.objects.count(); print('IDEMPOTENT OK')"

# 6. (Sanity) -- plik image fizycznie skopiowany do MEDIA_ROOT.
.venv/bin/python manage.py shell -c "from django.conf import settings; from pathlib import Path; p = Path(settings.MEDIA_ROOT) / 'recipes' / 'krem-z-bialej-fasoli.jpg'; print('MEDIA file exists:', p.exists(), p)"
```

Oczekiwane wyniki:
- BEFORE: 10
- AFTER: 11
- TITLE: Krem z bialej fasoli ze szparagami i pomidorkami
- IMAGE: recipes/krem-z-bialej-fasoli.jpg
- PUBLISHED: True
- CATEGORY: przekaski
- IDEMPOTENT OK
- MEDIA file exists: True

Jezeli BEFORE != 10, oznacz to w summary -- to nie blokuje zadania (poprzednie quick taski mogly dodac przepisy), ale licze AFTER musi byc BEFORE+1.
  </action>
  <verify>
    <automated>.venv/bin/python manage.py migrate recipes && .venv/bin/python manage.py shell -c "from recipes.models import Recipe; assert Recipe.objects.filter(slug='krem-z-bialej-fasoli-ze-szparagami', is_published=True).exists(); from django.conf import settings; from pathlib import Path; assert (Path(settings.MEDIA_ROOT) / 'recipes' / 'krem-z-bialej-fasoli.jpg').exists()"</automated>
  </verify>
  <done>Migracja przeszla bez bledow, Recipe.objects.count() pokazuje BEFORE+1, nowy przepis istnieje z image i is_published=True, ponowne migrate nie tworzy duplikatu, plik jpg jest w MEDIA_ROOT/recipes/.</done>
</task>

</tasks>

<verification>
End-to-end checks:
1. `file recipes/seed_images/krem-z-bialej-fasoli.jpg` -> "JPEG image data"
2. `python -c "import ast; ast.parse(open('recipes/migrations/0003_add_krem_z_bialej_fasoli.py').read())"` -> exit 0
3. Brak polskich diakrytykow w pliku migracji (grep -P pattern lub Python check w Task 2 verify).
4. `.venv/bin/python manage.py migrate recipes` przechodzi bez bledow.
5. Recipe.objects.count() roenie o 1.
6. Nowy przepis ma `is_published=True`, `category.slug == "przekaski"`, `image.name == "recipes/krem-z-bialej-fasoli.jpg"`.
7. (Manualnie -- opcjonalne) odwiedz `/przepisy/krem-z-bialej-fasoli-ze-szparagami/` w devie i potwierdz, ze strona renderuje sie z poprawnym tytulem, opisem, krokami i zdjeciem.
</verification>

<success_criteria>
- Plik recipes/seed_images/krem-z-bialej-fasoli.jpg istnieje i jest valid JPEG
- recipes/seed_images/README.md ma wpis o nowym pliku
- recipes/migrations/0003_add_krem_z_bialej_fasoli.py istnieje, jest poprawnym Pythonem, nie zawiera diakrytykow, ma dependency na 0002 i RunPython z forward+reverse
- Po `manage.py migrate recipes` Recipe.objects.count() = previous + 1
- Recipe.objects.get(slug="krem-z-bialej-fasoli-ze-szparagami") zwraca obiekt z is_published=True, category.slug="przekaski", non-empty image
- Powtorne `migrate recipes` nie zmienia liczby (idempotentnosc)
</success_criteria>

<output>
After completion, create `.planning/quick/260508-hne-dodaj-przepis-krem-z-bia-ej-fasoli-ze-sz/260508-hne-SUMMARY.md` zawierajace:
- Co zostalo dodane (slug, kategoria, prep_time, image filename)
- Recipe count BEFORE / AFTER
- Wszelkie odchylenia od oryginalnych user notes (np. "porcje" pominiete bo nie ma takiego pola)
- Lista plikow zmienionych
</output>
