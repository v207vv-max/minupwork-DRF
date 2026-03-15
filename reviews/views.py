from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import mixins, status, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.permissions import ReviewPermission

from .filters import ReviewFilter
from .models import Review
from .serializers import ReviewSerializer
from .services import create_review


def _raise_drf_validation_error(exc):
    if hasattr(exc, "message_dict"):
        raise ValidationError(exc.message_dict)
    raise ValidationError(exc.messages)


class ReviewViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, ReviewPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ReviewFilter
    ordering_fields = ["created_at", "rating"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        queryset = Review.objects.select_related(
            "contract",
            "contract__project",
            "project",
            "client",
            "freelancer",
        )

        if getattr(user, "role", None) == "client":
            queryset = queryset.filter(client=user)
        elif getattr(user, "role", None) == "freelancer":
            queryset = queryset.filter(freelancer=user)
        else:
            queryset = queryset.none()

        return queryset.order_by("-created_at")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contract = serializer.validated_data["contract"]

        try:
            review = create_review(
                contract=contract,
                client=request.user,
                rating=serializer.validated_data["rating"],
                comment=serializer.validated_data["comment"],
            )
        except DjangoValidationError as exc:
            _raise_drf_validation_error(exc)

        output_serializer = self.get_serializer(review)
        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )
