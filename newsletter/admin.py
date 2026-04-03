from django.contrib import admin

from .models import Subscriber


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ["email", "is_confirmed", "is_unsubscribed", "created_at"]
    list_filter = ["is_confirmed", "is_unsubscribed"]
    search_fields = ["email"]
    readonly_fields = [
        "confirmation_token",
        "unsubscribe_token",
        "confirmation_sent_at",
        "created_at",
    ]
