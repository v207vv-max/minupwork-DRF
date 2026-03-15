from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ProjectStatus(models.TextChoices):
    OPEN = "open", _("Open")
    IN_PROGRESS = "in_progress", _("In progress")
    COMPLETED = "completed", _("Completed")
    CANCELLED = "cancelled", _("Cancelled")


class Project(models.Model):
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_projects",
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    deadline = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.OPEN,
    )
    skills_required = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Optional. Example: Python, Django, DRF, PostgreSQL"),
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["deadline"]),
            models.Index(fields=["client"]),
            models.Index(fields=["client", "status"]),
        ]

    def __str__(self):
        return f"{self.title} | {self.client.username}"

    def clean(self):
        super().clean()

        if self.client_id and getattr(self.client, "role", None) != "client":
            raise ValidationError({"client": _("Only clients can create projects.")})

        if self.title:
            self.title = self.title.strip()

        if self.skills_required:
            self.skills_required = self.skills_required.strip()

        if not self.title:
            raise ValidationError({"title": _("Title cannot be empty.")})

        if self.budget is None or self.budget <= 0:
            raise ValidationError({"budget": _("Budget must be greater than 0.")})

        if self.deadline and self.deadline < timezone.localdate():
            raise ValidationError({"deadline": _("Deadline cannot be in the past.")})

        if self.status in [ProjectStatus.COMPLETED, ProjectStatus.CANCELLED] and self.is_active:
            raise ValidationError(
                {"is_active": _("Completed or cancelled project cannot remain active.")}
            )

    def save(self, *args, **kwargs):
        if self.status in [ProjectStatus.COMPLETED, ProjectStatus.CANCELLED]:
            self.is_active = False

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_open(self):
        return self.status == ProjectStatus.OPEN

    @property
    def can_receive_bids(self):
        return self.status == ProjectStatus.OPEN and self.is_active

    @property
    def is_editable(self):
        return self.status == ProjectStatus.OPEN
