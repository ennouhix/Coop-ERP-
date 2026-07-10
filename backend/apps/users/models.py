"""
Modèle Invitation — permet à un OWNER/ADMIN d'inviter un collègue par
email avec un rôle prédéfini, sans que celui-ci ait besoin de connaître
un mot de passe temporaire (plus sûr, expérience plus fluide).
"""
from __future__ import annotations

import secrets

from django.db import models
from django.utils import timezone

from apps.authentication.models import UserRole
from apps.core.models import TenantBaseModel

INVITATION_VALIDITY_DAYS = 7


def generate_invitation_token() -> str:
    """Token opaque à usage unique, non devinable (256 bits d'entropie)."""
    return secrets.token_urlsafe(32)


def default_invitation_expiry() -> "timezone.datetime":
    return timezone.now() + timezone.timedelta(days=INVITATION_VALIDITY_DAYS)


class InvitationStatus(models.TextChoices):
    PENDING = "pending", "En attente"
    ACCEPTED = "accepted", "Acceptée"
    CANCELLED = "cancelled", "Annulée"


class Invitation(TenantBaseModel):
    """Invitation d'un email à rejoindre la coopérative avec un rôle donné."""

    email = models.EmailField(db_index=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.STAFF)
    token = models.CharField(max_length=64, unique=True, default=generate_invitation_token, editable=False)
    status = models.CharField(max_length=10, choices=InvitationStatus.choices, default=InvitationStatus.PENDING)
    expires_at = models.DateTimeField(default=default_invitation_expiry)
    accepted_at = models.DateTimeField(null=True, blank=True)
    invited_by = models.ForeignKey(
        "authentication.User", on_delete=models.SET_NULL, null=True, related_name="sent_invitations"
    )

    class Meta:
        indexes = [models.Index(fields=["cooperative", "email", "status"])]
        constraints = [
            # Une seule invitation PENDING active à la fois par (coopérative, email) —
            # appliqué aussi au niveau applicatif dans services.py pour un message
            # d'erreur clair, cette contrainte est le filet de sécurité en base.
            models.UniqueConstraint(
                fields=["cooperative", "email"],
                condition=models.Q(status="pending"),
                name="unique_pending_invitation_per_email",
            )
        ]

    def __str__(self) -> str:
        return f"Invitation({self.email}, {self.role}, {self.status})"

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at
