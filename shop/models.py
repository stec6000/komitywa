from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify


class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Kategoria produktu"
        verbose_name_plural = "Kategorie produktów"
        ordering = ["name"]

    def __str__(self):
        return self.name


class OrderEditionQuerySet(models.QuerySet):
    def current(self, at=None):
        """Return the edition accepting orders at the given moment."""
        at = at or timezone.now()
        return (
            self.filter(status="open")
            .filter(Q(opens_at__isnull=True) | Q(opens_at__lte=at))
            .filter(Q(closes_at__isnull=True) | Q(closes_at__gt=at))
            .order_by("-opens_at", "-created_at")
            .first()
        )


class OrderEdition(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Szkic"
        UPCOMING = "upcoming", "Nadchodząca"
        OPEN = "open", "Otwarta"
        CLOSED = "closed", "Zamknięta"

    STATUS_CHOICES = Status.choices

    title = models.CharField(max_length=200, verbose_name="Nazwa edycji")
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name="Opis")
    image = models.ImageField(
        upload_to="order-editions/",
        blank=True,
        null=True,
        verbose_name="Zdjęcie",
    )
    image_alt = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Tekst alternatywny zdjęcia",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Status",
    )
    opens_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Początek zamówień",
    )
    closes_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Koniec zamówień",
    )
    pickup_details = models.TextField(
        blank=True,
        verbose_name="Termin i miejsce odbioru",
    )
    payment_details = models.TextField(
        blank=True,
        verbose_name="Informacje o płatności",
    )
    show_in_archive = models.BooleanField(
        default=True,
        verbose_name="Pokaż w archiwum",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = OrderEditionQuerySet.as_manager()

    class Meta:
        verbose_name = "Edycja zamówień"
        verbose_name_plural = "Edycje zamówień"
        ordering = ["-opens_at", "-created_at"]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if (
            self.opens_at
            and self.closes_at
            and self.closes_at <= self.opens_at
        ):
            raise ValidationError({
                "closes_at": (
                    "Koniec zamówień musi przypadać po ich rozpoczęciu."
                )
            })

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "edycja"
            candidate = base_slug[:200]
            suffix = 2
            editions = type(self).objects.exclude(pk=self.pk)
            while editions.filter(slug=candidate).exists():
                suffix_text = f"-{suffix}"
                candidate = f"{base_slug[:200 - len(suffix_text)]}{suffix_text}"
                suffix += 1
            self.slug = candidate

            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {"slug"}

        super().save(*args, **kwargs)


class Product(models.Model):
    TYPE_CHOICES = [
        ("ebook", "Ebook"),
        ("physical", "Produkt fizyczny"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    edition = models.ForeignKey(
        OrderEdition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="Edycja zamówień",
    )
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    type = models.CharField(
        max_length=10, choices=TYPE_CHOICES, default="physical"
    )
    description = models.TextField(
        help_text="Krótki opis (1-2 zdania) - wyświetlany na karcie"
    )
    full_description = models.TextField(
        blank=True,
        help_text="Pełny opis - wyświetlany na stronie produktu",
    )
    ingredients = models.TextField(
        blank=True,
        default="",
        verbose_name="Składniki",
    )
    allergens = models.TextField(
        blank=True,
        default="",
        verbose_name="Alergeny",
    )
    price = models.DecimalField(
        max_digits=8, decimal_places=2, help_text="Cena w PLN"
    )
    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True,
        help_text="Zdjęcie produktu",
    )
    ebook_file = models.FileField(
        upload_to="ebooks/",
        blank=True,
        null=True,
        help_text="Plik PDF ebooka (tylko dla produktów typu ebook)",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Kolejność",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produkt"
        verbose_name_plural = "Produkty"
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Oczekujące na płatność"),
        ("paid", "Opłacone"),
        ("completed", "Zrealizowane"),
        ("cancelled", "Anulowane"),
    ]

    email = models.EmailField()
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    pickup_date = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    total = models.DecimalField(max_digits=10, decimal_places=2)
    cart_snapshot = models.JSONField(
        help_text="Kopia koszyka w momencie zamówienia"
    )
    p24_session_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Identyfikator sesji Przelewy24",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Zamówienie"
        verbose_name_plural = "Zamówienia"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Zamówienie #{self.id} - {self.email}"
