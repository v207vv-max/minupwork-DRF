from rest_framework import serializers

from accounts.serializers import UserSerializer
from projects.models import Project, ProjectStatus
from projects.serializers import ProjectSerializer

from .models import Bid


class BidSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(read_only=True)
    project_id = serializers.PrimaryKeyRelatedField(
        source="project",
        queryset=Project.objects.select_related("client"),
        write_only=True,
    )
    freelancer = UserSerializer(read_only=True)

    class Meta:
        model = Bid
        fields = (
            "id",
            "project",
            "project_id",
            "freelancer",
            "proposal",
            "price",
            "delivery_time_days",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "project",
            "freelancer",
            "status",
            "created_at",
            "updated_at",
        )

    def validate_proposal(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Proposal cannot be empty.")

        if len(value) < 20:
            raise serializers.ValidationError("Proposal must contain at least 20 characters.")

        return value

    def validate_price(self, value):
        if value is None:
            raise serializers.ValidationError("Price is required.")

        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")

        return value

    def validate_delivery_time_days(self, value):
        if value is None:
            raise serializers.ValidationError("Delivery time is required.")

        if value < 1:
            raise serializers.ValidationError("Delivery time must be at least 1 day.")

        return value

    def validate(self, attrs):
        request = self.context.get("request")
        freelancer = getattr(request, "user", None)
        project = attrs.get("project") or getattr(self.instance, "project", None)

        if not project:
            raise serializers.ValidationError({"project_id": "Project is required."})

        if freelancer and not freelancer.is_anonymous:
            if getattr(freelancer, "role", None) != "freelancer":
                raise serializers.ValidationError("Only freelancers can create bids.")

            if project.client_id == freelancer.id:
                raise serializers.ValidationError("You cannot bid on your own project.")

            bid_exists = Bid.objects.filter(project=project, freelancer=freelancer)
            if self.instance:
                bid_exists = bid_exists.exclude(pk=self.instance.pk)

            if bid_exists.exists():
                raise serializers.ValidationError(
                    "Freelancer cannot submit two bids for the same project."
                )

        if project.status != ProjectStatus.OPEN:
            raise serializers.ValidationError("Bid can be sent only for open projects.")

        if not project.is_active:
            raise serializers.ValidationError("You cannot bid on an inactive project.")

        return attrs

