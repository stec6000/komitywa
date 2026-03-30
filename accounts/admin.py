from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db import transaction

from allauth.account.models import EmailAddress

from .forms import AdminUserChangeForm, AdminUserCreationForm

User = get_user_model()


@admin.action(description="Activate users")
def activate_users(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(
        request,
        f"Activated {updated} user(s).",
        level=messages.SUCCESS,
    )


@admin.action(description="Deactivate users")
def deactivate_users(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(
        request,
        f"Deactivated {updated} user(s).",
        level=messages.SUCCESS,
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = AdminUserCreationForm
    form = AdminUserChangeForm
    model = User
    list_display = (
        "email",
        "is_active",
        "is_staff",
        "is_superuser",
        "last_login",
        "date_joined",
    )
    search_fields = ("email",)
    list_filter = ("is_active", "is_staff", "is_superuser")
    ordering = ("email",)
    actions = (activate_users, deactivate_users)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_active", "is_staff", "is_superuser"),
            },
        ),
    )
    readonly_fields = ("last_login", "date_joined")


@admin.action(description="Mark selected as verified")
def mark_email_verified(modeladmin, request, queryset):
    updated = queryset.update(verified=True)
    modeladmin.message_user(
        request,
        f"Marked {updated} email address(es) as verified.",
        level=messages.SUCCESS,
    )


@admin.action(description="Mark selected as primary")
def mark_email_primary(modeladmin, request, queryset):
    updated = 0
    with transaction.atomic():
        for user_id in queryset.values_list("user_id", flat=True).distinct():
            selected_for_user = queryset.filter(user_id=user_id).order_by("pk")
            selected = selected_for_user.first()
            if not selected:
                continue
            EmailAddress.objects.filter(user_id=user_id).exclude(pk=selected.pk).update(
                primary=False
            )
            EmailAddress.objects.filter(pk=selected.pk).update(primary=True)
            updated += 1
    modeladmin.message_user(
        request,
        f"Marked {updated} user(s) with a primary email.",
        level=messages.SUCCESS,
    )


class EmailAddressAdmin(admin.ModelAdmin):
    list_display = ("email", "user", "verified", "primary")
    search_fields = ("email",)
    list_filter = ("verified", "primary")
    actions = (mark_email_verified, mark_email_primary)


try:
    admin.site.unregister(EmailAddress)
except admin.sites.NotRegistered:
    pass

admin.site.register(EmailAddress, EmailAddressAdmin)
