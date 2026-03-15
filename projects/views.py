from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.permissions import ProjectPermission

from .filters import ProjectFilter
from .models import Project, ProjectStatus
from .serializers import ProjectSerializer


def _raise_drf_validation_error(exc):
    if hasattr(exc, "message_dict"):
        raise ValidationError(exc.message_dict)
    raise ValidationError(exc.messages)


class ProjectViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, ProjectPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProjectFilter
    search_fields = ["title"]
    ordering_fields = ["created_at", "budget", "deadline"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        queryset = Project.objects.select_related("client").all()

        if getattr(user, "role", None) == "freelancer":
            queryset = queryset.filter(
                status=ProjectStatus.OPEN,
                is_active=True,
            )
        elif getattr(user, "role", None) == "client":
            queryset = queryset.filter(client=user)
        else:
            queryset = queryset.none()

        return queryset.order_by("-created_at")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            project = serializer.save(client=request.user)
        except DjangoValidationError as exc:
            _raise_drf_validation_error(exc)

        output_serializer = self.get_serializer(project)
        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )
