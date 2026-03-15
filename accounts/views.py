from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Avg, Count
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView

from contracts.models import Contract, ContractStatus
from reviews.models import Review

from .models import User, UserRole
from .serializers import (
    ChangePasswordSerializer,
    FreelancerProfileSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    SignUpSerializer,
    UserSerializer,
    VerifySignupCodeSerializer,
)
from .services import (
    authenticate_user,
    change_password,
    register_user,
    request_password_reset,
    reset_password,
    verify_signup_code,
)


def _raise_drf_validation_error(exc):
    if hasattr(exc, "message_dict"):
        raise ValidationError(exc.message_dict)
    raise ValidationError(exc.messages)


def _get_token_payload(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def _get_freelancer_stats(user):
    review_summary = Review.objects.filter(freelancer=user).aggregate(
        average_rating=Avg("rating"),
        review_count=Count("id"),
    )
    completed_orders = Contract.objects.filter(
        freelancer=user,
        status=ContractStatus.FINISHED,
    ).count()

    average_rating = review_summary["average_rating"]
    return {
        "average_rating": round(float(average_rating), 1) if average_rating is not None else None,
        "review_count": review_summary["review_count"],
        "completed_orders": completed_orders,
    }


class SignUpAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = register_user(**serializer.validated_data)
        except DjangoValidationError as exc:
            _raise_drf_validation_error(exc)

        return Response(
            {
                "message": "Verification code was sent successfully.",
                "pending_user_id": user.id,
                "user": UserSerializer(user, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifySignupCodeAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifySignupCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        try:
            user = verify_signup_code(
                user=user,
                code=serializer.validated_data["code"],
            )
        except DjangoValidationError as exc:
            _raise_drf_validation_error(exc)

        return Response(
            {
                "message": "Account verified successfully.",
                "tokens": _get_token_payload(user),
                "user": UserSerializer(user, context={"request": request}).data,
            }
        )


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = authenticate_user(
                identifier=serializer.validated_data["identifier"],
                password=serializer.validated_data["password"],
            )
        except DjangoValidationError as exc:
            _raise_drf_validation_error(exc)

        return Response(
            {
                "tokens": _get_token_payload(user),
                "user": UserSerializer(user, context={"request": request}).data,
            }
        )


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        payload = UserSerializer(request.user, context={"request": request}).data
        if request.user.is_freelancer:
            payload["freelancer_stats"] = _get_freelancer_stats(request.user)
        return Response(payload)

    def patch(self, request):
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class FreelancerProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        freelancer = User.objects.filter(
            role=UserRole.FREELANCER,
            pk=pk,
        ).first()
        if not freelancer:
            raise NotFound("Freelancer not found.")

        payload = FreelancerProfileSerializer(
            freelancer,
            context={"request": request},
        ).data
        payload["freelancer_stats"] = _get_freelancer_stats(freelancer)
        return Response(payload)


class PasswordResetRequestAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = request_password_reset(serializer.validated_data["identifier"])
        except DjangoValidationError as exc:
            _raise_drf_validation_error(exc)

        return Response(
            {
                "message": "Password reset code was sent.",
                "reset_user_id": user.id,
            }
        )


class PasswordResetConfirmAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            reset_password(
                user=serializer.validated_data["user"],
                code=serializer.validated_data["code"],
                new_password=serializer.validated_data["new_password"],
            )
        except DjangoValidationError as exc:
            _raise_drf_validation_error(exc)

        return Response({"message": "Password was reset successfully."})


class ChangePasswordAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            change_password(
                user=request.user,
                old_password=serializer.validated_data["old_password"],
                new_password=serializer.validated_data["new_password"],
            )
        except DjangoValidationError as exc:
            _raise_drf_validation_error(exc)

        return Response({"message": "Password changed successfully."})
