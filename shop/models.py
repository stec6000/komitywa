from django.db import models
from django.utils.text import slugify


class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Kategoria produktu"
        verbose_name_plural = "Kategorie produktow"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    TYPE_CHOICES = [
        ("ebook", "Ebook"),
        ("physical", "Produkt fizyczny"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
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
        help_text="Krotki opis (1-2 zdania) -- wyswietlany na karcie"
    )
    full_description = models.TextField(
        blank=True,
        help_text="Pelny opis -- wyswietlany na stronie produktu",
    )
    price = models.DecimalField(
        max_digits=8, decimal_places=2, help_text="Cena w PLN"
    )
    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True,
        help_text="Zdjecie produktu",
    )
    ebook_file = models.FileField(
        upload_to="ebooks/",
        blank=True,
        null=True,
        help_text="Plik PDF ebooka (tylko dla produktow typu ebook)",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produkt"
        verbose_name_plural = "Produkty"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Oczekujace na platnosc"),
        ("paid", "Oplacone"),
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
        help_text="Kopia koszyka w momencie zamowienia"
    )
    p24_session_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Identyfikator sesji Przelewy24",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Zamowienie"
        verbose_name_plural = "Zamowienia"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Zamowienie #{self.id} - {self.email}"
