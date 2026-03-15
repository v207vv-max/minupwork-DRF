from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from projects.models import Project, ProjectStatus


class BidStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    ACCEPTED = "accepted", _("Accepted")
    REJECTED = "rejected", _("Rejected")
    WITHDRAWN = "withdrawn", _("Withdrawn")


class Bid(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="bids",
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="freelancer_bids",
    )
    proposal = models.TextField(
        help_text="Freelancer's offer message for the project.",
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    delivery_time_days = models.PositiveIntegerField(
        help_text="Estimated number of days to complete the work.",
    )
    status = models.CharField(
        max_length=20,
        choices=BidStatus.choices,
        default=BidStatus.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["project"]),
            models.Index(fields=["freelancer"]),
            models.Index(fields=["project", "status"]),
            models.Index(fields=["freelancer", "status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "freelancer"],
                name="unique_bid_per_project_per_freelancer",
            )
        ]

    def __str__(self):
        return f"{self.project.title} | {self.freelancer.username} | {self.status}"

    def clean(self):
        super().clean()

        if self.freelancer_id and getattr(self.freelancer, "role", None) != "freelancer":
            raise ValidationError({"freelancer": "Only freelancers can create bids."})

        if self.project_id and self.freelancer_id and self.project.client_id == self.freelancer_id:
            raise ValidationError({"freelancer": "You cannot bid on your own project."})

        if self.project_id:
            if self.project.status != ProjectStatus.OPEN:
                raise ValidationError({"project": "You can only bid on open projects."})

            if not self.project.is_active:
                raise ValidationError({"project": "You cannot bid on an inactive project."})

        if self.proposal:
            self.proposal = self.proposal.strip()

        if not self.proposal:
            raise ValidationError({"proposal": "Proposal cannot be empty."})

        if self.price is None or self.price <= 0:
            raise ValidationError({"price": "Price must be greater than 0."})

        if self.delivery_time_days < 1:
            raise ValidationError(
                {"delivery_time_days": "Delivery time must be at least 1 day."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_pending(self):
        return self.status == BidStatus.PENDING

    @property
    def is_accepted(self):
        return self.status == BidStatus.ACCEPTED

    @property
    def is_rejected(self):
        return self.status == BidStatus.REJECTED

    @property
    def is_withdrawn(self):
        return self.status == BidStatus.WITHDRAWN

    @property
    def is_editable(self):
        return self.status == BidStatus.PENDING

    @property
    def can_be_withdrawn(self):
        return self.status == BidStatus.PENDING
