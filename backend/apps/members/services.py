"""
Logique métier du module members.

Le point sensible est la génération du numéro d'adhérent : deux requêtes
concurrentes ne doivent jamais se voir attribuer le même numéro. On utilise
un verrou pessimiste (select_for_update) sur la coopérative le temps de
calculer le prochain numéro, pour rendre l'opération atomique même sous
forte concurrence (plusieurs guichets d'enregistrement simultanés).
"""
from __future__ import annotations

from django.db import transaction

from apps.cooperatives.models import Cooperative
from apps.members.models import Member

MEMBER_NUMBER_PADDING = 4  # ARG-0001, ARG-0002...


def _cooperative_prefix(cooperative: Cooperative) -> str:
    """Préfixe basé sur le slug, ex: 'argane-sud' -> 'ARG'."""
    letters = "".join(ch for ch in cooperative.slug.upper() if ch.isalpha())
    return (letters[:3] or "COOP")


@transaction.atomic
def generate_member_number(cooperative: Cooperative) -> str:
    """
    Verrouille la ligne Cooperative le temps de lire le dernier numéro
    attribué et d'en générer un nouveau, empêchant toute collision entre
    deux enregistrements simultanés.
    """
    Cooperative.objects.select_for_update().get(pk=cooperative.pk)

    prefix = _cooperative_prefix(cooperative)
    last_member = (
        Member.all_objects.filter(cooperative=cooperative, member_number__startswith=f"{prefix}-")
        .order_by("-member_number")
        .first()
    )

    if last_member is None:
        next_sequence = 1
    else:
        try:
            next_sequence = int(last_member.member_number.split("-")[-1]) + 1
        except ValueError:
            next_sequence = Member.all_objects.filter(cooperative=cooperative).count() + 1

    return f"{prefix}-{str(next_sequence).zfill(MEMBER_NUMBER_PADDING)}"


@transaction.atomic
def create_member(*, cooperative: Cooperative, **fields) -> Member:
    member_number = generate_member_number(cooperative)
    return Member.objects.create(cooperative=cooperative, member_number=member_number, **fields)
