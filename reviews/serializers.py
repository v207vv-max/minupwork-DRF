from rest_framework import serializers

from accounts.serializers import UserSerializer
from contracts.models import Contract, ContractStatus
from contracts.serializers import ContractSerializer
from projects.serializers import ProjectSerializer

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    contract = ContractSerializer(read_only=True)
    contract_id = serializers.PrimaryKeyRelatedField(
        source="contract",
        queryset=Contract.objects.select_related("project", "client", "freelancer"),
        write_only=True,
        required=False,
    )
    project = ProjectSerializer(read_only=True)
    client = UserSerializer(read_only=True)
    freelancer = UserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = (
            "id",
            "contract",
            "contract_id",
            "project",
            "client",
            "freelancer",
            "rating",
            "comment",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "contract",
            "project",
            "client",
            "freelancer",
            "created_at",
            "updated_at",
        )

    def validate_rating(self, value):
        if value is None:
            raise serializers.ValidationError("Rating is required.")

        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")

        return value

    def validate_comment(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Comment cannot be empty.")

        if len(value) < 10:
            raise serializers.ValidationError("Comment must contain at least 10 characters.")

        return value

    def validate(self, attrs):
        request = self.context.get("request")
        client = getattr(request, "user", None)
        contract = attrs.get("contract") or getattr(self.instance, "contract", None)

        if not contract:
            raise serializers.ValidationError({"contract_id": "Contract is required."})

        if client and not client.is_anonymous:
            if getattr(client, "role", None) != "client":
                raise serializers.ValidationError("Only clients can create reviews.")

            if contract.client_id != client.id:
                raise serializers.ValidationError(
                    "You can create a review only for your own contract."
                )

        if contract.status != ContractStatus.FINISHED:
            raise serializers.ValidationError(
                "Review can only be created for a finished contract."
            )

        existing_review = Review.objects.filter(contract=contract)
        if self.instance:
            existing_review = existing_review.exclude(pk=self.instance.pk)

        if existing_review.exists():
            raise serializers.ValidationError("Review for this contract already exists.")

        return attrs
