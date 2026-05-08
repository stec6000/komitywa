from django.contrib.auth import get_user_model
from django.test import TestCase

from recipes.models import Category, Recipe


User = get_user_model()


class TestRecipeList(TestCase):

    def setUp(self):
        self.category = Category.objects.create(name="Desery", slug="desery")
        self.recipe1 = Recipe.objects.create(
            title="Brownie",
            slug="brownie",
            category=self.category,
            description="Pyszne brownie czekoladowe",
            ingredients_text="200g czekolady\n100g masla",
            steps_text="Rozpusc czekolade\nWymieszaj",
            prep_time=45,
        )
        self.recipe2 = Recipe.objects.create(
            title="Sernik",
            slug="sernik",
            category=self.category,
            description="Klasyczny sernik",
            ingredients_text="500g twarogu\n3 jajka",
            steps_text="Wymieszaj skladniki\nPiecz",
            prep_time=60,
        )
        self.unpublished = Recipe.objects.create(
            title="Tajny Przepis",
            slug="tajny-przepis",
            category=self.category,
            description="Nie publikowac",
            ingredients_text="tajne",
            steps_text="tajne",
            prep_time=10,
            is_published=False,
        )

    def test_list_returns_200(self):
        response = self.client.get("/przepisy/")
        self.assertEqual(response.status_code, 200)

    def test_list_shows_published_recipes(self):
        response = self.client.get("/przepisy/")
        self.assertContains(response, "Brownie")
        self.assertContains(response, "Sernik")

    def test_list_hides_unpublished(self):
        response = self.client.get("/przepisy/")
        self.assertNotContains(response, "Tajny Przepis")

    def test_list_uses_correct_template(self):
        response = self.client.get("/przepisy/")
        self.assertTemplateUsed(response, "recipes/list.html")


class TestRecipeDetail(TestCase):

    def setUp(self):
        self.category = Category.objects.create(name="Desery", slug="desery")
        self.recipe = Recipe.objects.create(
            title="Test Recipe",
            slug="test-recipe",
            category=self.category,
            description="Opis testowego przepisu",
            ingredients_text="1 cup flour\n2 eggs",
            steps_text="Mix ingredients\nBake",
            prep_time=30,
        )

    def test_detail_returns_200(self):
        response = self.client.get("/przepisy/test-recipe/")
        self.assertEqual(response.status_code, 200)

    def test_detail_shows_title(self):
        response = self.client.get("/przepisy/test-recipe/")
        self.assertContains(response, "Test Recipe")

    def test_detail_uses_correct_template(self):
        response = self.client.get("/przepisy/test-recipe/")
        self.assertTemplateUsed(response, "recipes/detail.html")

    def test_detail_404_for_unpublished(self):
        Recipe.objects.create(
            title="Ukryty",
            slug="ukryty",
            description="Ukryty przepis",
            ingredients_text="nic",
            steps_text="nic",
            prep_time=5,
            is_published=False,
        )
        response = self.client.get("/przepisy/ukryty/")
        self.assertEqual(response.status_code, 404)

    def test_detail_404_for_nonexistent(self):
        response = self.client.get("/przepisy/nonexistent/")
        self.assertEqual(response.status_code, 404)


class TestCategoryFilter(TestCase):

    def setUp(self):
        self.desery, _ = Category.objects.get_or_create(
            name="Desery",
            slug="desery",
        )
        self.obiady, _ = Category.objects.get_or_create(
            name="Obiady",
            slug="obiady",
        )
        self.recipe1 = Recipe.objects.create(
            title="Brownie Deser",
            slug="brownie-deser",
            category=self.desery,
            description="Deser brownie",
            ingredients_text="czekolada",
            steps_text="zrob",
            prep_time=30,
        )
        self.recipe2 = Recipe.objects.create(
            title="Sernik Deser",
            slug="sernik-deser",
            category=self.desery,
            description="Deser sernik",
            ingredients_text="twarog",
            steps_text="zrob",
            prep_time=60,
        )
        self.recipe3 = Recipe.objects.create(
            title="Zupa Obiadowa",
            slug="zupa-obiadowa",
            category=self.obiady,
            description="Obiad zupa",
            ingredients_text="warzywa",
            steps_text="gotuj",
            prep_time=45,
        )

    def test_filter_by_category(self):
        response = self.client.get("/przepisy/?kategoria=desery")
        self.assertContains(response, "Brownie Deser")
        self.assertContains(response, "Sernik Deser")
        self.assertNotContains(response, "Zupa Obiadowa")

    def test_filter_all_shows_all(self):
        response = self.client.get("/przepisy/")
        self.assertContains(response, "Brownie Deser")
        self.assertContains(response, "Sernik Deser")
        self.assertContains(response, "Zupa Obiadowa")


class TestRecipeSearch(TestCase):

    def setUp(self):
        self.recipe_title = Recipe.objects.create(
            title="Tort czekoladowy",
            slug="tort-czekoladowy",
            description="Pyszny tort",
            ingredients_text="maka\njajka",
            steps_text="zrob ciasto",
            prep_time=60,
        )
        self.recipe_ingredient = Recipe.objects.create(
            title="Babeczki",
            slug="babeczki",
            description="Male babeczki",
            ingredients_text="czekolada\nmaslo",
            steps_text="wymieszaj",
            prep_time=30,
        )
        self.recipe_none = Recipe.objects.create(
            title="Salatka owocowa",
            slug="salatka-owocowa",
            description="Zdrowa salatka",
            ingredients_text="jablka\nbanany",
            steps_text="pokroj",
            prep_time=10,
        )

    def test_search_by_title(self):
        response = self.client.get("/przepisy/?q=tort")
        self.assertContains(response, "Tort czekoladowy")

    def test_search_by_ingredient(self):
        response = self.client.get("/przepisy/?q=czekolada")
        self.assertContains(response, "Babeczki")

    def test_search_excludes_non_matching(self):
        response = self.client.get("/przepisy/?q=czekolada")
        self.assertNotContains(response, "Salatka owocowa")


class TestSchemaOrgMarkup(TestCase):

    def setUp(self):
        self.category = Category.objects.create(name="Desery", slug="desery")
        self.recipe = Recipe.objects.create(
            title="Brownie Testowe",
            slug="brownie-testowe",
            category=self.category,
            description="Brownie do testow",
            ingredients_text="200g czekolady\n100g masla",
            steps_text="Rozpusc czekolade\nWymieszaj",
            prep_time=45,
        )

    def test_detail_contains_json_ld_script(self):
        response = self.client.get("/przepisy/brownie-testowe/")
        self.assertContains(response, "application/ld+json")

    def test_json_ld_contains_recipe_type(self):
        response = self.client.get("/przepisy/brownie-testowe/")
        self.assertContains(response, '"@type"')
        self.assertContains(response, "Recipe")

    def test_json_ld_contains_recipe_name(self):
        response = self.client.get("/przepisy/brownie-testowe/")
        self.assertContains(response, "Brownie Testowe")


class TestRecipeTags(TestCase):

    def setUp(self):
        from recipes.models import Tag
        self.tofu = Tag.objects.create(name="tofu-tag", slug="tofu-tag")
        self.szybkie = Tag.objects.create(name="szybkie-tag", slug="szybkie-tag")
        self.cat = Category.objects.create(name="Obiady-tags", slug="obiady-tags")

        self.r_tofu_szybkie = Recipe.objects.create(
            title="Tofu Szybkie",
            slug="tofu-szybkie",
            category=self.cat,
            description="oba tagi",
            ingredients_text="x",
            steps_text="y",
            prep_time=10,
            servings=2,
            difficulty="latwy",
        )
        self.r_tofu_szybkie.tags.add(self.tofu, self.szybkie)

        self.r_tofu_only = Recipe.objects.create(
            title="Tofu Wolne",
            slug="tofu-wolne",
            category=self.cat,
            description="tylko tofu",
            ingredients_text="x",
            steps_text="y",
            prep_time=40,
            servings=2,
            difficulty="latwy",
        )
        self.r_tofu_only.tags.add(self.tofu)

        self.r_szybkie_only = Recipe.objects.create(
            title="Szybkie Bez Tofu",
            slug="szybkie-bez-tofu",
            category=self.cat,
            description="tylko szybkie",
            ingredients_text="x",
            steps_text="y",
            prep_time=8,
            servings=1,
            difficulty="latwy",
        )
        self.r_szybkie_only.tags.add(self.szybkie)

    def test_single_tag_filter(self):
        response = self.client.get("/przepisy/?tag=tofu-tag")
        self.assertContains(response, "Tofu Szybkie")
        self.assertContains(response, "Tofu Wolne")
        self.assertNotContains(response, "Szybkie Bez Tofu")

    def test_multi_tag_filter_uses_and(self):
        response = self.client.get("/przepisy/?tag=tofu-tag&tag=szybkie-tag")
        self.assertContains(response, "Tofu Szybkie")
        self.assertNotContains(response, "Tofu Wolne")
        self.assertNotContains(response, "Szybkie Bez Tofu")

    def test_tag_filter_combines_with_category_via_and(self):
        other_cat = Category.objects.create(name="Salatki-tags", slug="salatki-tags")
        Recipe.objects.create(
            title="Tofu z innej kategorii",
            slug="tofu-inna-kategoria",
            category=other_cat,
            description="x",
            ingredients_text="x",
            steps_text="y",
            prep_time=10,
            servings=1,
            difficulty="latwy",
        ).tags.add(self.tofu)
        response = self.client.get("/przepisy/?tag=tofu-tag&kategoria=obiady-tags")
        self.assertContains(response, "Tofu Szybkie")
        self.assertContains(response, "Tofu Wolne")
        self.assertNotContains(response, "Tofu z innej kategorii")


class TestRecipeBackfill(TestCase):
    """Verifies that migration 0004 backfilled the locked values on real seeded recipes."""

    def test_krem_z_bialej_fasoli_backfill(self):
        recipe = Recipe.objects.get(slug="krem-z-bialej-fasoli-ze-szparagami")
        self.assertEqual(recipe.servings, 2)
        self.assertEqual(recipe.difficulty, "latwy")
        self.assertEqual(
            set(recipe.tags.values_list("slug", flat=True)),
            {"fasola", "tofu", "pieczone", "bezglutenowe"},
        )

    def test_chlebek_bananowy_backfill(self):
        recipe = Recipe.objects.get(slug="chlebek-bananowy-z-orzechami-wloskimi")
        self.assertEqual(recipe.servings, 8)
        self.assertEqual(recipe.difficulty, "sredni")
        self.assertEqual(
            set(recipe.tags.values_list("slug", flat=True)),
            {"pieczone"},
        )

    def test_starter_tags_seeded(self):
        from recipes.models import Tag
        slugs = set(Tag.objects.values_list("slug", flat=True))
        for required in [
            "tofu", "bezglutenowe", "szybkie", "pieczone",
            "na-zimno", "ciecierzyca", "fasola", "soczewica",
        ]:
            self.assertIn(required, slugs)


class TestSchemaOrgExtras(TestCase):

    def setUp(self):
        from recipes.models import Tag
        self.cat = Category.objects.create(name="Desery-extras", slug="desery-extras")
        self.tag = Tag.objects.create(name="szybkie-extras", slug="szybkie-extras")
        self.with_tags = Recipe.objects.create(
            title="Z Tagami",
            slug="z-tagami-schema",
            category=self.cat,
            description="x",
            ingredients_text="a",
            steps_text="b",
            prep_time=15,
            servings=4,
            difficulty="latwy",
        )
        self.with_tags.tags.add(self.tag)
        self.without_tags = Recipe.objects.create(
            title="Bez Tagow",
            slug="bez-tagow-schema",
            category=self.cat,
            description="x",
            ingredients_text="a",
            steps_text="b",
            prep_time=10,
            servings=2,
            difficulty="latwy",
        )

    def test_recipe_yield_present(self):
        response = self.client.get("/przepisy/z-tagami-schema/")
        self.assertContains(response, '"recipeYield": "4"')

    def test_keywords_present_when_tags(self):
        response = self.client.get("/przepisy/z-tagami-schema/")
        self.assertContains(response, '"keywords"')
        self.assertContains(response, "szybkie-extras")

    def test_keywords_absent_when_no_tags(self):
        response = self.client.get("/przepisy/bez-tagow-schema/")
        self.assertNotContains(response, '"keywords"')
        # recipeYield should still be present.
        self.assertContains(response, '"recipeYield": "2"')


class TestRecipeAdmin(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(
            email="admin@test.com",
            password="testpass123",
        )
        self.client.login(email="admin@test.com", password="testpass123")

    def test_recipe_changelist_accessible(self):
        response = self.client.get("/admin/recipes/recipe/")
        self.assertEqual(response.status_code, 200)

    def test_category_changelist_accessible(self):
        response = self.client.get("/admin/recipes/category/")
        self.assertEqual(response.status_code, 200)

    def test_recipe_add_accessible(self):
        response = self.client.get("/admin/recipes/recipe/add/")
        self.assertEqual(response.status_code, 200)
