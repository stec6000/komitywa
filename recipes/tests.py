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
