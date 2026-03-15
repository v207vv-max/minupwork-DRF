from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from projects.models import Project
from bids.models import Bid


class ContractStatus(models.TextChoices):
    ACTIVE = "active", _("Active")
    FINISHED = "finished", _("Finished")
    CANCELLED = "cancelled", _("Cancelled")


class Contract(models.Model):
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="contract",
    )

    bid = models.OneToOneField(
        Bid,
        on_delete=models.CASCADE,
        related_name="contract",
    )

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_contracts",
    )

    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="freelancer_contracts",
    )

    agreed_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Final agreed price for the project.",
    )

    status = models.CharField(
        max_length=20,
        choices=ContractStatus.choices,
        default=ContractStatus.ACTIVE,
    )

    notes = models.TextField(
        blank=True,
        help_text="Optional notes or agreement details.",
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    finished_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["client"]),
            models.Index(fields=["freelancer"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Contract #{self.id} | {self.project}"

    # ===============================
    # VALIDATION
    # ===============================

    def clean(self):
        super().clean()

        if not self.project:
            raise ValidationError("Contract must be linked to a project.")

        if not self.bid:
            raise ValidationError("Contract must be linked to a bid.")

        if self.bid.project != self.project:
            raise ValidationError("Bid must belong to the same project.")

        if self.bid.freelancer != self.freelancer:
            raise ValidationError("Freelancer must match the bid freelancer.")

        if self.project.client != self.client:
            raise ValidationError("Client must match the project owner.")

        if self.agreed_price <= 0:
            raise ValidationError("Agreed price must be greater than zero.")

        if self.status == ContractStatus.FINISHED and not self.finished_at:
            raise ValidationError("Finished contract must have finished_at.")

        if self.status == ContractStatus.CANCELLED and not self.cancelled_at:
            raise ValidationError("Cancelled contract must have cancelled_at.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    # ===============================
    # STATE HELPERS
    # ===============================

    @property
    def is_active(self):
        return self.status == ContractStatus.ACTIVE

    @property
    def is_finished(self):
        return self.status == ContractStatus.FINISHED

    @property
    def is_cancelled(self):
        return self.status == ContractStatus.CANCELLED

    # ===============================
    # STATE TRANSITIONS
    # ===============================

    def mark_started(self):
        if not self.started_at:
            self.started_at = timezone.now()
            self.save(update_fields=["started_at", "updated_at"])

    def mark_finished(self):
        if not self.is_active:
            raise ValidationError("Only active contracts can be finished.")

        self.status = ContractStatus.FINISHED
        self.finished_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "finished_at",
                "updated_at",
            ]
        )

    def mark_cancelled(self):
        if not self.is_active:
            raise ValidationError("Only active contracts can be cancelled.")

        self.status = ContractStatus.CANCELLED
        self.cancelled_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "cancelled_at",
                "updated_at",
            ]
        )
