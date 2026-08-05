from django.db import models


class CafeLocation(models.Model):
    """A cafe or venue where customers can find Komitywa products."""

    name = models.CharField("nazwa", max_length=200)
    address = models.CharField("adres", max_length=255)
    url = models.URLField("strona lub media społecznościowe", blank=True)
    products_note = models.TextField(
        "informacja o produktach",
        help_text="Orientacyjnie opisz, jakie produkty są dostępne w lokalu.",
    )
    sort_order = models.PositiveIntegerField("kolejność", default=0)
    is_active = models.BooleanField("widoczne", default=True)
    created_at = models.DateTimeField("utworzono", auto_now_add=True)
    updated_at = models.DateTimeField("zaktualizowano", auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "lokal z produktami Komitywy"
        verbose_name_plural = "lokale z produktami Komitywy"

    def __str__(self):
        return self.name


class CafeInquiry(models.Model):
    FREQUENCY_CHOICES = [
        ("weekly", "Co tydzień"),
        ("biweekly", "Co dwa tygodnie"),
        ("monthly", "Raz w miesiącu"),
        ("occasionally", "Okazjonalnie"),
        ("one_off", "Jednorazowo"),
    ]
    STATUS_CHOICES = [
        ("new", "Nowe"),
        ("contacted", "Skontaktowano się"),
        ("closed", "Zamknięte"),
    ]

    venue_name = models.CharField("nazwa lokalu", max_length=200)
    contact_name = models.CharField("imię osoby kontaktowej", max_length=150)
    email = models.EmailField("e-mail")
    phone = models.CharField("telefon", max_length=40, blank=True)
    city = models.CharField("miasto", max_length=120)
    interested_products = models.TextField("interesujące produkty")
    frequency = models.CharField(
        "przewidywana częstotliwość zamówień",
        max_length=20,
        choices=FREQUENCY_CHOICES,
    )
    message = models.TextField("wiadomość")
    privacy_consent = models.BooleanField(
        "zgoda na przetwarzanie danych",
        default=False,
    )
    status = models.CharField(
        "status",
        max_length=20,
        choices=STATUS_CHOICES,
        default="new",
    )
    created_at = models.DateTimeField("utworzono", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "zapytanie od kawiarni"
        verbose_name_plural = "zapytania od kawiarni"

    def __str__(self):
        return f"{self.venue_name} — {self.contact_name}"


class WorkshopInterest(models.Model):
    TOPIC_CHOICES = [
        ("plant_based_buns", "Roślinne drożdżówki"),
        ("shared_dumpling_making", "Wspólne lepienie"),
        ("fermentation", "Kiszenie i fermentacja"),
        ("seasonal_table", "Sezonowy stół"),
        ("holiday_cooking", "Świąteczne gotowanie"),
    ]
    PREFERRED_TIMING_CHOICES = [
        ("weekday_evening", "Dzień roboczy wieczorem"),
        ("weekend", "Weekend"),
    ]

    name = models.CharField("imię", max_length=150)
    email = models.EmailField("e-mail")
    topic = models.CharField(
        "interesujący temat",
        max_length=40,
        choices=TOPIC_CHOICES,
    )
    preferred_timing = models.CharField(
        "preferowany termin",
        max_length=20,
        choices=PREFERRED_TIMING_CHOICES,
    )
    consent_contact = models.BooleanField("zgoda na kontakt", default=False)
    created_at = models.DateTimeField("utworzono", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "zainteresowanie warsztatami"
        verbose_name_plural = "zainteresowania warsztatami"

    def __str__(self):
        return f"{self.name} — {self.get_topic_display()}"
