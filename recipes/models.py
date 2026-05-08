from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Kategoria"
        verbose_name_plural = "Kategorie"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tagi"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recipes",
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="recipes",
    )
    description = models.TextField(
        help_text="Krotki opis (1-2 zdania) - wyswietlany na karcie"
    )
    ingredients_text = models.TextField(
        help_text="Skladniki - kazdy w nowej linii"
    )
    steps_text = models.TextField(
        help_text="Kroki przygotowania - kazdy w nowej linii"
    )
    prep_time = models.PositiveSmallIntegerField(
        help_text="Czas przygotowania w minutach"
    )
    servings = models.PositiveSmallIntegerField(
        default=1,
        help_text="Liczba porcji",
    )
    difficulty = models.CharField(
        max_length=10,
        choices=[
            ("latwy", "latwy"),
            ("sredni", "sredni"),
            ("trudny", "trudny"),
        ],
        default="latwy",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Opcjonalne notatki autora",
    )
    image = models.ImageField(
        upload_to="recipes/",
        blank=True,
        null=True,
        help_text="Zdjecie przepisu",
    )
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Przepis"
        verbose_name_plural = "Przepisy"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
