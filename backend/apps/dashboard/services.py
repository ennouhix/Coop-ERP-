"""
Logique d'agrégation du tableau de bord.

Aucun modèle propre à ce module : il lit exclusivement les données des
modules déjà construits (Epics 4 à 11). Les totaux financiers sont
calculés par agrégation SQL (Sum sur des expressions F()), jamais par des
boucles Python sur des querysets complets — sauf le calcul des factures
en retard, itéré en Python sur un ensemble borné (les factures actives
d'UNE coopérative, un volume raisonnable en V1).
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from django.db.models import DecimalField, ExpressionWrapper, F, Sum

from apps.billing.models import Invoice, InvoiceLine, InvoiceStatus, Payment
from apps.cooperatives.models import Cooperative
from apps.inventory.models import StockLevel
from apps.members.models import Member, MemberStatus
from apps.partners.models import Partner
from apps.purchases.models import PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus
from apps.sales.models import SalesOrder, SalesOrderStatus

MONEY_FIELD = DecimalField(max_digits=14, decimal_places=2)


def _line_amount_sum(queryset, quantity_field: str = "quantity", price_field: str = "unit_price") -> Decimal:
    expr = ExpressionWrapper(F(quantity_field) * F(price_field), output_field=MONEY_FIELD)
    result = queryset.annotate(_amount=expr).aggregate(total=Sum("_amount"))["total"]
    return result or Decimal("0")


def get_dashboard_summary(
    *, cooperative: Cooperative, date_from: Optional[date] = None, date_to: Optional[date] = None
) -> dict:
    if date_to is None:
        date_to = date.today()
    if date_from is None:
        date_from = date_to.replace(day=1)  # début du mois courant par défaut

    summary = {
        "period": {"date_from": date_from, "date_to": date_to},
        "members": _members_summary(cooperative),
        "partners": _partners_summary(cooperative),
        "sales": _sales_summary(cooperative, date_from, date_to),
        "purchases": _purchases_summary(cooperative, date_from, date_to),
        "stock": _stock_summary(cooperative),
        "billing": _billing_summary(cooperative, date_from, date_to),
    }
    return summary


def _members_summary(cooperative: Cooperative) -> dict:
    return {
        "active_count": Member.objects.filter(cooperative=cooperative, status=MemberStatus.ACTIVE).count(),
        "total_count": Member.all_objects.filter(cooperative=cooperative).count(),
    }


def _partners_summary(cooperative: Cooperative) -> dict:
    return {
        "active_customers": Partner.objects.filter(cooperative=cooperative, is_customer=True).count(),
        "active_suppliers": Partner.objects.filter(cooperative=cooperative, is_supplier=True).count(),
    }


def _sales_summary(cooperative: Cooperative, date_from: date, date_to: date) -> dict:
    orders = SalesOrder.objects.filter(cooperative=cooperative)
    revenue_lines = InvoiceLine.objects.filter(
        invoice__cooperative=cooperative,
        invoice__status__in=[InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.PAID],
        invoice__issue_date__range=[date_from, date_to],
    )
    return {
        "orders_draft": orders.filter(status=SalesOrderStatus.DRAFT).count(),
        "orders_confirmed": orders.filter(status=SalesOrderStatus.CONFIRMED).count(),
        "orders_partially_delivered": orders.filter(status=SalesOrderStatus.PARTIALLY_DELIVERED).count(),
        "orders_delivered": orders.filter(status=SalesOrderStatus.DELIVERED).count(),
        "revenue_invoiced_period": _line_amount_sum(revenue_lines),
    }


def _purchases_summary(cooperative: Cooperative, date_from: date, date_to: date) -> dict:
    orders = PurchaseOrder.objects.filter(cooperative=cooperative)
    spend_lines = PurchaseOrderLine.objects.filter(
        purchase_order__cooperative=cooperative,
        purchase_order__status__in=[
            PurchaseOrderStatus.CONFIRMED, PurchaseOrderStatus.PARTIALLY_RECEIVED, PurchaseOrderStatus.RECEIVED,
        ],
        purchase_order__order_date__range=[date_from, date_to],
    )
    return {
        "orders_draft": orders.filter(status=PurchaseOrderStatus.DRAFT).count(),
        "orders_confirmed": orders.filter(status=PurchaseOrderStatus.CONFIRMED).count(),
        "orders_partially_received": orders.filter(status=PurchaseOrderStatus.PARTIALLY_RECEIVED).count(),
        "orders_received": orders.filter(status=PurchaseOrderStatus.RECEIVED).count(),
        "spend_confirmed_period": _line_amount_sum(spend_lines, "quantity_ordered", "unit_price"),
    }


def _stock_summary(cooperative: Cooperative) -> dict:
    levels = StockLevel.objects.filter(cooperative=cooperative)
    value_expr = ExpressionWrapper(
        F("quantity") * F("product__reference_purchase_price"), output_field=MONEY_FIELD
    )
    total_value = levels.annotate(_value=value_expr).aggregate(total=Sum("_value"))["total"] or Decimal("0")
    low_stock_count = levels.filter(quantity__lt=F("product__minimum_stock_threshold")).count()

    return {
        "total_stock_value": total_value,
        "low_stock_lines_count": low_stock_count,
    }


def _billing_summary(cooperative: Cooperative, date_from: date, date_to: date) -> dict:
    active_invoices = Invoice.objects.filter(
        cooperative=cooperative, status__in=[InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID]
    ).prefetch_related("lines", "payments")

    # Itération Python volontairement bornée aux factures ACTIVES d'une
    # seule coopérative (typiquement quelques dizaines/centaines en V1) :
    # total_amount et balance_due sont des propriétés Python (Epic 11),
    # pas des colonnes agrégeables directement en SQL sans dénormalisation
    # supplémentaire. Revoir si le volume explose (dénormaliser un champ
    # `balance_due` mis à jour à chaque paiement, comme StockLevel).
    total_outstanding = Decimal("0")
    overdue_count = 0
    for invoice in active_invoices:
        total_outstanding += invoice.balance_due
        if invoice.is_overdue:
            overdue_count += 1

    collected = Payment.objects.filter(
        invoice__cooperative=cooperative, payment_date__range=[date_from, date_to]
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    return {
        "total_outstanding_balance": total_outstanding,
        "overdue_invoices_count": overdue_count,
        "amount_collected_period": collected,
    }
