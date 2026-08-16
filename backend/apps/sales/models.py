"""
Modèles du module sales — miroir de apps.purchases, avec les nuances
propres à la vente : client (is_customer), contrôle d'encours, sortie de
stock (au lieu d'entrée) à la livraison.
"""

from __future__ import annotations

from decimal import Decimal

from django.db import models

from apps.core.models import TenantBaseModel


class SalesOrderStatus(models.TextChoices):
    DRAFT = "draft", "Brouillon"
    CONFIRMED = "confirmed", "Confirmée"
    PARTIALLY_DELIVERED = "partially_delivered", "Partiellement livrée"
    DELIVERED = "delivered", "Livrée"
    CANCELLED = "cancelled", "Annulée"


class SalesOrder(TenantBaseModel):
    """Une commande de vente à un client."""

    order_number = models.CharField(max_length=20, db_index=True, editable=False)
    customer = models.ForeignKey(
        "partners.Partner", on_delete=models.PROTECT, related_name="sales_orders"
    )
    warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        on_delete=models.PROTECT,
        related_name="sales_orders",
        help_text="Entrepôt source des marchandises livrées.",
    )
    status = models.CharField(
        max_length=20, choices=SalesOrderStatus.choices, default=SalesOrderStatus.DRAFT
    )

    order_date = models.DateField()
    expected_delivery_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Commande de vente"
        verbose_name_plural = "Commandes de vente"
        ordering = ["-order_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["cooperative", "order_number"],
                name="unique_sales_order_number_per_cooperative",
            ),
        ]
        indexes = [models.Index(fields=["cooperative", "status"])]

    def __str__(self) -> str:
        return f"{self.order_number} — {self.customer.name}"

    @property
    def total_amount(self) -> Decimal:
        return sum((line.line_total for line in self.lines.all()), Decimal("0"))

    @property
    def is_fully_delivered(self) -> bool:
        lines = list(self.lines.all())
        return bool(lines) and all(
            line.quantity_delivered >= line.quantity_ordered for line in lines
        )

    @property
    def has_any_delivery(self) -> bool:
        return any(line.quantity_delivered > 0 for line in self.lines.all())


class SalesOrderLine(TenantBaseModel):
    """Une ligne de produit au sein d'une commande de vente."""

    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.PROTECT, related_name="sales_order_lines"
    )

    quantity_ordered = models.DecimalField(max_digits=14, decimal_places=3)
    quantity_delivered = models.DecimalField(max_digits=14, decimal_places=3, default=Decimal("0"))
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Ligne de commande de vente"
        verbose_name_plural = "Lignes de commande de vente"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity_ordered__gt=0),
                name="sales_line_quantity_ordered_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity_delivered__gte=0)
                & models.Q(quantity_delivered__lte=models.F("quantity_ordered")),
                name="sales_line_delivered_within_ordered",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product} x{self.quantity_ordered}"

    @property
    def line_total(self) -> Decimal:
        return self.quantity_ordered * self.unit_price

    @property
    def quantity_remaining(self) -> Decimal:
        return self.quantity_ordered - self.quantity_delivered
