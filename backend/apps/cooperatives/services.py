"""
Logique métier de création de coopérative.

La création d'une coopérative et de son premier utilisateur (OWNER) doit
être atomique : on ne veut jamais d'une coopérative sans propriétaire, ni
d'un utilisateur OWNER sans coopérative valide derrière lui.
"""
from __future__ import annotations

from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.text import slugify

from apps.authentication.models import UserRole
from apps.cooperatives.models import Cooperative

User = get_user_model()


@dataclass(frozen=True)
class CooperativeRegistrationData:
    cooperative_name: str
    owner_email: str
    owner_password: str
    owner_first_name: str
    owner_last_name: str


def generate_unique_slug(name: str) -> str:
    """
    Génère un slug unique à partir du nom. En cas de collision (deux
    coopératives au nom identique ou très proche), ajoute un suffixe
    numérique incrémental plutôt que de faire échouer l'inscription.
    """
    base_slug = slugify(name)[:240] or "cooperative"
    slug = base_slug
    suffix = 1
    while Cooperative.objects.filter(slug=slug).exists():
        suffix += 1
        slug = f"{base_slug}-{suffix}"
    return slug


@transaction.atomic
def register_cooperative(data: CooperativeRegistrationData) -> tuple[Cooperative, "User"]:
    """
    Crée la coopérative puis son utilisateur OWNER dans la même transaction.
    Toute exception ici annule les deux créations (rollback complet).
    """
    cooperative = Cooperative.objects.create(
        name=data.cooperative_name,
        slug=generate_unique_slug(data.cooperative_name),
    )

    owner = User.objects.create_user(
        username=data.owner_email,  # pas de username séparé en V1, on réutilise l'email
        email=data.owner_email,
        password=data.owner_password,
        first_name=data.owner_first_name,
        last_name=data.owner_last_name,
        cooperative=cooperative,
        role=UserRole.OWNER,
    )

    return cooperative, owner
