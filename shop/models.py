from dataclasses import dataclass
from datetime import datetime, time as datetime_time, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from django.utils.text import slugify


@dataclass(frozen=True)
class PickupSlot:
    starts_at: datetime_time
    ends_at: datetime_time


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
        """Return the Rzut accepting orders at the given moment."""
        at = at or timezone.now()
        return (
            self.filter(
                status=OrderEdition.Status.PUBLISHED,
                opens_at__lte=at,
                closes_at__gt=at,
            )
            .order_by("-opens_at", "-created_at")
            .first()
        )

    def next_upcoming(self, at=None):
        at = at or timezone.now()
        return (
            self.filter(
                status=OrderEdition.Status.PUBLISHED,
                opens_at__gt=at,
            )
            .order_by("opens_at", "created_at")
            .first()
        )

    def archived(self, at=None):
        at = at or timezone.now()
        return (
            self.filter(show_in_archive=True)
            .filter(
                Q(status=OrderEdition.Status.CLOSED)
                | Q(
                    status=OrderEdition.Status.PUBLISHED,
                    closes_at__lte=at,
                )
            )
            .order_by("-closes_at", "-created_at")
        )


class OrderEdition(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Szkic"
        PUBLISHED = "published", "Opublikowany"
        PAUSED = "paused", "Wstrzymany"
        CLOSED = "closed", "Zamknięty"

    class Phase(models.TextChoices):
        UPCOMING = "upcoming", "Nadchodzący"
        OPEN = "open", "Otwarty"
        ENDED = "ended", "Zakończony"

    STATUS_CHOICES = Status.choices

    title = models.CharField(max_length=200, verbose_name="Nazwa Rzutu")
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
        verbose_name="Początek sprzedaży",
    )
    closes_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Koniec sprzedaży",
    )
    pickup_details = models.TextField(
        blank=True,
        verbose_name="Termin i miejsce odbioru",
    )
    pickup_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Dzień odbioru",
    )
    pickup_place_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="Nazwa miejsca odbioru",
    )
    pickup_address = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Adres odbioru",
    )
    pickup_starts_at = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Początek odbioru",
    )
    pickup_ends_at = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Koniec odbioru",
    )
    pickup_instructions = models.TextField(
        blank=True,
        default="",
        verbose_name="Instrukcja odbioru",
    )
    payment_details = models.TextField(
        blank=True,
        verbose_name="Informacje o płatności",
    )
    show_in_archive = models.BooleanField(
        default=True,
        verbose_name="Pokaż w archiwum",
    )
    show_upcoming_menu = models.BooleanField(
        default=True,
        verbose_name="Pokaż menu przed otwarciem sprzedaży",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = OrderEditionQuerySet.as_manager()

    class Meta:
        verbose_name = "Rzut"
        verbose_name_plural = "Rzuty"
        ordering = ["-opens_at", "-created_at"]

    def __str__(self):
        return self.title

    def phase_at(self, at=None):
        at = at or timezone.now()
        if self.status == self.Status.CLOSED:
            return self.Phase.ENDED
        if (
            self.status != self.Status.PUBLISHED
            or self.opens_at is None
            or self.closes_at is None
        ):
            return None
        if at < self.opens_at:
            return self.Phase.UPCOMING
        if at >= self.closes_at:
            return self.Phase.ENDED
        return self.Phase.OPEN

    def pickup_slots(self):
        if not all([
            self.pickup_date,
            self.pickup_starts_at,
            self.pickup_ends_at,
        ]):
            return []

        cursor = datetime.combine(
            self.pickup_date,
            self.pickup_starts_at,
        )
        pickup_end = datetime.combine(
            self.pickup_date,
            self.pickup_ends_at,
        )
        slots = []
        while cursor < pickup_end:
            slot_end = min(cursor + timedelta(hours=1), pickup_end)
            slots.append(PickupSlot(cursor.time(), slot_end.time()))
            cursor = slot_end
        return slots

    def is_public_at(self, at=None):
        phase = self.phase_at(at)
        if phase == self.Phase.OPEN:
            return True
        if phase == self.Phase.UPCOMING:
            return self.show_upcoming_menu
        if phase == self.Phase.ENDED:
            return self.show_in_archive
        return False

    def clean(self):
        super().clean()
        errors = {}
        if (
            self.opens_at
            and self.closes_at
            and self.closes_at <= self.opens_at
        ):
            errors["closes_at"] = (
                "Koniec sprzedaży musi przypadać po jej rozpoczęciu."
            )
        if (
            self.pickup_starts_at
            and self.pickup_ends_at
            and self.pickup_ends_at <= self.pickup_starts_at
        ):
            errors["pickup_ends_at"] = (
                "Koniec odbioru musi przypadać po jego rozpoczęciu."
            )
        if (
            self.closes_at
            and self.pickup_date
            and self.pickup_starts_at
        ):
            pickup_starts = datetime.combine(
                self.pickup_date,
                self.pickup_starts_at,
            )
            if timezone.is_aware(self.closes_at):
                pickup_starts = timezone.make_aware(
                    pickup_starts,
                    timezone.get_current_timezone(),
                )
            if self.closes_at >= pickup_starts:
                errors["closes_at"] = (
                    "Sprzedaż musi zakończyć się przed rozpoczęciem odbioru."
                )
        if self.status == self.Status.PUBLISHED:
            publication_errors = self.publication_errors()
            if publication_errors:
                errors["status"] = publication_errors
            if self.opens_at and self.closes_at:
                overlapping_rzut = (
                    type(self).objects.filter(
                        status=self.Status.PUBLISHED,
                        opens_at__lt=self.closes_at,
                        closes_at__gt=self.opens_at,
                    )
                    .exclude(pk=self.pk)
                    .order_by("opens_at")
                    .first()
                )
                if overlapping_rzut:
                    errors["opens_at"] = [
                        "Okno sprzedaży nakłada się na opublikowany "
                        f"Rzut „{overlapping_rzut.title}”."
                    ]

        if errors:
            raise ValidationError(errors)

    def publication_errors(self):
        errors = []
        required_values = [
            (self.description, "Uzupełnij opis Rzutu."),
            (self.opens_at, "Ustaw początek sprzedaży."),
            (self.closes_at, "Ustaw koniec sprzedaży."),
            (self.pickup_date, "Ustaw dzień odbioru."),
            (
                self.pickup_place_name,
                "Uzupełnij nazwę miejsca odbioru.",
            ),
            (self.pickup_address, "Uzupełnij adres odbioru."),
            (
                self.pickup_starts_at and self.pickup_ends_at,
                "Ustaw godziny odbioru.",
            ),
            (
                self.pickup_instructions,
                "Uzupełnij instrukcję odbioru.",
            ),
        ]
        for value, message in required_values:
            if not value:
                errors.append(message)

        active_items = (
            self.items.filter(
                is_active=True,
                product__type="physical",
            ).select_related("product")
            if self.pk
            else RzutItem.objects.none()
        )
        if not active_items.exists():
            errors.append("Dodaj co najmniej jedną aktywną Pozycję Rzutu.")
            return errors

        for item in active_items:
            errors.extend(item.publication_errors())

        return errors

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "rzut"
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


class ProductQuerySet(models.QuerySet):
    def available_in_shop(self):
        return self.filter(
            is_available_in_shop=True,
            is_archived=False,
        )


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
        max_digits=8,
        decimal_places=2,
        verbose_name="Cena domyślna",
        help_text="Domyślna cena w PLN, kopiowana do nowej Pozycji Rzutu",
    )
    default_portion = models.CharField(
        max_length=120,
        blank=True,
        default="",
        verbose_name="Domyślna porcja",
        help_text='Np. "bochenek ok. 750 g" albo "pudełko 6 szt."',
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
    is_available_in_shop = models.BooleanField(
        default=True,
        verbose_name="Dostępny w sklepie",
    )
    is_archived = models.BooleanField(
        default=False,
        verbose_name="Zarchiwizowany",
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Kolejność",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductQuerySet.as_manager()

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


class RzutItemQuerySet(models.QuerySet):
    def public_menu(self):
        return self.filter(
            is_active=True,
            product__type="physical",
        ).select_related("product", "product__category")


class RzutItem(models.Model):
    rzut = models.ForeignKey(
        OrderEdition,
        on_delete=models.PROTECT,
        related_name="items",
        verbose_name="Rzut",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="rzut_items",
        verbose_name="Produkt",
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Cena",
    )
    portion = models.CharField(
        max_length=120,
        verbose_name="Porcja",
        help_text='Np. "bochenek ok. 750 g" albo "pudełko 6 szt."',
    )
    pool = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Pula",
    )
    per_customer_limit = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        verbose_name="Limit Klienta",
        help_text="Pozostaw puste, aby nie nakładać dodatkowego limitu.",
    )
    allocated_quantity = models.PositiveIntegerField(
        default=0,
        editable=False,
        verbose_name="Przydzielona ilość",
        help_text=(
            "Łączna ilość zablokowana przez aktywne Rezerwacje i "
            "potwierdzone Zamówienia Rzutu."
        ),
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Kolejność",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktywna",
    )
    production_note = models.TextField(
        blank=True,
        default="",
        verbose_name="Notatka produkcyjna",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = RzutItemQuerySet.as_manager()

    class Meta:
        verbose_name = "Pozycja Rzutu"
        verbose_name_plural = "Pozycje Rzutu"
        ordering = ["sort_order", "product__title"]
        constraints = [
            models.UniqueConstraint(
                fields=["rzut", "product"],
                name="unique_product_per_rzut",
            ),
            models.CheckConstraint(
                condition=Q(price__gte=0),
                name="rzut_item_price_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(pool__gte=1),
                name="rzut_item_pool_positive",
            ),
            models.CheckConstraint(
                condition=(
                    Q(per_customer_limit__isnull=True)
                    | Q(per_customer_limit__gte=1)
                ),
                name="rzut_item_customer_limit_positive",
            ),
            models.CheckConstraint(
                condition=Q(allocated_quantity__lte=F("pool")),
                name="rzut_item_allocation_within_pool",
            ),
        ]

    def __str__(self):
        return f"{self.rzut}: {self.product}"

    def clean(self):
        super().clean()
        if (
            self.pool is not None
            and self.allocated_quantity is not None
            and self.allocated_quantity > self.pool
        ):
            raise ValidationError({
                "pool": (
                    "Pula nie może być mniejsza niż "
                    f"{self.allocated_quantity} już przydzielonych sztuk."
                )
            })

    def publication_errors(self):
        item_label = f"Pozycja „{self.product.title or 'bez nazwy'}”"
        required_values = [
            (
                self.product.title,
                f"{item_label}: uzupełnij nazwę Produktu.",
            ),
            (
                self.product.description,
                f"{item_label}: uzupełnij krótki opis Produktu.",
            ),
            (
                self.product.ingredients,
                f"{item_label}: uzupełnij skład Produktu.",
            ),
            (
                self.product.allergens,
                f"{item_label}: uzupełnij alergeny Produktu.",
            ),
            (self.portion, f"{item_label}: uzupełnij Porcję."),
            (self.pool and self.pool > 0, f"{item_label}: ustaw Pulę."),
            (self.price is not None, f"{item_label}: ustaw cenę."),
        ]
        return [message for value, message in required_values if not value]

    @property
    def available_quantity(self):
        return self.pool - self.allocated_quantity

    def is_offered_at(self, at=None):
        return (
            self.is_active
            and self.product.type == "physical"
            and self.rzut.phase_at(at) == OrderEdition.Phase.OPEN
        )

    def can_add_to_cart_at(self, at=None):
        return self.is_offered_at(at) and not self.is_sold_out

    @property
    def is_sold_out(self):
        return self.available_quantity <= 0

    @property
    def show_exact_availability(self):
        available = self.available_quantity
        return available <= 3 or available * 5 <= self.pool

    @property
    def availability_message(self):
        available = self.available_quantity
        if available == 1:
            return "Została 1 sztuka"
        if 2 <= available <= 4:
            return f"Zostały {available} sztuki"
        return f"Zostało {available} sztuk"


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
