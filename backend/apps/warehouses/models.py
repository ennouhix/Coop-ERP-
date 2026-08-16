"""
Modèle Warehouse — lieux de stockage physiques de la coopérative.
"""

from __future__ import annotations

from django.db import models

from apps.cooperatives.validators import phone_validator
from apps.core.models import TenantBaseModel


class Warehouse(TenantBaseModel):
    """Un entrepôt ou point de stockage de la coopérative."""

    code = models.CharField(max_length=20, db_index=True, editable=False)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500, blank=True)
    city = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, validators=[phone_validator])

    manager = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_warehouses",
    )
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Entrepôt"
        verbose_name_plural = "Entrepôts"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["cooperative", "code"], name="unique_warehouse_code_per_cooperative"
            ),
        ]

    def save(self, *args, **kwargs):
        """Génère automatiquement un code si non défini."""
        if not self.code and self.cooperative_id:
            # Évite l'import circulaire
            from apps.warehouses.services import generate_warehouse_code

            self.code = generate_warehouse_code(self.cooperative)

            # Si c'est le premier entrepôt, le définir comme défaut
            if not Warehouse.all_objects.filter(cooperative=self.cooperative).exists():
                self.is_default = True

        super().save(*args, **kwargs)

    # def __str__(self) -> str:
    #   return f"{self.code} — {self.name}"
