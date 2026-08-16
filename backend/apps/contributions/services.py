"""
Logique métier du module contributions.
"""

from __future__ import annotations

import logging

from django.db import transaction
from django.utils import timezone

from apps.contributions.models import Contribution, ContributionStatus
from apps.cooperatives.models import Cooperative

logger = logging.getLogger(__name__)


@transaction.atomic
def create_contribution(*, cooperative: Cooperative, **fields) -> Contribution:
    contribution = Contribution.objects.create(cooperative=cooperative, **fields)

    try:
        from apps.cooperatives.notifications import notify_contribution_pending
        notify_contribution_pending(contribution)
    except Exception:
        logger.warning(
            "Erreur notification cotisation %s", contribution.id, exc_info=True
        )

    return contribution


@transaction.atomic
def mark_contribution_paid(*, contribution: Contribution) -> Contribution:
    """Marque un apport comme payé (avec sa date de paiement)."""
    contribution.status = ContributionStatus.PAID
    contribution.payment_date = timezone.localdate()
    contribution.save(update_fields=["status", "payment_date", "updated_at"])
    return contribution
