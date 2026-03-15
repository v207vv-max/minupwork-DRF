from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from bids.models import BidStatus
from projects.models import ProjectStatus

from .models import Contract, ContractStatus

@transaction.atomic
def create_contract_from_bid(*, bid):

    from chat.services import create_conversation_for_contract

    project = bid.project

    if bid.status != BidStatus.ACCEPTED:
        raise ValidationError("Contract can only be created from an accepted bid.")

    if project.status != ProjectStatus.IN_PROGRESS:
        raise ValidationError("Project must be in progress to create a contract.")

    if hasattr(project, "contract"):
        raise ValidationError("This project already has a contract.")

    if hasattr(bid, "contract"):
        raise ValidationError("This bid already has a contract.")

    contract = Contract.objects.create(
        project=project,
        bid=bid,
        client=project.client,
        freelancer=bid.freelancer,
        agreed_price=bid.price,
        status=ContractStatus.ACTIVE,
        started_at=timezone.now(),
    )

    create_conversation_for_contract(contract=contract)

    return contract


@transaction.atomic
def finish_contract(*, contract, client):
    """
    Finish active contract and complete the project.
    """

    if contract.client != client:
        raise ValidationError("You can finish only your own contracts.")

    if not contract.is_active:
        raise ValidationError("Only active contracts can be finished.")

    contract.mark_finished()

    project = contract.project
    project.status = ProjectStatus.COMPLETED
    project.is_active = False
    project.save(update_fields=["status", "is_active", "updated_at"])

    return contract


@transaction.atomic
def cancel_contract(*, contract, client):
    """
    Cancel active contract and cancel the project.
    """

    if contract.client != client:
        raise ValidationError("You can cancel only your own contracts.")

    if not contract.is_active:
        raise ValidationError("Only active contracts can be cancelled.")

    contract.mark_cancelled()

    project = contract.project
    project.status = ProjectStatus.CANCELLED
    project.is_active = False
    project.save(update_fields=["status", "is_active", "updated_at"])

    return contract