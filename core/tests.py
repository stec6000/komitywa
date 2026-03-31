from pathlib import Path

from django.conf import settings
from django.test import TestCase


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
        self.assertContains(response, "main.css")


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
        self.assertContains(response, "cookie_consent.js")
