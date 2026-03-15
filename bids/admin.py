from django.contrib import admin

from .models import Bid


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project",
        "freelancer",
        "price",
        "delivery_time_days",
        "status",
        "created_at",
    )
    list_filter = (
        "status",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "proposal",
        "project__title",
        "freelancer__username",
        "freelancer__email",
        "freelancer__phone_number",
        "project__client__username",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)
    list_select_related = (
        "project",
        "freelancer",
        "project__client",
    )

    fieldsets = (
        (
            "Bid info",
            {
                "fields": (
                    "project",
                    "freelancer",
                    "proposal",
                )
            },
        ),
        (
            "Offer details",
            {
                "fields": (
                    "price",
                    "delivery_time_days",
                    "status",
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
