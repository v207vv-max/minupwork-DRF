from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from projects.models import ProjectStatus

from .models import Bid, BidStatus
from contracts.services import create_contract_from_bid


def create_bid(*, project, freelancer, proposal, price, delivery_time_days):


    if getattr(freelancer, "role", None) != "freelancer":
        raise ValidationError(_("Only freelancers can create bids."))

    if project.client == freelancer:
        raise ValidationError(_("You cannot bid on your own project."))

    if project.status != ProjectStatus.OPEN:
        raise ValidationError(_("You can only bid on open projects."))

    if not project.is_active:
        raise ValidationError(_("You cannot bid on an inactive project."))

    if Bid.objects.filter(project=project, freelancer=freelancer).exists():
        raise ValidationError(_("You have already submitted a bid for this project."))

    return Bid.objects.create(
        project=project,
        freelancer=freelancer,
        proposal=proposal.strip(),
        price=price,
        delivery_time_days=delivery_time_days,
    )


@transaction.atomic
def accept_bid(*, bid, client):
    from contracts.services import create_contract_from_bid

    project = bid.project

    if project.client != client:
        raise ValidationError(_("You can accept bids only for your own projects."))

    if project.status != ProjectStatus.OPEN:
        raise ValidationError(_("Bids can only be accepted for open projects."))

    if not project.is_active:
        raise ValidationError(_("This project is inactive."))

    if bid.status != BidStatus.PENDING:
        raise ValidationError(_("Only pending bids can be accepted."))

    bid.status = BidStatus.ACCEPTED
    bid.save(update_fields=["status", "updated_at"])

    Bid.objects.filter(
        project=project,
        status=BidStatus.PENDING,
    ).exclude(pk=bid.pk).update(
        status=BidStatus.REJECTED,
    )

    project.status = ProjectStatus.IN_PROGRESS
    project.save(update_fields=["status", "updated_at"])

    create_contract_from_bid(bid=bid)

    return bid


def update_bid(*, bid, freelancer, proposal, price, delivery_time_days):


    if bid.freelancer != freelancer:
        raise ValidationError(_("You can update only your own bid."))

    if bid.status != BidStatus.PENDING:
        raise ValidationError(_("Only pending bids can be updated."))

    bid.proposal = proposal
    bid.price = price
    bid.delivery_time_days = delivery_time_days
    bid.save()

    return bid


def withdraw_bid(*, bid, freelancer):


    if bid.freelancer != freelancer:
        raise ValidationError(_("You can withdraw only your own bid."))

    if bid.status != BidStatus.PENDING:
        raise ValidationError(_("Only pending bids can be withdrawn."))

    bid.status = BidStatus.WITHDRAWN
    bid.save(update_fields=["status", "updated_at"])

    return bid


def reject_bid(*, bid, client):


    if bid.project.client != client:
        raise ValidationError(_("You can reject bids only for your own projects."))

    if bid.status != BidStatus.PENDING:
        raise ValidationError(_("Only pending bids can be rejected."))

    bid.status = BidStatus.REJECTED
    bid.save(update_fields=["status", "updated_at"])

    return bid
