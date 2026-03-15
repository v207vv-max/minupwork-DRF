from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)

    class Meta:
        model = Project
        fields = (
            "id",
            "client",
            "title",
            "description",
            "budget",
            "deadline",
            "status",
            "skills_required",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "client",
            "status",
            "is_active",
            "created_at",
            "updated_at",
        )

    def validate_title(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Title cannot be empty.")

        if len(value) < 5:
            raise serializers.ValidationError("Title must contain at least 5 characters.")

        return value

    def validate_description(self, value):
        value = value.strip()

        if len(value) < 20:
            raise serializers.ValidationError(
                "Description must contain at least 20 characters."
            )

        return value

    def validate_budget(self, value):
        if value is None:
            raise serializers.ValidationError("Budget is required.")

        if value <= 0:
            raise serializers.ValidationError("Budget must be greater than 0.")

        return value

    def validate_deadline(self, value):
        from django.utils import timezone

        if value < timezone.localdate():
            raise serializers.ValidationError("Deadline cannot be in the past.")

        return value

    def validate_skills_required(self, value):
        return (value or "").strip()

