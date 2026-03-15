from rest_framework import serializers

from accounts.serializers import UserSerializer
from bids.serializers import BidSerializer
from projects.serializers import ProjectSerializer

from .models import Contract


class ContractSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(read_only=True)
    bid = BidSerializer(read_only=True)
    client = UserSerializer(read_only=True)
    freelancer = UserSerializer(read_only=True)

    class Meta:
        model = Contract
        fields = (
            "id",
            "project",
            "bid",
            "client",
            "freelancer",
            "agreed_price",
            "status",
            "notes",
            "started_at",
            "finished_at",
            "cancelled_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

