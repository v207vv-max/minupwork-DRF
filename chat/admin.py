from django.contrib import admin

from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "contract",
        "client",
        "freelancer",
        "can_send_messages",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "created_at",
        "updated_at",
    )
    search_fields = (
        "client__username",
        "client__email",
        "freelancer__username",
        "freelancer__email",
        "contract__project__title",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "can_send_messages",
    )
    ordering = ("-updated_at",)
    list_select_related = (
        "contract",
        "client",
        "freelancer",
        "contract__project",
    )
    autocomplete_fields = (
        "contract",
        "client",
        "freelancer",
    )

    fieldsets = (
        (
            "Conversation relations",
            {
                "fields": (
                    "contract",
                    "client",
                    "freelancer",
                )
            },
        ),
        (
            "Conversation state",
            {
                "fields": (
                    "can_send_messages",
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
            "client",
            "freelancer",
            "contract__project",
        )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "conversation",
        "sender",
        "has_text",
        "has_image",
        "is_read",
        "created_at",
    )
    list_filter = (
        "is_read",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "text",
        "sender__username",
        "sender__email",
        "conversation__contract__project__title",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "has_text",
        "has_image",
        "short_text",
    )
    ordering = ("-created_at",)
    list_select_related = (
        "conversation",
        "sender",
        "conversation__contract",
        "conversation__contract__project",
    )
    autocomplete_fields = (
        "conversation",
        "sender",
    )

    fieldsets = (
        (
            "Message relations",
            {
                "fields": (
                    "conversation",
                    "sender",
                )
            },
        ),
        (
            "Message content",
            {
                "fields": (
                    "text",
                    "image",
                    "short_text",
                    "has_text",
                    "has_image",
                )
            },
        ),
        (
            "Message state",
            {
                "fields": (
                    "is_read",
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
            "conversation",
            "sender",
            "conversation__contract",
            "conversation__contract__project",
        )