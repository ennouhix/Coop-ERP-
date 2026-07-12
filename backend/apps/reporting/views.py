"""
Vues du module reporting.

Endpoints :
- GET /api/v1/reporting/invoices/{id}/pdf/            -> facture PDF
- GET /api/v1/reporting/exports/members/              -> membres.xlsx
- GET /api/v1/reporting/exports/stock-movements/      -> mouvements-stock.xlsx (filtrable par date)
- GET /api/v1/reporting/exports/sales-orders/         -> commandes-vente.xlsx (filtrable par date)
"""
from __future__ import annotations

from datetime import date

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.authentication.permissions import IsCooperativeMember
from apps.billing.models import Invoice
from apps.reporting import excel, pdf
from apps.roles_permissions.permissions import RequirePermission

XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


class InvoicePdfView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("billing.view")]

    def get(self, request: Request, invoice_id: str) -> HttpResponse:
        invoice = get_object_or_404(
            Invoice.objects.select_related("cooperative", "customer").prefetch_related("lines__product"),
            pk=invoice_id, cooperative_id=request.user.cooperative_id,
        )
        buffer = pdf.generate_invoice_pdf(invoice)
        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{invoice.invoice_number}.pdf"'
        return response


class MembersExcelExportView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("reports.view")]

    def get(self, request: Request) -> HttpResponse:
        buffer = excel.export_members_excel(request.user.cooperative)
        response = HttpResponse(buffer, content_type=XLSX_CONTENT_TYPE)
        response["Content-Disposition"] = 'attachment; filename="membres.xlsx"'
        return response


class StockMovementsExcelExportView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("reports.view")]

    def get(self, request: Request) -> HttpResponse:
        date_from = _parse_date(request.query_params.get("date_from"))
        date_to = _parse_date(request.query_params.get("date_to"))
        buffer = excel.export_stock_movements_excel(request.user.cooperative, date_from, date_to)
        response = HttpResponse(buffer, content_type=XLSX_CONTENT_TYPE)
        response["Content-Disposition"] = 'attachment; filename="mouvements-stock.xlsx"'
        return response


class SalesOrdersExcelExportView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("reports.view")]

    def get(self, request: Request) -> HttpResponse:
        date_from = _parse_date(request.query_params.get("date_from"))
        date_to = _parse_date(request.query_params.get("date_to"))
        buffer = excel.export_sales_orders_excel(request.user.cooperative, date_from, date_to)
        response = HttpResponse(buffer, content_type=XLSX_CONTENT_TYPE)
        response["Content-Disposition"] = 'attachment; filename="commandes-vente.xlsx"'
        return response
