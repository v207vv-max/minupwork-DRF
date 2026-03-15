from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from contracts.models import Contract, ContractStatus


class Conversation(models.Model):
    contract = models.OneToOneField(
        Contract,
        on_delete=models.CASCADE,
        related_name="conversation",
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_conversations",
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="freelancer_conversations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["client"]),
            models.Index(fields=["freelancer"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self):
        return f"Conversation #{self.id} | Contract #{self.contract_id}"

    def clean(self):
        super().clean()

        if not self.contract:
            raise ValidationError("Conversation must be linked to a contract.")

        if not self.client:
            raise ValidationError("Conversation must have a client.")

        if not self.freelancer:
            raise ValidationError("Conversation must have a freelancer.")

        if self.contract.client != self.client:
            raise ValidationError("Client must match the contract client.")

        if self.contract.freelancer != self.freelancer:
            raise ValidationError("Freelancer must match the contract freelancer.")

        if getattr(self.client, "role", None) != "client":
            raise ValidationError("Conversation client must have client role.")

        if getattr(self.freelancer, "role", None) != "freelancer":
            raise ValidationError("Conversation freelancer must have freelancer role.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def participants(self):
        return [self.client, self.freelancer]

    def has_participant(self, user):
        return user == self.client or user == self.freelancer

    @property
    def can_send_messages(self):
        return self.contract.status in {
            ContractStatus.ACTIVE,
            ContractStatus.FINISHED,
        }


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    text = models.TextField(
        blank=True,
        help_text="Optional text message.",
    )
    image = models.ImageField(
        upload_to="chat_images/",
        null=True,
        blank=True,
        help_text="Optional image attachment.",
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation"]),
            models.Index(fields=["sender"]),
            models.Index(fields=["is_read"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["conversation", "is_read"]),
        ]

    def __str__(self):
        return f"Message #{self.id} | Conversation #{self.conversation_id}"

    def clean(self):
        super().clean()

        if self.text:
            self.text = self.text.strip()

        if not self.text and not self.image:
            raise ValidationError("Message must contain text or image.")

        if not self.conversation_id or not self.sender_id:
            return

        if not self.conversation.has_participant(self.sender):
            raise ValidationError("Sender must be a participant of this conversation.")

        if self.conversation.contract.status == ContractStatus.CANCELLED:
            raise ValidationError("You cannot send messages in a cancelled contract chat.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        Conversation.objects.filter(pk=self.conversation_id).update(
            updated_at=self.updated_at
        )

    @property
    def has_image(self):
        return bool(self.image)

    @property
    def has_text(self):
        return bool(self.text)

    @property
    def short_text(self):
        if not self.text:
            return ""
        if len(self.text) <= 50:
            return self.text
        return f"{self.text[:47]}..."