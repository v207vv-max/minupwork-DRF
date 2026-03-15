from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "contract",
        "project",
        "client",
        "freelancer",
        "rating",
        "sentiment",
        "created_at",
    )
    list_filter = (
        "rating",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "project__title",
        "client__username",
        "client__email",
        "freelancer__username",
        "freelancer__email",
        "comment",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "sentiment",
        "short_comment",
    )
    ordering = ("-created_at",)
    list_select_related = (
        "contract",
        "project",
        "client",
        "freelancer",
    )
    autocomplete_fields = (
        "contract",
        "project",
        "client",
        "freelancer",
    )

    fieldsets = (
        (
            "Review relations",
            {
                "fields": (
                    "contract",
                    "project",
                    "client",
                    "freelancer",
                )
            },
        ),
        (
            "Review content",
            {
                "fields": (
                    "rating",
                    "comment",
                    "sentiment",
                    "short_comment",
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
            "contract",
            "project",
            "client",
            "freelancer",
        )