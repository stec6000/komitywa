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
