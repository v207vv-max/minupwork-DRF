from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from contracts.models import Contract, ContractStatus
from projects.models import Project


class ReviewSentiment(models.TextChoices):
    POSITIVE = "positive", _("Positive")
    NEUTRAL = "neutral", _("Neutral")
    NEGATIVE = "negative", _("Negative")


class Review(models.Model):
    contract = models.OneToOneField(
        Contract,
        on_delete=models.CASCADE,
        related_name="review",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="written_reviews",
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_reviews",
    )

    rating = models.PositiveSmallIntegerField(
        help_text="Rating from 1 to 5.",
    )
    comment = models.TextField(
        help_text="Client's review comment about freelancer's work.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["rating"]),
            models.Index(fields=["client"]),
            models.Index(fields=["freelancer"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["freelancer", "rating"]),
        ]

    def __str__(self):
        return f"Review #{self.id} | {self.freelancer.username} | {self.rating}/5"

    def clean(self):
        super().clean()

        if self.comment:
            self.comment = self.comment.strip()

        if self.rating < 1 or self.rating > 5:
            raise ValidationError({"rating": "Rating must be between 1 and 5."})

        if not self.comment:
            raise ValidationError({"comment": "Comment cannot be empty."})

        if len(self.comment) < 10:
            raise ValidationError(
                {"comment": "Comment must contain at least 10 characters."}
            )

        if not self.contract_id or not self.project_id or not self.client_id or not self.freelancer_id:
            return

        if self.contract.status != ContractStatus.FINISHED:
            raise ValidationError("Review can only be created for a finished contract.")

        if self.contract.project != self.project:
            raise ValidationError("Project must match the contract project.")

        if self.contract.client != self.client:
            raise ValidationError("Client must match the contract client.")

        if self.contract.freelancer != self.freelancer:
            raise ValidationError("Freelancer must match the contract freelancer.")

        if getattr(self.client, "role", None) != "client":
            raise ValidationError("Only clients can write reviews.")

        if getattr(self.freelancer, "role", None) != "freelancer":
            raise ValidationError("Review can only be written for a freelancer.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def sentiment(self):
        if self.rating >= 4:
            return ReviewSentiment.POSITIVE
        if self.rating == 3:
            return ReviewSentiment.NEUTRAL
        return ReviewSentiment.NEGATIVE

    @property
    def is_positive(self):
        return self.rating >= 4

    @property
    def short_comment(self):
        if len(self.comment) <= 60:
            return self.comment
        return f"{self.comment[:57]}..."
