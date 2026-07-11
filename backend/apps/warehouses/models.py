"""
Modèle Warehouse — lieux de stockage physiques de la coopérative.

Dimension consommée directement par le module Stock (Epic 8) : chaque
mouvement/quantité en stock sera rattaché à un entrepôt précis.
"""
from __future__ import annotations

from django.db import models

from apps.core.models import TenantBaseModel
from apps.cooperatives.validators import phone_validator


class Warehouse(TenantBaseModel):
    """Un entrepôt ou point de stockage de la coopérative."""

    code = models.CharField(max_length=20, db_index=True, editable=False)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500, blank=True)
    city = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, validators=[phone_validator])

    manager = models.ForeignKey(
        "authentication.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="managed_warehouses"
    )
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Entrepôt"
        verbose_name_plural = "Entrepôts"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["cooperative", "code"], name="unique_warehouse_code_per_cooperative"),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"
