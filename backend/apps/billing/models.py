"""
Modèles du module billing.

Invoice.amount_paid et balance_due sont calculés à la volée depuis les
Payment liés (jamais stockés en cache dénormalisé ici, contrairement à
StockLevel à l'Epic 8) : le volume de paiements par facture reste faible,
la simplicité l'emporte sur l'optimisation prématurée.
"""
from __future__ import annotations

from decimal import Decimal

from django.db import models
from django.utils import timezone

from apps.core.models import TenantBaseModel


class InvoiceStatus(models.TextChoices):
    DRAFT = "draft", "Brouillon"
    ISSUED = "issued", "Émise"
    PARTIALLY_PAID = "partially_paid", "Partiellement payée"
    PAID = "paid", "Payée"
    CANCELLED = "cancelled", "Annulée"


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Espèces"
    BANK_TRANSFER = "bank_transfer", "Virement bancaire"
    CHECK = "check", "Chèque"
    MOBILE_PAYMENT = "mobile_payment", "Paiement mobile"
    OTHER = "other", "Autre"


class Invoice(TenantBaseModel):
    """Une facture émise à un client, optionnellement issue d'une commande de vente."""

    invoice_number = models.CharField(max_length=20, db_index=True, editable=False)
    customer = models.ForeignKey("partners.Partner", on_delete=models.PROTECT, related_name="invoices")
    sales_order = models.ForeignKey(
        "sales.SalesOrder", on_delete=models.PROTECT, null=True, blank=True, related_name="invoices"
    )
    status = models.CharField(max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT)

    issue_date = models.DateField()
    due_date = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ["-issue_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["cooperative", "invoice_number"], name="unique_invoice_number_per_cooperative"),
        ]
        indexes = [models.Index(fields=["cooperative", "status"])]

    def __str__(self) -> str:
        return f"{self.invoice_number} — {self.customer.name}"

    @property
    def total_amount(self) -> Decimal:
        return sum((line.line_total for line in self.lines.all()), Decimal("0"))

    @property
    def amount_paid(self) -> Decimal:
        return sum((p.amount for p in self.payments.all()), Decimal("0"))

    @property
    def balance_due(self) -> Decimal:
        return self.total_amount - self.amount_paid

    @property
    def is_overdue(self) -> bool:
        return (
            self.status in {InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID}
            and self.due_date < timezone.localdate()
            and self.balance_due > 0
        )


class InvoiceLine(TenantBaseModel):
    """Une ligne de facture."""

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="invoice_lines")
    description = models.CharField(max_length=255, blank=True, help_text="Libellé optionnel, sinon le nom du produit est utilisé.")

    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Ligne de facture"
        verbose_name_plural = "Lignes de facture"
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name="invoice_line_quantity_positive"),
        ]

    def __str__(self) -> str:
        return f"{self.product} x{self.quantity}"

    @property
    def line_total(self) -> Decimal:
        return self.quantity * self.unit_price


class Payment(TenantBaseModel):
    """
    Un paiement reçu sur une facture — ledger immuable, comme
    StockMovement (Epic 8) : aucune vue d'update/delete n'existe.
    """

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    reference = models.CharField(max_length=100, blank=True, help_text="N° de chèque, référence de virement...")
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ["-payment_date", "-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="payment_amount_positive"),
        ]

    def __str__(self) -> str:
        return f"{self.amount} — {self.invoice.invoice_number}"
