from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.permissions import ContractPermission

from .filters import ContractFilter
from .models import Contract
from .serializers import ContractSerializer
from .services import finish_contract


def _raise_drf_validation_error(exc):
    if hasattr(exc, "message_dict"):
        raise ValidationError(exc.message_dict)
    raise ValidationError(exc.messages)


class ContractViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated, ContractPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ContractFilter
    ordering_fields = ["created_at", "started_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        queryset = Contract.objects.select_related(
            "project",
            "project__client",
            "bid",
            "bid__freelancer",
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

    @action(detail=True, methods=["post"])
    def finish(self, request, pk=None):
        contract = self.get_object()

        try:
            finish_contract(
                contract=contract,
                client=request.user,
            )
        except DjangoValidationError as exc:
            _raise_drf_validation_error(exc)

        contract.refresh_from_db()
        serializer = self.get_serializer(contract)
        return Response(serializer.data, status=status.HTTP_200_OK)
