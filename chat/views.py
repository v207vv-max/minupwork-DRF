from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Conversation
from .serializers import (
    ConversationDetailSerializer,
    ConversationSerializer,
    MessageCreateSerializer,
    MessageSerializer,
)
from .services import mark_conversation_as_read, send_message


def _raise_drf_validation_error(exc):
    if hasattr(exc, "message_dict"):
        raise ValidationError(exc.message_dict)
    raise ValidationError(exc.messages)


class ConversationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.select_related(
            "contract",
            "contract__project",
            "client",
            "freelancer",
        ).filter(
            models.Q(client=self.request.user) | models.Q(freelancer=self.request.user)
        ).order_by("-updated_at")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ConversationDetailSerializer
        return ConversationSerializer

    def retrieve(self, request, *args, **kwargs):
        conversation = self.get_object()

        if not conversation.has_participant(request.user):
            raise PermissionDenied("You do not have permission to view this conversation.")

        try:
            mark_conversation_as_read(
                conversation=conversation,
                user=request.user,
            )
        except DjangoValidationError as exc:
            _raise_drf_validation_error(exc)

        serializer = self.get_serializer(conversation)
        return Response(serializer.data)

    @action(detail=True, methods=["get", "post"], url_path="messages")
    def messages(self, request, pk=None):
        conversation = self.get_queryset().filter(pk=pk).first()
        if not conversation:
            raise NotFound("Conversation not found.")

        if request.method.lower() == "get":
            queryset = conversation.messages.select_related("sender").all()
            serializer = MessageSerializer(
                queryset,
                many=True,
                context={"request": request},
            )
            return Response(serializer.data)

        serializer = MessageCreateSerializer(
            data=request.data,
            context={"request": request, "conversation": conversation},
        )
        serializer.is_valid(raise_exception=True)

        try:
            message = send_message(
                conversation=conversation,
                sender=request.user,
                text=serializer.validated_data.get("text", ""),
                image=serializer.validated_data.get("image"),
            )
        except DjangoValidationError as exc:
            _raise_drf_validation_error(exc)
        except DjangoPermissionDenied as exc:
            raise PermissionDenied(str(exc))

        output_serializer = MessageSerializer(
            message,
            context={"request": request},
        )
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
