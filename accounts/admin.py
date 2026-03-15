from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, VerificationCode


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "phone_number",
        "role",
        "is_email_verified",
        "is_phone_verified",
        "is_active",
        "is_staff",
        "created_at",
    )
    list_filter = (
        "role",
        "is_email_verified",
        "is_phone_verified",
        "is_active",
        "is_staff",
        "is_superuser",
        "preferred_contact_method",
        "created_at",
    )
    search_fields = ("username", "email", "phone_number")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "last_login", "date_joined")

    fieldsets = (
        ("Login credentials", {
            "fields": ("username", "password")
        }),
        ("Personal info", {
            "fields": ("first_name", "last_name", "bio")
        }),
        ("Contacts", {
            "fields": (
                "email",
                "phone_number",
                "preferred_contact_method",
                "is_email_verified",
                "is_phone_verified",
            )
        }),
        ("Role", {
            "fields": ("role",)
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Important dates", {
            "fields": ("last_login", "date_joined", "created_at", "updated_at")
        }),
    )

    add_fieldsets = (
        ("Create user", {
            "classes": ("wide",),
            "fields": (
                "username",
                "email",
                "phone_number",
                "role",
                "preferred_contact_method",
                "password1",
                "password2",
                "is_active",
                "is_staff",
                "is_superuser",
            ),
        }),
    )


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "target",
        "channel",
        "purpose",
        "status",
        "code",
        "attempt_count",
        "max_attempts",
        "expires_at",
        "used_at",
        "created_at",
    )
    list_filter = (
        "channel",
        "purpose",
        "status",
        "created_at",
        "expires_at",
        "used_at",
    )
    search_fields = (
        "target",
        "code",
        "user__username",
        "user__email",
        "user__phone_number",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "used_at")

    fieldsets = (
        ("Main info", {
            "fields": ("user", "target", "channel", "purpose", "status")
        }),
        ("Code data", {
            "fields": ("code", "attempt_count", "max_attempts")
        }),
        ("Dates", {
            "fields": ("expires_at", "used_at", "created_at", "updated_at")
        }),
    )