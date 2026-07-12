from __future__ import annotations

from django.urls import path

from apps.reporting.views import (
    InvoicePdfView,
    MembersExcelExportView,
    SalesOrdersExcelExportView,
    StockMovementsExcelExportView,
)

app_name = "reporting"

urlpatterns = [
    path("invoices/<uuid:invoice_id>/pdf/", InvoicePdfView.as_view(), name="invoice-pdf"),
    path("exports/members/", MembersExcelExportView.as_view(), name="export-members"),
    path("exports/stock-movements/", StockMovementsExcelExportView.as_view(), name="export-stock-movements"),
    path("exports/sales-orders/", SalesOrdersExcelExportView.as_view(), name="export-sales-orders"),
]
