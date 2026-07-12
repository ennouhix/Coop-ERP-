"""
Modèles du module inventory.

StockMovement = ledger immuable (source de vérité, jamais modifié/supprimé).
StockLevel = cache dénormalisé de la quantité actuelle, mis à jour de façon
atomique par apps.inventory.services à chaque mouvement.
"""
from __future__ import annotations

from decimal import Decimal

from django.db import models

from apps.core.models import TenantBaseModel


class StockMovementType(models.TextChoices):
    IN = "in", "Entrée"
    OUT = "out", "Sortie"
    TRANSFER = "transfer", "Transfert"


class StockMovementReason(models.TextChoices):
    PURCHASE = "purchase", "Achat"
    SALE = "sale", "Vente"
    ADJUSTMENT = "adjustment", "Ajustement d'inventaire"
    TRANSFER = "transfer", "Transfert inter-entrepôts"
    RETURN_CUSTOMER = "return_customer", "Retour client"
    RETURN_SUPPLIER = "return_supplier", "Retour fournisseur"
    LOSS = "loss", "Perte/casse"
    INITIAL = "initial", "Stock initial"
    OTHER = "other", "Autre"


class StockLevel(TenantBaseModel):
    """Quantité actuelle d'un produit dans un entrepôt (cache dénormalisé)."""

    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="stock_levels")
    warehouse = models.ForeignKey("warehouses.Warehouse", on_delete=models.PROTECT, related_name="stock_levels")
    quantity = models.DecimalField(max_digits=14, decimal_places=3, default=Decimal("0"))

    class Meta:
        verbose_name = "Niveau de stock"
        verbose_name_plural = "Niveaux de stock"
        ordering = ["product__sku", "warehouse__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["cooperative", "product", "warehouse"], name="unique_stock_level_per_product_warehouse"
            ),
            models.CheckConstraint(condition=models.Q(quantity__gte=0), name="stock_level_quantity_never_negative"),
        ]
        indexes = [models.Index(fields=["cooperative", "product"])]

    def __str__(self) -> str:
        return f"{self.product} @ {self.warehouse} = {self.quantity}"


class StockMovement(TenantBaseModel):
    """
    Un mouvement de stock — LEDGER IMMUABLE. Aucune vue d'update/delete
    n'existe pour ce modèle : voir apps/inventory/services.py pour la
    logique de création, et apps/inventory/views.py pour constater
    l'absence volontaire de PATCH/DELETE.
    """

    movement_type = models.CharField(max_length=10, choices=StockMovementType.choices)
    reason = models.CharField(max_length=20, choices=StockMovementReason.choices, default=StockMovementReason.OTHER)

    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="stock_movements")
    warehouse = models.ForeignKey(
        "warehouses.Warehouse", on_delete=models.PROTECT, related_name="stock_movements_out",
        help_text="Entrepôt source (IN/OUT/ADJUSTMENT) ou entrepôt de départ (TRANSFER).",
    )
    destination_warehouse = models.ForeignKey(
        "warehouses.Warehouse", on_delete=models.PROTECT, null=True, blank=True,
        related_name="stock_movements_in", help_text="Renseigné uniquement pour un TRANSFER.",
    )

    quantity = models.DecimalField(max_digits=14, decimal_places=3, help_text="Toujours positive ; le sens est donné par movement_type.")
    reference = models.CharField(max_length=100, blank=True, help_text="Ex: numéro de bon de réception.")
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name="stock_movement_quantity_positive"),
        ]
        indexes = [
            models.Index(fields=["cooperative", "product", "warehouse"]),
            models.Index(fields=["cooperative", "movement_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_movement_type_display()} {self.quantity} — {self.product}"
