from django.contrib import admin

from .models import CafeInquiry, CafeLocation, WorkshopInterest


@admin.register(CafeLocation)
class CafeLocationAdmin(admin.ModelAdmin):
    list_display = ["name", "address", "sort_order", "is_active", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "address", "products_note"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["sort_order", "name"]


@admin.register(CafeInquiry)
class CafeInquiryAdmin(admin.ModelAdmin):
    list_display = [
        "venue_name",
        "contact_name",
        "city",
        "frequency",
        "status",
        "created_at",
    ]
    list_filter = ["status", "frequency", "created_at"]
    search_fields = [
        "venue_name",
        "contact_name",
        "email",
        "phone",
        "city",
        "interested_products",
        "message",
    ]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"


@admin.register(WorkshopInterest)
class WorkshopInterestAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "topic", "preferred_timing", "created_at"]
    list_filter = ["topic", "preferred_timing", "created_at"]
    search_fields = ["name", "email"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"
