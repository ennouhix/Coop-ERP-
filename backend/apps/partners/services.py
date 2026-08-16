"""
Logique métier du module partners.

Même stratégie de verrouillage que apps.members.services : select_for_update
sur la coopérative pour garantir l'unicité du code sous forte concurrence.
"""

from __future__ import annotations

from django.db import transaction

from apps.cooperatives.models import Cooperative
from apps.partners.models import Partner

CODE_PADDING = 4


@transaction.atomic
def generate_partner_code(cooperative: Cooperative) -> str:
    Cooperative.objects.select_for_update().get(pk=cooperative.pk)

    last_partner = (
        Partner.all_objects.filter(cooperative=cooperative, code__startswith="PART-")
        .order_by("-code")
        .first()
    )

    if last_partner is None:
        next_sequence = 1
    else:
        try:
            next_sequence = int(last_partner.code.split("-")[-1]) + 1
        except ValueError:
            next_sequence = Partner.all_objects.filter(cooperative=cooperative).count() + 1

    return f"PART-{str(next_sequence).zfill(CODE_PADDING)}"


@transaction.atomic
def create_partner(*, cooperative: Cooperative, **fields) -> Partner:
    code = generate_partner_code(cooperative)
    partner = Partner(cooperative=cooperative, code=code, **fields)
    partner.full_clean()  # déclenche Partner.clean() : au moins client ou fournisseur
    partner.save()
    return partner
