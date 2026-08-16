from __future__ import annotations

from django.urls import path

from apps.reporting.views import (
    AccountingJournalExportView,
    InvoicePdfView,
    InvoicesExportView,
    MembersExportView,
    PartnersExportView,
    PurchaseOrdersExportView,
    ReportPreviewView,
    SalesOrdersExportView,
    StockLevelsExportView,
    StockMovementsExportView,
)

app_name = "reporting"

urlpatterns = [
    path("invoices/<uuid:invoice_id>/pdf/", InvoicePdfView.as_view(), name="invoice-pdf"),
    path("exports/members/", MembersExportView.as_view(), name="export-members"),
    path(
        "exports/stock-movements/",
        StockMovementsExportView.as_view(),
        name="export-stock-movements",
    ),
    path("exports/sales-orders/", SalesOrdersExportView.as_view(), name="export-sales-orders"),
    path(
        "exports/purchase-orders/",
        PurchaseOrdersExportView.as_view(),
        name="export-purchase-orders",
    ),
    path("exports/partners/", PartnersExportView.as_view(), name="export-partners"),
    path("exports/invoices/", InvoicesExportView.as_view(), name="export-invoices"),
    path("exports/stock-levels/", StockLevelsExportView.as_view(), name="export-stock-levels"),
    path(
        "exports/accounting-journal/",
        AccountingJournalExportView.as_view(),
        name="export-accounting-journal",
    ),
    path("previews/<str:report>/", ReportPreviewView.as_view(), name="preview-report"),
]
