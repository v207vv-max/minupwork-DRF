from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from contracts.models import ContractStatus

from .models import Conversation, Message


@transaction.atomic
def create_conversation_for_contract(*, contract):


    if hasattr(contract, "conversation"):
        raise ValidationError(_("Conversation for this contract already exists."))

    conversation = Conversation.objects.create(
        contract=contract,
        client=contract.client,
        freelancer=contract.freelancer,
    )

    return conversation


@transaction.atomic
def send_message(*, conversation, sender, text="", image=None):


    if not conversation.has_participant(sender):
        raise ValidationError(_("Only conversation participants can send messages."))

    if not conversation.can_send_messages:
        raise ValidationError(_("You cannot send messages in this conversation."))

    text = (text or "").strip()

    if not text and not image:
        raise ValidationError(_("Message must contain text or image."))

    message = Message.objects.create(
        conversation=conversation,
        sender=sender,
        text=text,
        image=image,
    )

    return message


@transaction.atomic
def mark_conversation_as_read(*, conversation, user):


    if not conversation.has_participant(user):
        raise ValidationError(_("Only conversation participants can access this chat."))

    conversation.messages.filter(
        is_read=False,
    ).exclude(
        sender=user,
    ).update(is_read=True)

    return conversation
