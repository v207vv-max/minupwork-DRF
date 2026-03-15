from django.urls import path

from .views import (
    ChangePasswordAPIView,
    FreelancerProfileAPIView,
    LoginAPIView,
    LogoutAPIView,
    PasswordResetConfirmAPIView,
    PasswordResetRequestAPIView,
    ProfileAPIView,
    SignUpAPIView,
    VerifySignupCodeAPIView,
)

app_name = "accounts"

urlpatterns = [
    path("signup/", SignUpAPIView.as_view(), name="signup"),
    path("verify-signup-code/", VerifySignupCodeAPIView.as_view(), name="verify-signup-code"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("me/", ProfileAPIView.as_view(), name="me"),
    path("freelancers/<int:pk>/", FreelancerProfileAPIView.as_view(), name="freelancer-profile"),
    path("password/reset/request/", PasswordResetRequestAPIView.as_view(), name="password-reset-request"),
    path("password/reset/confirm/", PasswordResetConfirmAPIView.as_view(), name="password-reset-confirm"),
    path("password/change/", ChangePasswordAPIView.as_view(), name="password-change"),
]
