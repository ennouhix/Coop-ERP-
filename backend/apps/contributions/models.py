"""
Modèle Contribution — les apports des membres (produits de la coopérative).

Dans une coopérative agricole marocaine, les membres livrent leur production
(lait, argan, olives, safran, dattes...) à la coopérative qui la valorise
puis leur verse le montant. Ce modèle suit chaque livraison : quantité,
prix de reprise, montant dû, et son état de paiement.
"""

from __future__ import annotations

from decimal import Decimal

from django.db import models
from django.utils import timezone

from apps.core.models import TenantBaseModel


class ContributionStatus(models.TextChoices):
    PENDING = "pending", "En attente de paiement"
    PAID = "paid", "Payée"


class Contribution(TenantBaseModel):
    """Un apport / une livraison de production par un membre."""

    member = models.ForeignKey(
        "members.Member", on_delete=models.PROTECT, related_name="contributions"
    )
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.PROTECT, related_name="contributions"
    )
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Prix de reprise unitaire (MAD)."
    )
    contribution_date = models.DateField(default=timezone.localdate)
    campaign = models.CharField(
        max_length=100, blank=True, help_text="Campagne agricole, ex: 2026."
    )
    status = models.CharField(
        max_length=10, choices=ContributionStatus.choices, default=ContributionStatus.PENDING
    )
    payment_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Apport"
        verbose_name_plural = "Apports"
        ordering = ["-contribution_date"]
        indexes = [
            models.Index(fields=["cooperative", "status"]),
            models.Index(fields=["cooperative", "member"]),
        ]

    def __str__(self) -> str:
        return f"Apport {self.member} — {self.quantity} x {self.product}"

    @property
    def total_amount(self) -> Decimal:
        return self.quantity * self.unit_price
