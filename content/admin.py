from django.contrib import admin

from .models import WeeklyResearch


@admin.register(WeeklyResearch)
class WeeklyResearchAdmin(admin.ModelAdmin):
    change_form_template = "admin/content/weeklyresearch/change_form.html"
    list_display = ("week_label", "date_from", "date_to", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("week_label",)
    readonly_fields = ("raw_research", "formatted_json", "created_at", "updated_at")
    ordering = ("-date_to",)
