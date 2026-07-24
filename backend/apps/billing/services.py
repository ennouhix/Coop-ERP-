"""
Logique métier du module billing.

record_payment() verrouille la facture le temps de vérifier que le
paiement ne dépasse pas le solde dû — même précaution de concurrence que
pour le stock (Epic 8) : deux paiements simultanés sur la même facture ne
doivent jamais pouvoir la faire passer en solde négatif.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from django.db import transaction

from apps.audit.services import log_activity
from apps.billing.models import Invoice, InvoiceLine, InvoiceStatus, Payment
from apps.cooperatives.models import Cooperative
from apps.partners.models import Partner
from apps.sales.models import SalesOrder, SalesOrderStatus

INVOICE_NUMBER_PADDING = 5


class InvoiceError(Exception):
    """Erreur métier générique (message destiné à être affiché tel quel)."""


class PaymentError(Exception):
    """Erreur métier liée à l'enregistrement d'un paiement."""


@transaction.atomic
def _generate_invoice_number(cooperative: Cooperative) -> str:
    Cooperative.objects.select_for_update().get(pk=cooperative.pk)

    last_invoice = (
        Invoice.all_objects.filter(cooperative=cooperative, invoice_number__startswith="FAC-")
        .order_by("-invoice_number")
        .first()
    )
    if last_invoice is None:
        next_sequence = 1
    else:
        try:
            next_sequence = int(last_invoice.invoice_number.split("-")[-1]) + 1
        except ValueError:
            next_sequence = Invoice.all_objects.filter(cooperative=cooperative).count() + 1

    return f"FAC-{str(next_sequence).zfill(INVOICE_NUMBER_PADDING)}"


def _default_due_date(customer: Partner, issue_date: date) -> date:
    return issue_date + timedelta(days=customer.payment_terms_days or 0)


@transaction.atomic
def create_manual_invoice(
    *, cooperative: Cooperative, customer: Partner, lines: list, actor,  # noqa: ANN001
    issue_date: date, due_date: Optional[date] = None, notes: str = "",
) -> Invoice:
    if not customer.is_customer:
        raise InvoiceError("Ce partenaire n'est pas enregistré comme client.")
    if not lines:
        raise InvoiceError("Une facture doit contenir au moins une ligne.")

    invoice = Invoice.objects.create(
        cooperative=cooperative,
        invoice_number=_generate_invoice_number(cooperative),
        customer=customer, sales_order=None,
        status=InvoiceStatus.DRAFT,
        issue_date=issue_date, due_date=due_date or _default_due_date(customer, issue_date),
        notes=notes, created_by=actor,
    )

    for line in lines:
        InvoiceLine.objects.create(
            cooperative=cooperative, invoice=invoice,
            product=line["product"], description=line.get("description", ""),
            quantity=line["quantity"], unit_price=line["unit_price"], created_by=actor,
        )

    return invoice


@transaction.atomic
def generate_invoice_from_sales_order(
    *, order: SalesOrder, actor, issue_date: date, due_date: Optional[date] = None,  # noqa: ANN001
) -> Invoice:
    if order.status not in {SalesOrderStatus.PARTIALLY_DELIVERED, SalesOrderStatus.DELIVERED}:
        raise InvoiceError("Seule une commande au moins partiellement livrée peut être facturée.")
    if order.invoices.exclude(status=InvoiceStatus.CANCELLED).exists():
        raise InvoiceError("Cette commande a déjà une facture active. Annulez-la avant d'en régénérer une.")

    delivered_lines = [line for line in order.lines.all() if line.quantity_delivered > 0]
    if not delivered_lines:
        raise InvoiceError("Aucune quantité livrée à facturer sur cette commande.")

    invoice = Invoice.objects.create(
        cooperative=order.cooperative,
        invoice_number=_generate_invoice_number(order.cooperative),
        customer=order.customer, sales_order=order,
        status=InvoiceStatus.DRAFT,
        issue_date=issue_date, due_date=due_date or _default_due_date(order.customer, issue_date),
        created_by=actor,
    )

    for line in delivered_lines:
        InvoiceLine.objects.create(
            cooperative=order.cooperative, invoice=invoice,
            product=line.product, quantity=line.quantity_delivered, unit_price=line.unit_price,
            created_by=actor,
        )

    return invoice


@transaction.atomic
def issue_invoice(*, invoice: Invoice, actor) -> Invoice:  # noqa: ANN001
    if invoice.status != InvoiceStatus.DRAFT:
        raise InvoiceError("Seule une facture en brouillon peut être émise.")
    if not invoice.lines.exists():
        raise InvoiceError("Impossible d'émettre une facture sans lignes.")

    invoice.status = InvoiceStatus.ISSUED
    invoice.updated_by = actor
    invoice.save(update_fields=["status", "updated_by"])

    log_activity(
        cooperative=invoice.cooperative, actor=actor, action="invoice.issued",
        target_type="Invoice", target_id=invoice.id, target_repr=invoice.invoice_number,
        metadata={"total_amount": str(invoice.total_amount)},
    )
    return invoice


@transaction.atomic
def cancel_invoice(*, invoice: Invoice, actor) -> Invoice:  # noqa: ANN001
    if invoice.status not in {InvoiceStatus.DRAFT, InvoiceStatus.ISSUED}:
        raise InvoiceError("Cette facture ne peut plus être annulée (déjà payée ou annulée).")
    if invoice.amount_paid > 0:
        raise InvoiceError("Impossible d'annuler une facture ayant déjà reçu un paiement.")

    invoice.status = InvoiceStatus.CANCELLED
    invoice.updated_by = actor
    invoice.save(update_fields=["status", "updated_by"])

    log_activity(
        cooperative=invoice.cooperative, actor=actor, action="invoice.cancelled",
        target_type="Invoice", target_id=invoice.id, target_repr=invoice.invoice_number,
    )
    return invoice


@transaction.atomic
def record_payment(
    *, invoice: Invoice, amount: Decimal, payment_date: date, actor,  # noqa: ANN001
    payment_method: str = "cash", reference: str = "", notes: str = "",
) -> Payment:
    # Verrouille la facture pendant tout le calcul du solde pour empêcher
    # deux paiements concurrents de faire passer le solde sous zéro.
    locked_invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)

    if locked_invoice.status not in {InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID}:
        raise PaymentError("Seule une facture émise peut recevoir un paiement.")
    if amount <= 0:
        raise PaymentError("Le montant du paiement doit être positif.")
    if amount > locked_invoice.balance_due:
        raise PaymentError(
            f"Le paiement ({amount}) dépasse le solde restant dû ({locked_invoice.balance_due})."
        )

    payment = Payment.objects.create(
        cooperative=locked_invoice.cooperative, invoice=locked_invoice, amount=amount,
        payment_date=payment_date, payment_method=payment_method, reference=reference,
        notes=notes, created_by=actor,
    )

    locked_invoice.refresh_from_db()
    locked_invoice.status = (
        InvoiceStatus.PAID if locked_invoice.balance_due <= 0 else InvoiceStatus.PARTIALLY_PAID
    )
    locked_invoice.updated_by = actor
    locked_invoice.save(update_fields=["status", "updated_by"])

    log_activity(
        cooperative=locked_invoice.cooperative, actor=actor, action="invoice.payment_recorded",
        target_type="Payment", target_id=payment.id, target_repr=f"{amount} — {locked_invoice.invoice_number}",
        metadata={"amount": str(amount), "payment_method": payment_method, "new_status": locked_invoice.status},
    )

    return payment
