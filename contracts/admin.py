from django.contrib import admin

from .models import Contract


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project",
        "client",
        "freelancer",
        "agreed_price",
        "status",
        "started_at",
        "finished_at",
        "cancelled_at",
        "created_at",
    )
    list_filter = (
        "status",
        "created_at",
        "started_at",
        "finished_at",
        "cancelled_at",
    )
    search_fields = (
        "project__title",
        "client__username",
        "client__email",
        "client__phone_number",
        "freelancer__username",
        "freelancer__email",
        "freelancer__phone_number",
        "notes",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "started_at",
        "finished_at",
        "cancelled_at",
    )
    ordering = ("-created_at",)
    list_select_related = (
        "project",
        "bid",
        "client",
        "freelancer",
    )
    autocomplete_fields = (
        "project",
        "bid",
        "client",
        "freelancer",
    )

    fieldsets = (
        (
            "Contract relations",
            {
                "fields": (
                    "project",
                    "bid",
                    "client",
                    "freelancer",
                )
            },
        ),
        (
            "Financial details",
            {
                "fields": (
                    "agreed_price",
                    "status",
                )
            },
        ),
        (
            "Additional details",
            {
                "fields": (
                    "notes",
                )
            },
        ),
        (
            "Contract timeline",
            {
                "fields": (
                    "started_at",
                    "finished_at",
                    "cancelled_at",
                )
            },
        ),
        (
            "System fields",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            "project",
            "bid",
            "client",
            "freelancer",
        )