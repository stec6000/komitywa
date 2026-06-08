import markdown as md
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.text import slugify


class WeeklyResearch(models.Model):
    STATUS_CHOICES = [
        ("pending", "pending"),
        ("research_done", "research_done"),
        ("formatted", "formatted"),
        ("failed", "failed"),
    ]

    week_label = models.CharField(
        max_length=16,
        unique=True,
        db_index=True,
        help_text="Format ISO YYYY-Www, np. 2026-W23",
    )
    date_from = models.DateField()
    date_to = models.DateField()
    raw_research = models.TextField(blank=True, default="")
    formatted_json = models.JSONField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Weekly research"
        verbose_name_plural = "Weekly researches"
        ordering = ["-date_to"]

    def __str__(self):
        return f"{self.week_label} ({self.status})"


class BlogPostManager(models.Manager):
    def published(self):
        return self.filter(
            status="published",
            published_at__lte=timezone.now(),
        )


class BlogPost(models.Model):
    STATUS_CHOICES = [
        ("draft", "draft"),
        ("published", "published"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    excerpt = models.TextField(
        blank=True,
        default="",
        help_text="Krótki lead 1-2 zdania (max 300 znaków).",
    )
    body = models.TextField(
        help_text="Markdown. Wspierane rozszerzenia: extra, smarty.",
    )
    tags = models.CharField(
        max_length=300,
        blank=True,
        default="",
        help_text="Tagi rozdzielone przecinkami, np. 'wegan, brownie, sezon'.",
    )
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default="draft",
        db_index=True,
    )
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    source_research = models.ForeignKey(
        WeeklyResearch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blog_posts",
        help_text="Źródłowy WeeklyResearch, jeśli post powstał z 'Promuj do BlogPost'.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = BlogPostManager()

    class Meta:
        verbose_name = "Blog post"
        verbose_name_plural = "Blog posts"
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "-published_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.status})"

    def save(self, *args, **kwargs):
        # Auto-slug TYLKO jeśli pusty (user może sam wpisać własny w admin)
        if not self.slug and self.title:
            base = slugify(self.title)[:200] or "post"
            slug = base
            i = 2
            qs = BlogPost.objects.filter(slug=slug).exclude(pk=self.pk)
            while qs.exists():
                slug = f"{base}-{i}"
                i += 1
                qs = BlogPost.objects.filter(slug=slug).exclude(pk=self.pk)
            self.slug = slug
        # Auto-published_at TYLKO jeśli status='published' i published_at jest None
        # (nigdy nie nadpisuje historii — gdy user cofa do draft a potem publikuje
        #  ponownie, zachowujemy pierwotną datę publikacji.)
        if self.status == "published" and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("content:blog_detail", args=[self.slug])

    @property
    def tags_list(self):
        return [t.strip() for t in (self.tags or "").split(",") if t.strip()]

    @property
    def body_html(self):
        html = md.markdown(self.body or "", extensions=["extra", "smarty"])
        return mark_safe(html)


class StorySlide(models.Model):
    research = models.ForeignKey(
        WeeklyResearch,
        on_delete=models.CASCADE,
        related_name="story_slides",
    )
    order = models.PositiveIntegerField(
        help_text="Kolejnosc slajdu (1-based).",
    )
    slide_type = models.CharField(
        max_length=20,
        help_text="hook/fact/tip/cta",
    )
    headline = models.CharField(
        max_length=90,
        help_text="Twardy bezpiecznik DB; cel redakcyjny <=55 znakow.",
    )
    subtext = models.TextField(blank=True, default="")
    bg_color = models.CharField(
        max_length=9,
        default="#f3ead7",
        help_text="Hex, fallback gdy brak zdjecia.",
    )
    visual_hint = models.TextField(
        blank=True,
        default="",
        help_text="Opis kadru -> zasila AI-prompt.",
    )
    background_image = models.ImageField(
        upload_to="weekly_research/story_uploads/%Y/%m/",
        blank=True,
        null=True,
        help_text="Wgrane zdjecie tla (layout A).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Story slide"
        verbose_name_plural = "Story slides"
        ordering = ["research", "order"]
        unique_together = ("research", "order")

    def __str__(self):
        return f"{self.research.week_label} #{self.order} ({self.slide_type})"
