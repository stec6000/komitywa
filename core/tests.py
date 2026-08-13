from pathlib import Path
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.conf import settings
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.forms import CafeInquiryForm, WorkshopInterestForm
from core.models import CafeInquiry, CafeLocation, WorkshopInterest
from recipes.models import Category, Recipe
from shop.models import OrderEdition, Product, ProductCategory, RzutItem


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
        """The mixed kitchen feed shows the three newest public recipes."""
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

        # The new "Z kuchni" feed is deliberately limited to three entries.
        self.assertContains(response, "Najnowszy przepis")
        self.assertContains(response, "Srodkowy przepis")
        self.assertContains(response, "Trzeci przepis")
        self.assertNotContains(response, "Czwarty przepis")
        self.assertNotContains(response, "Najstarszy przepis")
        self.assertNotContains(response, "Ukryty przepis")
        feed_titles = [item["title"] for item in response.context["kitchen_items"]]
        self.assertEqual(
            feed_titles,
            ["Najnowszy przepis", "Srodkowy przepis", "Trzeci przepis"],
        )

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


class TestOrdersView(TestCase):
    def setUp(self):
        self.category = ProductCategory.objects.create(
            name="Wypieki",
            slug="wypieki-zamowienia",
        )

    def test_empty_state_is_explicit_when_no_rzut_is_open(self):
        response = self.client.get(reverse("orders"))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["current_rzut"])
        self.assertContains(response, "W pracowni szykuje się kolejny rzut")
        self.assertContains(response, "Obecnie nie prowadzimy zapisów")

    def test_open_rzut_shows_only_active_physical_items(self):
        now = timezone.now()
        rzut = OrderEdition.objects.create(
            title="Sierpniowy stół",
            description="Mała sierpniowa seria.",
            status=OrderEdition.Status.PUBLISHED,
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(days=2),
            pickup_date=timezone.localdate() + timedelta(days=3),
            pickup_place_name="Kuchenna Komitywa",
            pickup_address="ul. Bukowa 14, Białystok",
            pickup_starts_at="10:00",
            pickup_ends_at="13:00",
            pickup_instructions="Odbiór w sobotę.",
            payment_details="Płatność online.",
        )
        visible_product = Product.objects.create(
            title="Drożdżówka ze śliwką",
            slug="drozdzowka-ze-sliwka",
            category=self.category,
            type="physical",
            description="Miękka drożdżówka z owocami.",
            ingredients="mąka, śliwki",
            allergens="gluten",
            price=Decimal("16.00"),
        )
        visible = RzutItem.objects.create(
            rzut=rzut,
            product=visible_product,
            price=Decimal("16.00"),
            portion="1 sztuka",
            pool=10,
        )
        inactive_product = Product.objects.create(
            title="Nieaktywny chleb",
            slug="nieaktywny-chleb",
            category=self.category,
            type="physical",
            description="Nie powinien być widoczny.",
            price=Decimal("20.00"),
        )
        RzutItem.objects.create(
            rzut=rzut,
            product=inactive_product,
            price=Decimal("20.00"),
            portion="1 sztuka",
            pool=10,
            is_active=False,
        )
        ebook = Product.objects.create(
            title="Ebook z tego Rzutu",
            slug="ebook-z-tego-rzutu",
            category=self.category,
            type="ebook",
            description="Produkt cyfrowy pozostaje w starym sklepie.",
            price=Decimal("29.00"),
        )
        RzutItem.objects.create(
            rzut=rzut,
            product=ebook,
            price=Decimal("29.00"),
            portion="1 plik",
            pool=10,
        )

        response = self.client.get(reverse("orders"))

        self.assertEqual(response.context["current_rzut"], rzut)
        self.assertEqual(list(response.context["current_items"]), [visible])
        self.assertContains(response, "Sierpniowy stół")
        self.assertContains(response, "Drożdżówka ze śliwką")
        self.assertContains(response, "mąka, śliwki")
        self.assertContains(response, "gluten")
        self.assertContains(response, "Odbiór w sobotę")
        self.assertNotContains(response, "Nieaktywny chleb")
        self.assertNotContains(response, "Ebook z tego Rzutu")

    def test_archive_shows_only_closed_editions_marked_for_archive(self):
        visible = OrderEdition.objects.create(
            title="Wielkanocny stół",
            status=OrderEdition.Status.CLOSED,
            closes_at=timezone.now() - timedelta(days=10),
            show_in_archive=True,
        )
        OrderEdition.objects.create(
            title="Wewnętrzna próba",
            status=OrderEdition.Status.CLOSED,
            closes_at=timezone.now() - timedelta(days=5),
            show_in_archive=False,
        )

        response = self.client.get(reverse("orders"))

        self.assertEqual(list(response.context["archived_rzuty"]), [visible])
        self.assertContains(response, "Wielkanocny stół")
        self.assertNotContains(response, "Wewnętrzna próba")


class TestBaseTemplate(TestCase):
    """FOUND-02: base.html renders with nav, footer."""

    def test_home_page_has_navbar(self):
        response = self.client.get("/")
        expected_links = {
            reverse("orders"): "Zamówienia",
            reverse("for_cafes"): "Dla kawiarni",
            reverse("recipes:list"): "Przepisy",
            reverse("content:blog_list"): "Z kuchni",
            reverse("workshops"): "Wspólne gotowanie",
            reverse("about"): "O Komitywie",
            reverse("contact"): "Kontakt",
        }
        for url, label in expected_links.items():
            with self.subTest(label=label):
                self.assertContains(response, f'href="{url}"')
                self.assertContains(response, label)

    def test_home_page_has_cart_link(self):
        response = self.client.get("/")
        self.assertContains(
            response,
            'aria-label="Koszyk, liczba produktów: 0"',
        )
        self.assertContains(response, "nav-cart")

    def test_home_page_has_footer(self):
        response = self.client.get("/")
        self.assertContains(response, "Kuchenna Komitywa")
        self.assertContains(response, "sezonowo, rzemieślniczo")

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
        self.assertContains(response, 'class="kk-home-hero"')
        self.assertContains(response, "kk-home-hero__grid")

    def test_hero_has_headline(self):
        response = self.client.get("/")
        self.assertContains(
            response,
            "Roślinna pracownia wypieków i dobrego jedzenia",
        )

    def test_hero_has_cta_button(self):
        response = self.client.get("/")
        self.assertContains(response, "Dowiedz się o kolejnym rzucie")
        self.assertContains(response, "Współpraca dla kawiarni")
        self.assertContains(response, "btn-accent")

    def test_hero_has_real_photo_with_meaningful_alt(self):
        response = self.client.get("/")
        self.assertContains(response, "kk-home-hero__photo")
        self.assertContains(
            response,
            'alt="Tomasz siedzący przy stoliku przed kawiarnią z wypiekiem"',
        )


class TestHomeOfferSections(TestCase):
    """LAND-01: Home explains the four real areas of the workshop."""

    def test_four_offer_areas_are_present(self):
        response = self.client.get("/")
        self.assertContains(response, "Wypieki dla kawiarni")
        self.assertContains(response, "Limitowane zamówienia")
        self.assertContains(response, "Cateringi świąteczne")
        self.assertContains(response, "Wspólne gotowanie")

    def test_closed_orders_state_does_not_invent_an_offer(self):
        response = self.client.get("/")
        self.assertContains(response, "W kuchni właśnie szykuje się kolejny Rzut")
        self.assertContains(response, "Listy z Komitywy")


class TestAboutPage(TestCase):
    """LAND-02: O nas page accessible with company story."""

    def test_about_page_returns_200(self):
        response = self.client.get("/o-nas/")
        self.assertEqual(response.status_code, 200)

    def test_about_page_has_heading(self):
        response = self.client.get("/o-nas/")
        html = response.content.decode()
        self.assertRegex(html, r"<h1[^>]*>\s*O Komitywie\s*</h1>")

    def test_about_page_has_content(self):
        response = self.client.get("/o-nas/")
        self.assertContains(
            response,
            "Kuchenna Komitywa to niewielka roślinna pracownia",
        )
        self.assertContains(response, "Nie zamykamy się w jednej tradycji kulinarnej")


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


class TestCafeLocation(TestCase):
    def test_locations_are_ordered_for_display(self):
        second = CafeLocation.objects.create(
            name="Druga Kawiarnia",
            address="Białystok",
            products_note="Drożdżówki",
            sort_order=20,
        )
        first = CafeLocation.objects.create(
            name="Pierwsza Kawiarnia",
            address="Białystok",
            products_note="Shokupan",
            sort_order=10,
        )

        self.assertEqual(list(CafeLocation.objects.all()), [first, second])

    def test_home_context_contains_only_active_locations(self):
        visible = CafeLocation.objects.create(
            name="Widoczny lokal",
            address="Białystok",
            products_note="Ciastka",
        )
        CafeLocation.objects.create(
            name="Ukryty lokal",
            address="Białystok",
            products_note="Ciastka",
            is_active=False,
        )

        response = self.client.get(reverse("home"))

        self.assertEqual(list(response.context["cafe_locations"]), [visible])
        self.assertContains(response, "Gdzie zjeść Komitywę")
        self.assertContains(response, "Widoczny lokal")
        self.assertNotContains(response, "Ukryty lokal")

    def test_home_hides_locations_section_until_real_data_exists(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(list(response.context["cafe_locations"]), [])
        self.assertNotContains(response, "Gdzie zjeść Komitywę")


class TestCafeInquiryForm(TestCase):
    def valid_data(self):
        return {
            "venue_name": "Kawiarnia Próba",
            "contact_name": "Anna",
            "email": "anna@example.com",
            "phone": "",
            "city": "Białystok",
            "interested_products": ["shokupan", "cookies"],
            "frequency": "weekly",
            "message": "Chcemy przetestować wypieki.",
            "privacy_consent": "on",
            "website": "",
        }

    def test_selected_products_are_saved_as_readable_text(self):
        form = CafeInquiryForm(data=self.valid_data())

        self.assertTrue(form.is_valid(), form.errors)
        inquiry = form.save()

        self.assertEqual(inquiry.interested_products, "Shokupan, Ciastka")
        self.assertEqual(inquiry.status, "new")
        self.assertEqual(inquiry.phone, "")

    def test_honeypot_rejects_submission(self):
        data = self.valid_data()
        data["website"] = "https://spam.example"

        form = CafeInquiryForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("website", form.errors)

    def test_privacy_consent_is_required(self):
        data = self.valid_data()
        data.pop("privacy_consent")

        form = CafeInquiryForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("privacy_consent", form.errors)

    def test_invalid_field_is_described_for_assistive_technology(self):
        data = self.valid_data()
        data["email"] = "niepoprawny"
        form = CafeInquiryForm(data=data)

        self.assertFalse(form.is_valid())
        attrs = form.fields["email"].widget.attrs
        self.assertEqual(attrs["aria-invalid"], "true")
        self.assertIn("id_email-error", attrs["aria-describedby"])


class TestWorkshopInterestForm(TestCase):
    def valid_data(self):
        return {
            "name": "Ola",
            "email": "ola@example.com",
            "topic": "fermentation",
            "preferred_timing": "weekend",
            "consent_contact": "on",
            "website": "",
        }

    def test_valid_interest_is_saved(self):
        form = WorkshopInterestForm(data=self.valid_data())

        self.assertTrue(form.is_valid(), form.errors)
        interest = form.save()

        self.assertEqual(interest.get_topic_display(), "Kiszenie i fermentacja")
        self.assertEqual(interest.get_preferred_timing_display(), "Weekend")

    def test_honeypot_rejects_submission(self):
        data = self.valid_data()
        data["website"] = "spam"

        form = WorkshopInterestForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("website", form.errors)


class TestInquiryViews(TestCase):
    cafe_data = {
        "venue_name": "Kawiarnia Próba",
        "contact_name": "Anna",
        "email": "anna@example.com",
        "phone": "123 456 789",
        "city": "Białystok",
        "interested_products": ["buns", "seasonal_bakes"],
        "frequency": "occasionally",
        "message": "Prosimy o kontakt.",
        "privacy_consent": "on",
        "website": "",
    }
    workshop_data = {
        "name": "Ola",
        "email": "ola@example.com",
        "topic": "seasonal_table",
        "preferred_timing": "weekday_evening",
        "consent_contact": "on",
        "website": "",
    }

    @patch("core.views.send_mail")
    def test_cafe_inquiry_is_saved_and_notification_is_attempted(self, send_mail):
        response = self.client.post(reverse("for_cafes"), self.cafe_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("for_cafes"))
        self.assertEqual(CafeInquiry.objects.count(), 1)
        send_mail.assert_called_once()
        self.assertEqual(send_mail.call_args.args[3], [settings.CONTACT_EMAIL])
        self.assertTrue(list(get_messages(response.wsgi_request)))

    @patch("core.views.send_mail", side_effect=RuntimeError("SMTP unavailable"))
    def test_email_failure_does_not_lose_cafe_inquiry(self, send_mail):
        with self.assertLogs("core.views", level="ERROR"):
            response = self.client.post(reverse("for_cafes"), self.cafe_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(CafeInquiry.objects.count(), 1)
        send_mail.assert_called_once()

    @patch("core.views.send_mail")
    def test_workshop_interest_is_saved_and_notification_is_attempted(
        self,
        send_mail,
    ):
        response = self.client.post(reverse("workshops"), self.workshop_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("workshops"))
        self.assertEqual(WorkshopInterest.objects.count(), 1)
        send_mail.assert_called_once()
        self.assertEqual(send_mail.call_args.args[3], [settings.CONTACT_EMAIL])
        self.assertTrue(list(get_messages(response.wsgi_request)))

    def test_bot_submission_is_not_saved(self):
        data = {**self.workshop_data, "website": "https://spam.example"}

        response = self.client.post(reverse("workshops"), data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(WorkshopInterest.objects.count(), 0)
        self.assertIn("website", response.context["form"].errors)

    def test_invalid_workshop_form_links_error_to_field(self):
        data = {**self.workshop_data, "email": "niepoprawny"}

        response = self.client.post(reverse("workshops"), data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'aria-describedby="id_email-error"')
        self.assertContains(response, 'aria-invalid="true"')
        self.assertContains(response, 'id="id_email-error"')
        self.assertContains(response, 'data-focus-on-load')
