from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from content.models import BlogPost
from recipes.models import Recipe
from shop.models import Product


class StaticViewSitemap(Sitemap):
    """Public landing pages that should be discoverable by search engines."""

    pages = {
        "home": {"changefreq": "weekly", "priority": 1.0},
        "orders": {"changefreq": "daily", "priority": 0.9},
        "for_cafes": {"changefreq": "monthly", "priority": 0.8},
        "recipes:list": {"changefreq": "weekly", "priority": 0.8},
        "content:blog_list": {"changefreq": "weekly", "priority": 0.8},
        "workshops": {"changefreq": "weekly", "priority": 0.7},
        "about": {"changefreq": "monthly", "priority": 0.6},
        "contact": {"changefreq": "monthly", "priority": 0.6},
    }

    def items(self):
        return list(self.pages)

    def location(self, item):
        return reverse(item)

    def changefreq(self, item):
        return self.pages[item]["changefreq"]

    def priority(self, item):
        return self.pages[item]["priority"]


class RecipeSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Recipe.objects.filter(is_published=True)

    def location(self, item):
        return reverse("recipes:detail", kwargs={"slug": item.slug})

    def lastmod(self, item):
        return item.updated_at


class BlogPostSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return BlogPost.objects.published()

    def location(self, item):
        return item.get_absolute_url()

    def lastmod(self, item):
        return item.updated_at


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Product.objects.available_in_shop()

    def location(self, item):
        return reverse("shop:detail", kwargs={"slug": item.slug})

    def lastmod(self, item):
        return item.updated_at
