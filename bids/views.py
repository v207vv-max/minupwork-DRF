from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.permissions import BidPermission
from projects.models import Project

from .filters import BidFilter
from .models import Bid
from .serializers import BidSerializer
from .services import accept_bid, create_bid


def _raise_drf_validation_error(exc):
    if hasattr(exc, "message_dict"):
        raise ValidationError(exc.message_dict)
    raise ValidationError(exc.messages)


class BidViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated, BidPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = BidFilter
    ordering_fields = ["created_at", "price", "delivery_time_days"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        queryset = Bid.objects.select_related(
            "project",
            "project__client",
            "freelancer",
        )

        if getattr(user, "role", None) == "freelancer":
            queryset = queryset.filter(freelancer=user)
        elif getattr(user, "role", None) == "client":
            queryset = queryset.filter(project__client=user)
        else:
            queryset = queryset.none()

        return queryset.order_by("-created_at")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = serializer.validated_data["project"]

        try:
            bid = create_bid(
                project=project,
                freelancer=request.user,
                proposal=serializer.validated_data["proposal"],
                price=serializer.validated_data["price"],
                delivery_time_days=serializer.validated_data["delivery_time_days"],
            )
        except DjangoValidationError as exc:
            _raise_drf_validation_error(exc)

        output_serializer = self.get_serializer(bid)
        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @action(detail=False, methods=["get"], url_path=r"project/(?P<project_id>\d+)")
    def project_bids(self, request, project_id=None):
        if getattr(request.user, "role", None) != "client":
            raise PermissionDenied("Only clients can view bids on their projects.")

        project = Project.objects.select_related("client").filter(
            pk=project_id,
            client=request.user,
        ).first()
        if not project:
            raise PermissionDenied("You can view bids only for your own projects.")

        queryset = self.get_queryset().filter(project=project)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        bid = self.get_object()

        try:
            accept_bid(
                bid=bid,
                client=request.user,
            )
        except DjangoValidationError as exc:
            _raise_drf_validation_error(exc)

        bid.refresh_from_db()
        serializer = self.get_serializer(bid)
        return Response(serializer.data, status=status.HTTP_200_OK)
