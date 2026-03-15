from rest_framework import serializers

from accounts.serializers import UserSerializer
from contracts.serializers import ContractSerializer

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = (
            "id",
            "sender",
            "text",
            "image",
            "is_read",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class MessageCreateSerializer(serializers.Serializer):
    text = serializers.CharField(required=False, allow_blank=True)
    image = serializers.ImageField(required=False, allow_null=True)

    def validate(self, attrs):
        text = (attrs.get("text") or "").strip()
        image = attrs.get("image")

        if not text and not image:
            raise serializers.ValidationError("Message must contain text or image.")

        if text and len(text) > 3000:
            raise serializers.ValidationError("Message text cannot be longer than 3000 characters.")

        attrs["text"] = text
        return attrs


class ConversationSerializer(serializers.ModelSerializer):
    contract = ContractSerializer(read_only=True)
    client = UserSerializer(read_only=True)
    freelancer = UserSerializer(read_only=True)
    unread_messages_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = (
            "id",
            "contract",
            "client",
            "freelancer",
            "created_at",
            "updated_at",
            "unread_messages_count",
        )
        read_only_fields = fields

    def get_unread_messages_count(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or user.is_anonymous:
            return 0
        return obj.messages.filter(is_read=False).exclude(sender=user).count()


class ConversationDetailSerializer(ConversationSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ("messages",)
