from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from content.models import BlogPost
from core.sitemaps import (
    BlogPostSitemap,
    ProductSitemap,
    RecipeSitemap,
    StaticViewSitemap,
)
from recipes.models import Recipe
from shop.models import Product


class SitemapFilteringTests(TestCase):
    def setUp(self):
        self.published_recipe = Recipe.objects.create(
            title="Opublikowany przepis",
            slug="opublikowany-przepis",
            description="Opis przepisu",
            ingredients_text="Składnik",
            steps_text="Krok",
            prep_time=20,
            is_published=True,
        )
        self.hidden_recipe = Recipe.objects.create(
            title="Ukryty przepis",
            slug="ukryty-przepis",
            description="Opis przepisu",
            ingredients_text="Składnik",
            steps_text="Krok",
            prep_time=20,
            is_published=False,
        )

        self.published_post = BlogPost.objects.create(
            title="Opublikowany wpis",
            slug="opublikowany-wpis",
            body="Treść wpisu",
            status="published",
            published_at=timezone.now() - timedelta(days=1),
        )
        self.draft_post = BlogPost.objects.create(
            title="Szkic wpisu",
            slug="szkic-wpisu",
            body="Treść wpisu",
            status="draft",
        )
        self.future_post = BlogPost.objects.create(
            title="Zaplanowany wpis",
            slug="zaplanowany-wpis",
            body="Treść wpisu",
            status="published",
            published_at=timezone.now() + timedelta(days=1),
        )

        self.active_product = Product.objects.create(
            title="Aktywny produkt",
            slug="aktywny-produkt",
            description="Opis produktu",
            price="25.00",
            is_active=True,
        )
        self.inactive_product = Product.objects.create(
            title="Nieaktywny produkt",
            slug="nieaktywny-produkt",
            description="Opis produktu",
            price="25.00",
            is_active=False,
        )

    def test_recipe_sitemap_contains_only_published_recipes(self):
        sitemap = RecipeSitemap()
        items = list(sitemap.items())

        self.assertIn(self.published_recipe, items)
        self.assertNotIn(self.hidden_recipe, items)
        self.assertEqual(
            sitemap.location(self.published_recipe),
            reverse("recipes:detail", kwargs={"slug": self.published_recipe.slug}),
        )
        self.assertEqual(sitemap.lastmod(self.published_recipe), self.published_recipe.updated_at)

    def test_blog_sitemap_contains_only_currently_published_posts(self):
        sitemap = BlogPostSitemap()
        items = list(sitemap.items())

        self.assertIn(self.published_post, items)
        self.assertNotIn(self.draft_post, items)
        self.assertNotIn(self.future_post, items)
        self.assertEqual(
            sitemap.location(self.published_post),
            self.published_post.get_absolute_url(),
        )
        self.assertEqual(sitemap.lastmod(self.published_post), self.published_post.updated_at)

    def test_product_sitemap_contains_only_active_products(self):
        sitemap = ProductSitemap()
        items = list(sitemap.items())

        self.assertIn(self.active_product, items)
        self.assertNotIn(self.inactive_product, items)
        self.assertEqual(
            sitemap.location(self.active_product),
            reverse("shop:detail", kwargs={"slug": self.active_product.slug}),
        )
        self.assertEqual(sitemap.lastmod(self.active_product), self.active_product.updated_at)


class SeoEndpointTests(TestCase):
    def test_static_sitemap_covers_public_landing_pages(self):
        sitemap = StaticViewSitemap()

        self.assertEqual(
            sitemap.items(),
            [
                "home",
                "orders",
                "for_cafes",
                "recipes:list",
                "content:blog_list",
                "workshops",
                "about",
                "contact",
            ],
        )

    def test_sitemap_endpoint_returns_xml(self):
        response = self.client.get(reverse("sitemap"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        self.assertContains(response, "<urlset")
        self.assertContains(response, reverse("home"))
        self.assertContains(response, reverse("recipes:list"))

    def test_robots_txt_allows_crawling_and_points_to_sitemap(self):
        response = self.client.get(reverse("robots_txt"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/plain"))
        self.assertEqual(
            response.content.decode(),
            "User-agent: *\n"
            "Allow: /\n"
            "Sitemap: http://testserver/sitemap.xml\n",
        )
