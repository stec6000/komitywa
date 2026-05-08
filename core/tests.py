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

    def test_home_shows_latest_published_recipes(self):
        """Home shows 1 featured + 3 grid (top 4 latest); older + unpublished hidden."""
        category, _ = Category.objects.get_or_create(
            name="Obiady",
            slug="obiady",
        )
        recipes = []
        for i, title in enumerate([
            "Najstarszy przepis",
            "Czwarty przepis",
            "Trzeci przepis",
            "Srodkowy przepis",
            "Najnowszy przepis",
        ]):
            recipes.append(Recipe.objects.create(
                title=title,
                slug=title.lower().replace(" ", "-"),
                category=category,
                description=f"Opis {i}",
                ingredients_text="skladnik 1",
                steps_text="krok 1",
                prep_time=15 + i * 5,
            ))
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
        for i, r in enumerate(recipes):
            Recipe.objects.filter(pk=r.pk).update(created_at=now + timedelta(days=i))
        Recipe.objects.filter(pk=hidden.pk).update(created_at=now + timedelta(days=10))

        response = self.client.get("/")

        # Top 4 visible: newest as featured + next 3 in grid
        self.assertContains(response, "Najnowszy przepis")
        self.assertContains(response, "Srodkowy przepis")
        self.assertContains(response, "Trzeci przepis")
        self.assertContains(response, "Czwarty przepis")
        # Oldest + unpublished hidden
        self.assertNotContains(response, "Najstarszy przepis")
        self.assertNotContains(response, "Ukryty przepis")
        # Featured contract
        self.assertEqual(
            response.context["featured_recipe"].title,
            "Najnowszy przepis",
        )
        feed_titles = [r.title for r in response.context["feed_recipes"]]
        self.assertEqual(feed_titles, [
            "Srodkowy przepis", "Trzeci przepis", "Czwarty przepis",
        ])

    def test_home_recipe_cards_are_fully_clickable_without_read_more_text(self):
        category = Category.objects.create(name="Desery", slug="desery-home")
        Recipe.objects.create(
            title="Domowy hummus",
            slug="domowy-hummus",
            category=category,
            description="Krotki opis przepisu",
            ingredients_text="ciecierzyca",
            steps_text="zmiksuj",
            prep_time=10,
        )

        response = self.client.get("/")

        self.assertContains(response, 'href="/przepisy/domowy-hummus/"')
        self.assertNotContains(response, "Czytaj więcej")


class TestBaseTemplate(TestCase):
    """FOUND-02: base.html renders with nav, footer."""

    def test_home_page_has_navbar(self):
        response = self.client.get("/")
        # Sketchbook nav uses lowercase handwritten labels
        self.assertContains(response, "przepiśnik")
        self.assertContains(response, "sklep")
        self.assertContains(response, "o nas")
        self.assertContains(response, "kontakt")

    def test_home_page_has_cart_link(self):
        response = self.client.get("/")
        self.assertContains(response, 'aria-label="Koszyk"')
        self.assertContains(response, "nav-cart")

    def test_home_page_has_footer(self):
        response = self.client.get("/")
        self.assertContains(response, "Kuchenna Komitywa")
        self.assertContains(response, "zrobione powoli, ręcznie")

    def test_home_page_has_skip_link(self):
        response = self.client.get("/")
        self.assertContains(response, "Przejdź do treści")


class TestResponsiveLayout(TestCase):
    """FOUND-03: Pages are responsive (custom CSS + viewport meta)."""

    def test_viewport_meta_tag(self):
        response = self.client.get("/")
        self.assertContains(response, "viewport")

    def test_static_css_included(self):
        response = self.client.get("/")
        self.assertRegex(
            response.content.decode(),
            r"/static/css/main(?:\.[0-9a-f]+)?\.css",
        )

    def test_brand_fonts_loaded(self):
        response = self.client.get("/")
        self.assertContains(response, "DM+Serif+Display")
        self.assertContains(response, "Caveat")


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
        self.assertContains(response, 'class="hero"')
        self.assertContains(response, "hero-grid")

    def test_hero_has_headline(self):
        response = self.client.get("/")
        # Sketchbook headline: "Wsp\u00f3lnie gotujemy z ro\u015blin"
        self.assertContains(response, "Wsp\u00f3lnie")
        self.assertContains(response, "gotujemy")
        self.assertContains(response, "ro\u015blin")

    def test_hero_has_cta_button(self):
        response = self.client.get("/")
        self.assertContains(response, "otw\u00f3rz szkicownik")
        self.assertContains(response, "btn-accent")

    def test_hero_has_polaroid_stack(self):
        response = self.client.get("/")
        self.assertContains(response, "hero-illus")
        self.assertContains(response, "polaroid")


class TestAboutTeaser(TestCase):
    """LAND-01: Sketchbook about teaser replaces feature cards."""

    def test_about_teaser_present(self):
        response = self.client.get("/")
        self.assertContains(response, "I. \u00b7 kto gotuje")
        self.assertContains(response, "cze\u015b\u0107, tu Tomasz")

    def test_belief_card_present(self):
        response = self.client.get("/")
        self.assertContains(response, "w co wierzymy")
        self.assertContains(response, "Sezonowo, lokalnie, powoli")


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
