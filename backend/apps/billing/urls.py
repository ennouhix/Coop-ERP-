from __future__ import annotations

from django.urls import path

from apps.billing.views import (
    InvoiceCancelView,
    InvoiceDetailView,
    InvoiceFromOrderView,
    InvoiceIssueView,
    InvoiceListCreateView,
    InvoicePaymentView,
)

app_name = "billing"

urlpatterns = [
    path("invoices/", InvoiceListCreateView.as_view(), name="invoice-list-create"),
    path("invoices/from-order/", InvoiceFromOrderView.as_view(), name="invoice-from-order"),
    path("invoices/<uuid:pk>/", InvoiceDetailView.as_view(), name="invoice-detail"),
    path("invoices/<uuid:invoice_id>/issue/", InvoiceIssueView.as_view(), name="invoice-issue"),
    path("invoices/<uuid:invoice_id>/cancel/", InvoiceCancelView.as_view(), name="invoice-cancel"),
    path(
        "invoices/<uuid:invoice_id>/payments/", InvoicePaymentView.as_view(), name="invoice-payment"
    ),
]
