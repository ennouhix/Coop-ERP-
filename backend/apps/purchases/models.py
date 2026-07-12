"""
Modèles du module purchases.

PurchaseOrderLine.quantity_received progresse au fil des réceptions
(potentiellement partielles). La réception réelle passe TOUJOURS par
apps.purchases.services, qui orchestre la mise à jour de la ligne ET la
création du StockMovement correspondant (Epic 8) dans la même transaction.
"""
from __future__ import annotations

from decimal import Decimal

from django.db import models

from apps.core.models import TenantBaseModel


class PurchaseOrderStatus(models.TextChoices):
    DRAFT = "draft", "Brouillon"
    CONFIRMED = "confirmed", "Confirmée"
    PARTIALLY_RECEIVED = "partially_received", "Partiellement reçue"
    RECEIVED = "received", "Reçue"
    CANCELLED = "cancelled", "Annulée"


class PurchaseOrder(TenantBaseModel):
    """Une commande d'achat auprès d'un fournisseur."""

    order_number = models.CharField(max_length=20, db_index=True, editable=False)
    supplier = models.ForeignKey("partners.Partner", on_delete=models.PROTECT, related_name="purchase_orders")
    warehouse = models.ForeignKey(
        "warehouses.Warehouse", on_delete=models.PROTECT, related_name="purchase_orders",
        help_text="Entrepôt de destination des marchandises reçues.",
    )
    status = models.CharField(max_length=20, choices=PurchaseOrderStatus.choices, default=PurchaseOrderStatus.DRAFT)

    order_date = models.DateField()
    expected_delivery_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Commande d'achat"
        verbose_name_plural = "Commandes d'achat"
        ordering = ["-order_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["cooperative", "order_number"], name="unique_purchase_order_number_per_cooperative"),
        ]
        indexes = [models.Index(fields=["cooperative", "status"])]

    def __str__(self) -> str:
        return f"{self.order_number} — {self.supplier.name}"

    @property
    def total_amount(self) -> Decimal:
        return sum((line.line_total for line in self.lines.all()), Decimal("0"))

    @property
    def is_fully_received(self) -> bool:
        lines = list(self.lines.all())
        return bool(lines) and all(line.quantity_received >= line.quantity_ordered for line in lines)

    @property
    def has_any_receipt(self) -> bool:
        return any(line.quantity_received > 0 for line in self.lines.all())


class PurchaseOrderLine(TenantBaseModel):
    """Une ligne de produit au sein d'une commande d'achat."""

    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="purchase_order_lines")

    quantity_ordered = models.DecimalField(max_digits=14, decimal_places=3)
    quantity_received = models.DecimalField(max_digits=14, decimal_places=3, default=Decimal("0"))
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Ligne de commande d'achat"
        verbose_name_plural = "Lignes de commande d'achat"
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity_ordered__gt=0), name="purchase_line_quantity_ordered_positive"),
            models.CheckConstraint(
                condition=models.Q(quantity_received__gte=0) & models.Q(quantity_received__lte=models.F("quantity_ordered")),
                name="purchase_line_received_within_ordered",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product} x{self.quantity_ordered}"

    @property
    def line_total(self) -> Decimal:
        return self.quantity_ordered * self.unit_price

    @property
    def quantity_remaining(self) -> Decimal:
        return self.quantity_ordered - self.quantity_received
