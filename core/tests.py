from pathlib import Path
from datetime import timedelta

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from recipes.models import Category, Recipe


class TestEnvironmentConfig(TestCase):
    """FOUND-01: App uses env vars, no hardcoded secrets."""

    def test_secret_key_not_hardcoded(self):
        settings_path = Path(settings.BASE_DIR) / "backend" / "settings.py"
        content = settings_path.read_text()
        self.assertNotIn("django-insecure-", content)
        self.assertIn('env("SECRET_KEY")', content)

    def test_debug_from_env(self):
        settings_path = Path(settings.BASE_DIR) / "backend" / "settings.py"
        content = settings_path.read_text()
        self.assertIn('env("DEBUG")', content)

    def test_production_domains_included(self):
        self.assertIn("kuchennakomitywa.pl", settings.ALLOWED_HOSTS)
        self.assertIn("www.kuchennakomitywa.pl", settings.ALLOWED_HOSTS)

    def test_production_csrf_origins_included(self):
        self.assertIn(
            "https://kuchennakomitywa.pl",
            settings.CSRF_TRUSTED_ORIGINS,
        )
        self.assertIn(
            "https://www.kuchennakomitywa.pl",
            settings.CSRF_TRUSTED_ORIGINS,
        )

    def test_env_example_exists(self):
        env_example = Path(settings.BASE_DIR) / ".env.example"
        self.assertTrue(env_example.exists())


class TestStaticFiles(TestCase):
    """FOUND-04: Static files are properly served."""

    def test_staticfiles_dirs_configured(self):
        self.assertTrue(len(settings.STATICFILES_DIRS) > 0)

    def test_static_directory_exists(self):
        static_dir = Path(settings.BASE_DIR) / "static"
        self.assertTrue(static_dir.exists())

    def test_static_url_configured(self):
        self.assertEqual(settings.STATIC_URL, "/static/")


class TestMediaConfig(TestCase):
    """FOUND-05: Media upload works properly."""

    def test_media_root_configured(self):
        self.assertTrue(str(settings.MEDIA_ROOT).endswith("media"))

    def test_media_url_configured(self):
        self.assertEqual(settings.MEDIA_URL, "/media/")

    def test_media_directory_exists(self):
        media_dir = Path(settings.MEDIA_ROOT)
        self.assertTrue(media_dir.exists())


class TestHomeView(TestCase):
    """Home page returns 200."""

    def test_home_returns_200(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_home_shows_three_latest_published_recipes(self):
        category, _ = Category.objects.get_or_create(
            name="Obiady",
            slug="obiady",
        )
        older = Recipe.objects.create(
            title="Starszy przepis",
            slug="starszy-przepis",
            category=category,
            description="Starszy opis",
            ingredients_text="skladnik 1",
            steps_text="krok 1",
            prep_time=15,
        )
        newest = Recipe.objects.create(
            title="Najnowszy przepis",
            slug="najnowszy-przepis",
            category=category,
            description="Najnowszy opis",
            ingredients_text="skladnik 1",
            steps_text="krok 1",
            prep_time=20,
        )
        middle = Recipe.objects.create(
            title="Srodkowy przepis",
            slug="srodkowy-przepis",
            category=category,
            description="Srodkowy opis",
            ingredients_text="skladnik 1",
            steps_text="krok 1",
            prep_time=25,
        )
        third = Recipe.objects.create(
            title="Trzeci przepis",
            slug="trzeci-przepis",
            category=category,
            description="Trzeci opis",
            ingredients_text="skladnik 1",
            steps_text="krok 1",
            prep_time=30,
        )
        hidden = Recipe.objects.create(
            title="Ukryty przepis",
            slug="ukryty-przepis-home",
            category=category,
            description="Ukryty opis",
            ingredients_text="skladnik 1",
            steps_text="krok 1",
            prep_time=35,
            is_published=False,
        )

        now = timezone.now()
        Recipe.objects.filter(pk=older.pk).update(created_at=now + timedelta(days=1))
        Recipe.objects.filter(pk=third.pk).update(created_at=now + timedelta(days=2))
        Recipe.objects.filter(pk=middle.pk).update(created_at=now + timedelta(days=3))
        Recipe.objects.filter(pk=newest.pk).update(created_at=now + timedelta(days=4))
        Recipe.objects.filter(pk=hidden.pk).update(created_at=now + timedelta(days=5))

        response = self.client.get("/")

        latest_titles = [recipe.title for recipe in response.context["latest_recipes"]]
        self.assertEqual(
            latest_titles,
            ["Najnowszy przepis", "Srodkowy przepis", "Trzeci przepis"],
        )
        self.assertContains(response, "Najnowszy przepis")
        self.assertContains(response, "Srodkowy przepis")
        self.assertContains(response, "Trzeci przepis")
        self.assertNotContains(response, "Starszy przepis")
        self.assertNotContains(response, "Ukryty przepis")


class TestBaseTemplate(TestCase):
    """FOUND-02: base.html renders with nav, footer."""

    def test_home_page_has_navbar(self):
        response = self.client.get("/")
        self.assertContains(response, "Przepisy")
        self.assertContains(response, "Sklep")
        self.assertContains(response, "O nas")
        self.assertContains(response, "Kontakt")

    def test_home_page_has_cart_icon(self):
        response = self.client.get("/")
        self.assertContains(response, "bi-cart3")
        self.assertContains(response, 'aria-label="Koszyk"')

    def test_home_page_has_footer(self):
        response = self.client.get("/")
        self.assertContains(response, "Kuchenna Komitywa")
        self.assertContains(response, "Wszelkie prawa")

    def test_home_page_has_skip_link(self):
        response = self.client.get("/")
        self.assertContains(response, "Przejdź do treści")


class TestResponsiveLayout(TestCase):
    """FOUND-03: Pages are responsive with Bootstrap 5."""

    def test_bootstrap_css_included(self):
        response = self.client.get("/")
        self.assertContains(response, "bootstrap")

    def test_viewport_meta_tag(self):
        response = self.client.get("/")
        self.assertContains(response, "viewport")

    def test_static_css_included(self):
        response = self.client.get("/")
        self.assertRegex(
            response.content.decode(),
            r"/static/css/main(?:\.[0-9a-f]+)?\.css",
        )


class TestCookieBanner(TestCase):
    """LEGAL-03: Cookie consent banner present in page."""

    def test_cookie_banner_html_present(self):
        response = self.client.get("/")
        self.assertContains(response, 'id="cookie-banner"')

    def test_cookie_banner_has_accept_button(self):
        response = self.client.get("/")
        self.assertContains(response, 'id="cookie-accept"')
        self.assertContains(response, "Akceptuj")

    def test_cookie_banner_has_reject_button(self):
        response = self.client.get("/")
        self.assertContains(response, 'id="cookie-reject"')

    def test_cookie_banner_has_aria_attributes(self):
        response = self.client.get("/")
        self.assertContains(response, 'role="alert"')
        self.assertContains(response, 'aria-live="polite"')

    def test_cookie_consent_js_included(self):
        response = self.client.get("/")
        self.assertRegex(
            response.content.decode(),
            r"/static/js/cookie_consent(?:\.[0-9a-f]+)?\.js",
        )


class TestHeroSection(TestCase):
    """LAND-01: Hero section with mission and value proposition."""

    def test_home_has_hero_section(self):
        response = self.client.get("/")
        self.assertContains(response, "kk-hero")

    def test_hero_has_headline(self):
        response = self.client.get("/")
        self.assertContains(response, "Gotujemy z sercem")

    def test_hero_has_cta_button(self):
        response = self.client.get("/")
        self.assertContains(response, "Zobacz przepisy")
        self.assertContains(response, "kk-btn-primary")

    def test_hero_has_split_layout(self):
        response = self.client.get("/")
        self.assertContains(response, "col-lg-6")


class TestFeatureCards(TestCase):
    """LAND-01: Feature cards section."""

    def test_feature_cards_present(self):
        response = self.client.get("/")
        self.assertContains(response, "100% Ro\u015blinne")
        self.assertContains(response, "Lokalne Sk\u0142adniki")
        self.assertContains(response, "Odbi\u00f3r Osobisty")

    def test_feature_icons_present(self):
        response = self.client.get("/")
        self.assertContains(response, "bi-flower1")
        self.assertContains(response, "bi-geo-alt")
        self.assertContains(response, "bi-shop")


class TestAboutPage(TestCase):
    """LAND-02: O nas page accessible with company story."""

    def test_about_page_returns_200(self):
        response = self.client.get("/o-nas/")
        self.assertEqual(response.status_code, 200)

    def test_about_page_has_heading(self):
        response = self.client.get("/o-nas/")
        self.assertContains(response, "O nas")

    def test_about_page_has_content(self):
        response = self.client.get("/o-nas/")
        self.assertContains(response, "Kuchenna Komitywa")


class TestContactPage(TestCase):
    """LAND-03: Contact page with address and hours."""

    def test_contact_page_returns_200(self):
        response = self.client.get("/kontakt/")
        self.assertEqual(response.status_code, 200)

    def test_contact_has_address(self):
        response = self.client.get("/kontakt/")
        self.assertContains(response, "Bukowa 14")

    def test_contact_has_company_details(self):
        response = self.client.get("/kontakt/")
        self.assertContains(response, "Tomasz Steckiewicz Kuchenna Komitywa")
        self.assertContains(response, "5423485438")
        self.assertContains(response, "511 562 100")


class TestPrivacyPage(TestCase):
    """LEGAL-01: Privacy policy page accessible."""

    def test_privacy_page_returns_200(self):
        response = self.client.get("/polityka-prywatnosci/")
        self.assertEqual(response.status_code, 200)

    def test_privacy_has_heading(self):
        response = self.client.get("/polityka-prywatnosci/")
        self.assertContains(response, "Polityka prywatno\u015bci")

    def test_privacy_has_full_company_name(self):
        response = self.client.get("/polityka-prywatnosci/")
        self.assertContains(response, "TOMASZ STECKIEWICZ")
        self.assertContains(response, "5423485438")


class TestRegulationsPage(TestCase):
    """LEGAL-02: Regulations page accessible."""

    def test_regulations_page_returns_200(self):
        response = self.client.get("/regulamin/")
        self.assertEqual(response.status_code, 200)

    def test_regulations_has_heading(self):
        response = self.client.get("/regulamin/")
        self.assertContains(response, "Regulamin")

    def test_regulations_has_full_company_name(self):
        response = self.client.get("/regulamin/")
        self.assertContains(response, "TOMASZ STECKIEWICZ")
        self.assertContains(response, "5423485438")

    def test_regulations_has_14_calendar_days_for_complaints(self):
        response = self.client.get("/regulamin/")
        self.assertContains(response, "14 dni kalendarzowych")


class TestNavbarLinks(TestCase):
    """Phase 2: Navbar links wired to real URLs."""

    def test_navbar_has_about_link(self):
        response = self.client.get("/")
        self.assertContains(response, 'href="/o-nas/"')

    def test_navbar_has_contact_link(self):
        response = self.client.get("/")
        self.assertContains(response, 'href="/kontakt/"')


class TestFooterLinks(TestCase):
    """Phase 2: Footer contains legal page links."""

    def test_footer_has_privacy_link(self):
        response = self.client.get("/")
        self.assertContains(response, 'href="/polityka-prywatnosci/"')

    def test_footer_has_regulations_link(self):
        response = self.client.get("/")
        self.assertContains(response, 'href="/regulamin/"')
