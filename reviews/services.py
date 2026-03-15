from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from contracts.models import ContractStatus

from .models import Review


@transaction.atomic
def create_review(*, contract, client, rating, comment):


    if contract.client != client:
        raise ValidationError(_("You can create a review only for your own contract."))

    if contract.status != ContractStatus.FINISHED:
        raise ValidationError(_("Review can only be created for a finished contract."))

    if hasattr(contract, "review"):
        raise ValidationError(_("Review for this contract already exists."))

    review = Review.objects.create(
        contract=contract,
        project=contract.project,
        client=contract.client,
        freelancer=contract.freelancer,
        rating=rating,
        comment=comment,
    )

    return review


@transaction.atomic
def update_review(*, review, client, rating, comment):


    if review.client != client:
        raise ValidationError(_("You can update only your own review."))

    if review.contract.status != ContractStatus.FINISHED:
        raise ValidationError(_("You can update review only for a finished contract."))

    review.rating = rating
    review.comment = comment
    review.save()

    return review
