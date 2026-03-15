import random
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import (
    User,
    VerificationCode,
    VerificationChannel,
    VerificationPurpose,
    VerificationStatus,
)


def generate_code():

    return str(random.randint(100000, 999999))


def create_verification_code(*, user, channel, purpose, target):

    code = generate_code()

    verification = VerificationCode.objects.create(
        user=user,
        channel=channel,
        purpose=purpose,
        target=target,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=10),
    )

    if channel == VerificationChannel.EMAIL:
        send_verification_code_email(
            to_email=target,
            code=code,
            purpose=purpose,
        )
        print(f'----------------------------{code}')
    else:
        # Phone delivery is intentionally not implemented for this project.
        # We keep the field and channel for architecture completeness.
        print(f"[PHONE DELIVERY NOT IMPLEMENTED] Verification code for {target}: {code}")

    return verification


# ===============================
# SIGNUP
# ===============================

def register_user(
    *,
    username,
    password,
    role,
    email=None,
    phone_number=None,
    preferred_contact_method=None,
):


    if not email and not phone_number:
        raise ValidationError(_("Email or phone number must be provided"))

    user = User.objects.create_user(
        username=username,
        password=password,
        role=role,
        email=email,
        phone_number=phone_number,
        preferred_contact_method=preferred_contact_method,
    )

    channel, target = resolve_contact_channel_and_target(
        email=user.email,
        phone_number=user.phone_number,
        preferred_contact_method=user.preferred_contact_method,
    )

    create_verification_code(
        user=user,
        channel=channel,
        purpose=VerificationPurpose.SIGNUP,
        target=target,
    )

    return user


def _get_pending_verification(*, user, purpose):
    verification = (
        VerificationCode.objects.filter(
            user=user,
            purpose=purpose,
            status=VerificationStatus.NEW,
        )
        .order_by("-created_at")
        .first()
    )

    if not verification:
        raise ValidationError(_("Invalid verification code"))

    if verification.is_expired:
        verification.mark_expired()
        raise ValidationError(_("Verification code expired"))

    if not verification.can_be_used:
        verification.mark_cancelled()
        raise ValidationError(_("Verification code can no longer be used"))

    return verification


# ===============================
# VERIFY SIGNUP
# ===============================

def verify_signup_code(*, user, code):


    verification = _get_pending_verification(
        user=user,
        purpose=VerificationPurpose.SIGNUP,
    )

    if verification.code != code:
        verification.increase_attempts()
        raise ValidationError(_("Invalid verification code"))

    verification.mark_used()

    user.is_active = True

    if verification.channel == VerificationChannel.EMAIL:
        user.is_email_verified = True

    if verification.channel == VerificationChannel.PHONE:
        user.is_phone_verified = True

    user.save(update_fields=["is_active", "is_email_verified", "is_phone_verified"])

    return user


# ===============================
# LOGIN
# ===============================

def authenticate_user(identifier, password):


    user = (
        User.objects.filter(username=identifier).first()
        or User.objects.filter(email=identifier).first()
        or User.objects.filter(phone_number=identifier).first()
    )

    if not user:
        raise ValidationError(_("User not found"))

    user = authenticate(username=user.username, password=password)

    if not user:
        raise ValidationError(_("Invalid password"))

    if not user.is_active:
        raise ValidationError(_("User account is not active"))

    return user


# ===============================
# FORGOT PASSWORD
# ===============================

def request_password_reset(identifier):


    user = (
        User.objects.filter(username=identifier).first()
        or User.objects.filter(email=identifier).first()
        or User.objects.filter(phone_number=identifier).first()
    )

    if not user:
        raise ValidationError(_("User not found"))

    channel, target = resolve_contact_channel_and_target(
        email=user.email,
        phone_number=user.phone_number,
        preferred_contact_method=user.preferred_contact_method,
    )

    create_verification_code(
        user=user,
        channel=channel,
        purpose=VerificationPurpose.RESET_PASSWORD,
        target=target,
    )

    return user


# ===============================
# RESET PASSWORD
# ===============================

def reset_password(*, user, code, new_password):


    verification = _get_pending_verification(
        user=user,
        purpose=VerificationPurpose.RESET_PASSWORD,
    )

    if verification.code != code:
        verification.increase_attempts()
        raise ValidationError(_("Invalid verification code"))

    verification.mark_used()

    user.set_password(new_password)
    user.save(update_fields=["password"])

    return user


# ===============================
# CHANGE PASSWORD
# ===============================

def change_password(*, user, old_password, new_password):


    if not user.check_password(old_password):
        raise ValidationError(_("Old password is incorrect"))

    user.set_password(new_password)
    user.save(update_fields=["password"])

    return user

def resolve_contact_channel_and_target(*, email=None, phone_number=None, preferred_contact_method=None):


    if email:
        return VerificationChannel.EMAIL, email

    if phone_number:
        return VerificationChannel.PHONE, phone_number

    raise ValidationError(_("Email or phone number must be provided."))


def send_verification_code_email(*, to_email, code, purpose):

    subject = "Your verification code"
    message = (
        f"Your verification code for {purpose} is: {code}\n\n"
        f"This code will expire in 10 minutes."
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )
