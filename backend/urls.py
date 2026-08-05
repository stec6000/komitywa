from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from core.seo import robots_txt
from core.sitemaps import (
    BlogPostSitemap,
    ProductSitemap,
    RecipeSitemap,
    StaticViewSitemap,
)


sitemaps = {
    "static": StaticViewSitemap,
    "recipes": RecipeSitemap,
    "blog": BlogPostSitemap,
    "products": ProductSitemap,
}


urlpatterns = [
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    path("przepisy/", include("recipes.urls", namespace="recipes")),
    path("blog/", include("content.urls", namespace="content")),
    path("", include("newsletter.urls")),
    path("", include("core.urls")),
    path("", include("shop.urls")),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
