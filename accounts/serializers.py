from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User, VerificationChannel


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "phone_number",
            "role",
            "bio",
            "image",
            "preferred_contact_method",
            "is_email_verified",
            "is_phone_verified",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "is_email_verified",
            "is_phone_verified",
            "created_at",
            "updated_at",
        )

    def validate_username(self, value):
        value = value.strip()
        queryset = User.objects.filter(username=value)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("Username already exists.")

        return value

    def validate_email(self, value):
        if not value:
            return value

        value = value.strip().lower()
        queryset = User.objects.filter(email=value)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("Email already exists.")

        return value

    def validate_phone_number(self, value):
        if not value:
            return value

        value = "".join(value.strip().split())
        queryset = User.objects.filter(phone_number=value)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("Phone number already exists.")

        return value

    def validate(self, attrs):
        email = attrs.get("email", getattr(self.instance, "email", None))
        phone_number = attrs.get("phone_number", getattr(self.instance, "phone_number", None))
        preferred_contact_method = attrs.get(
            "preferred_contact_method",
            getattr(self.instance, "preferred_contact_method", None),
        )

        if not email and not phone_number:
            raise serializers.ValidationError(
                "You must provide either email or phone number."
            )

        if preferred_contact_method == VerificationChannel.EMAIL and not email:
            raise serializers.ValidationError(
                "Preferred contact method is email, but email is empty."
            )

        if preferred_contact_method == VerificationChannel.PHONE and not phone_number:
            raise serializers.ValidationError(
                "Preferred contact method is phone, but phone number is empty."
            )

        return attrs


class FreelancerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "role",
            "bio",
            "image",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class SignUpSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    role = serializers.ChoiceField(choices=User._meta.get_field("role").choices)
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    preferred_contact_method = serializers.ChoiceField(
        choices=VerificationChannel.choices,
        required=False,
        allow_null=True,
    )
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_username(self, value):
        value = value.strip()
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    def validate_email(self, value):
        if not value:
            return None
        value = value.strip().lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def validate_phone_number(self, value):
        if not value:
            return None
        value = "".join(value.strip().split())
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number already exists.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        validate_password(attrs["password"])

        if not attrs.get("email") and not attrs.get("phone_number"):
            raise serializers.ValidationError("You must provide either email or phone number.")

        preferred_contact_method = attrs.get("preferred_contact_method")
        if preferred_contact_method == VerificationChannel.EMAIL and not attrs.get("email"):
            raise serializers.ValidationError(
                {"preferred_contact_method": "Preferred contact method is email, but email is empty."}
            )

        if preferred_contact_method == VerificationChannel.PHONE and not attrs.get("phone_number"):
            raise serializers.ValidationError(
                {
                    "preferred_contact_method": "Preferred contact method is phone, but phone number is empty."
                }
            )

        attrs.pop("confirm_password")
        return attrs


class VerifySignupCodeSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    code = serializers.CharField(max_length=10)

    def validate(self, attrs):
        user = User.objects.filter(pk=attrs["user_id"]).first()
        if not user:
            raise serializers.ValidationError({"user_id": "User not found."})
        attrs["user"] = user
        return attrs


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    code = serializers.CharField(max_length=10)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = User.objects.filter(pk=attrs["user_id"]).first()
        if not user:
            raise serializers.ValidationError({"user_id": "User not found."})

        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        validate_password(attrs["new_password"], user=user)
        attrs["user"] = user
        attrs.pop("confirm_password")
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        validate_password(attrs["new_password"])
        attrs.pop("confirm_password")
        return attrs
