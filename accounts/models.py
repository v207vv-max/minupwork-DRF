from datetime import timedelta

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    CLIENT = "client", _("Client")
    FREELANCER = "freelancer", _("Freelancer")


class VerificationChannel(models.TextChoices):
    EMAIL = "email", _("Email")
    PHONE = "phone", _("Phone")


class VerificationPurpose(models.TextChoices):
    SIGNUP = "signup", _("Signup")
    RESET_PASSWORD = "reset_password", _("Reset password")
    CHANGE_PASSWORD = "change_password", _("Change password")
    VERIFY_EMAIL = "verify_email", _("Verify email")
    VERIFY_PHONE = "verify_phone", _("Verify phone")


class VerificationStatus(models.TextChoices):
    NEW = "new", _("New")
    USED = "used", _("Used")
    EXPIRED = "expired", _("Expired")
    CANCELLED = "cancelled", _("Cancelled")


class UserManager(BaseUserManager):
    def _normalize_phone(self, phone_number: str | None) -> str | None:
        if not phone_number:
            return None
        return "".join(phone_number.strip().split())

    def _create_user(self, username, password, **extra_fields):
        email = extra_fields.get("email")
        phone_number = extra_fields.get("phone_number")

        if not username:
            raise ValueError(_("The username field is required."))

        if not email and not phone_number:
            raise ValueError(_("Either email or phone number must be provided."))

        if email:
            extra_fields["email"] = self.normalize_email(email).lower()

        if phone_number:
            extra_fields["phone_number"] = self._normalize_phone(phone_number)

        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", False)  # activation by code
        return self._create_user(username=username, password=password, **extra_fields)

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("role", UserRole.CLIENT)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_email_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        if not password:
            raise ValueError(_("Superuser must have a password."))
        if not extra_fields.get("email") and not extra_fields.get("phone_number"):
            raise ValueError(_("Superuser must have either email or phone number."))

        return self._create_user(username=username, password=password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(
        unique=True,
        null=True,
        blank=True,
        help_text=_("Optional. Must be unique if provided."),
    )
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Optional. Must be unique if provided."),
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
    )
    bio = models.TextField(blank=True)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    image = models.ImageField(upload_to="user_images/", default="user_images/default.jpg", null=True, blank=True)
    preferred_contact_method = models.CharField(
        max_length=10,
        choices=VerificationChannel.choices,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["username"]),
            models.Index(fields=["email"]),
            models.Index(fields=["phone_number"]),
        ]

    def __str__(self):
        return f"{self.username} ({self.role})"

    def clean(self):
        super().clean()

        if self.email:
            self.email = self.__class__.objects.normalize_email(self.email).lower()

        if self.phone_number:
            self.phone_number = "".join(self.phone_number.strip().split())

        if not self.email and not self.phone_number:
            raise ValidationError(_("User must have either email or phone number."))

        if self.preferred_contact_method == VerificationChannel.EMAIL and not self.email:
            raise ValidationError(
                {"preferred_contact_method": _("Preferred method is email, but email is empty.")}
            )

        if self.preferred_contact_method == VerificationChannel.PHONE and not self.phone_number:
            raise ValidationError(
                {"preferred_contact_method": _("Preferred method is phone, but phone number is empty.")}
            )

    @property
    def is_freelancer(self):
        return self.role == UserRole.FREELANCER

    @property
    def is_client(self):
        return self.role == UserRole.CLIENT

    def get_default_contact(self):
        """
        Returns the best available contact channel and target.
        Example:
            ("email", "user@example.com")
            ("phone", "+998901234567")
        """
        if self.preferred_contact_method == VerificationChannel.EMAIL and self.email:
            return VerificationChannel.EMAIL, self.email

        if self.preferred_contact_method == VerificationChannel.PHONE and self.phone_number:
            return VerificationChannel.PHONE, self.phone_number

        if self.email:
            return VerificationChannel.EMAIL, self.email

        if self.phone_number:
            return VerificationChannel.PHONE, self.phone_number

        return None, None


class VerificationCode(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="verification_codes",
        null=True,
        blank=True,
    )
    channel = models.CharField(
        max_length=10,
        choices=VerificationChannel.choices,
    )
    purpose = models.CharField(
        max_length=30,
        choices=VerificationPurpose.choices,
    )
    status = models.CharField(
        max_length=10,
        choices=VerificationStatus.choices,
        default=VerificationStatus.NEW,
    )

    target = models.CharField(
        max_length=255,
        help_text=_("Email address or phone number where the code was sent."),
    )
    code = models.CharField(
        max_length=10,
        help_text=_("Verification code. Usually 4-6 digits."),
    )

    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    attempt_count = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=5)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["target"]),
            models.Index(fields=["channel"]),
            models.Index(fields=["purpose"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["user", "purpose"]),
        ]

    def __str__(self):
        return f"{self.target} | {self.purpose} | {self.status}"

    def clean(self):
        super().clean()

        if self.channel == VerificationChannel.EMAIL:
            self.target = (self.target or "").strip().lower()
        elif self.channel == VerificationChannel.PHONE:
            self.target = "".join((self.target or "").strip().split())

        if not self.code:
            raise ValidationError({"code": _("Code cannot be empty.")})

        if self.max_attempts < 1:
            raise ValidationError({"max_attempts": _("max_attempts must be at least 1.")})

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def can_be_used(self):
        return (
            self.status == VerificationStatus.NEW
            and not self.is_expired
            and self.attempt_count < self.max_attempts
        )

    def mark_used(self):
        self.status = VerificationStatus.USED
        self.used_at = timezone.now()
        self.save(update_fields=["status", "used_at", "updated_at"])

    def mark_expired(self):
        self.status = VerificationStatus.EXPIRED
        self.save(update_fields=["status", "updated_at"])

    def mark_cancelled(self):
        self.status = VerificationStatus.CANCELLED
        self.save(update_fields=["status", "updated_at"])

    def increase_attempts(self):
        self.attempt_count += 1
        if self.attempt_count >= self.max_attempts and self.status == VerificationStatus.NEW:
            self.status = VerificationStatus.CANCELLED
        self.save(update_fields=["attempt_count", "status", "updated_at"])
