from django.db import models


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
