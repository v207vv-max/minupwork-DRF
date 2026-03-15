from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "client",
        "budget",
        "status",
        "is_active",
        "deadline",
        "created_at",
    )
    list_filter = (
        "status",
        "is_active",
        "created_at",
        "deadline",
    )
    search_fields = (
        "title",
        "description",
        "skills_required",
        "client__username",
        "client__email",
        "client__phone_number",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Project info",
            {
                "fields": (
                    "client",
                    "title",
                    "description",
                    "skills_required",
                )
            },
        ),
        (
            "Budget and deadline",
            {
                "fields": (
                    "budget",
                    "deadline",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "status",
                    "is_active",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )