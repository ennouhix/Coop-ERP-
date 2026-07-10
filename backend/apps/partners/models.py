"""
Modèle Partner — tiers commerciaux (clients ET/OU fournisseurs).

Un seul modèle plutôt que deux (Client, Supplier) séparés : un tiers peut
cumuler les deux rôles (ex: une coopérative partenaire qui achète et vend),
et les attributs (identité, contact, conditions de paiement) sont
identiques dans les deux cas. Dupliquer en deux modèles aurait signifié
dupliquer aussi toute la logique de code séquentiel, validation ICE, etc.
"""
from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TenantBaseModel
from apps.cooperatives.validators import ice_validator, phone_validator


class PartnerKind(models.TextChoices):
    INDIVIDUAL = "individual", "Personne physique"
    COMPANY = "company", "Personne morale"


class PartnerStatus(models.TextChoices):
    ACTIVE = "active", "Actif"
    INACTIVE = "inactive", "Inactif"


class Partner(TenantBaseModel):
    """Un tiers commercial : client, fournisseur, ou les deux."""

    code = models.CharField(max_length=20, db_index=True, editable=False)

    is_customer = models.BooleanField(default=False)
    is_supplier = models.BooleanField(default=False)

    partner_kind = models.CharField(max_length=15, choices=PartnerKind.choices, default=PartnerKind.INDIVIDUAL)
    name = models.CharField(max_length=255)
    ice = models.CharField("ICE", max_length=15, blank=True, validators=[ice_validator])

    phone_number = models.CharField(max_length=20, validators=[phone_validator])
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=500, blank=True)
    city = models.CharField(max_length=100, blank=True)

    payment_terms_days = models.PositiveSmallIntegerField(
        default=0, help_text="Délai de paiement en jours (0 = comptant)."
    )
    credit_limit = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Encours maximum autorisé pour ce client (0 = pas de limite définie).",
    )

    status = models.CharField(max_length=10, choices=PartnerStatus.choices, default=PartnerStatus.ACTIVE)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Partenaire"
        verbose_name_plural = "Partenaires"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["cooperative", "code"], name="unique_partner_code_per_cooperative"),
            models.UniqueConstraint(
                fields=["cooperative", "ice"],
                condition=~models.Q(ice=""),
                name="unique_partner_ice_per_cooperative",
            ),
        ]
        indexes = [
            models.Index(fields=["cooperative", "is_customer"]),
            models.Index(fields=["cooperative", "is_supplier"]),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"

    def clean(self) -> None:
        super().clean()
        if not self.is_customer and not self.is_supplier:
            raise ValidationError("Un partenaire doit être client et/ou fournisseur.")
