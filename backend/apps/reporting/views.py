"""
Vues du module reporting.

Endpoints :
- GET /api/v1/reporting/invoices/{id}/pdf/                  -> facture PDF
- GET /api/v1/reporting/exports/{report}/?format=xlsx|pdf   -> export d'un rapport
- GET /api/v1/reporting/previews/{report}/                  -> aperçu JSON (prévisualisation)
"""
from __future__ import annotations

from datetime import date

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsCooperativeMember
from apps.billing.models import Invoice
from apps.reporting import data, excel, pdf
from apps.roles_permissions.permissions import RequirePermission

XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PREVIEW_LIMIT = 50  # nombre de lignes renvoyées dans l'aperçu à l'écran


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _export_response(
    cooperative, fmt: str, stem: str, title: str, subtitle: str, headers: list, rows: list,
):
    """Construit la réponse Excel ou PDF à partir des lignes partagées."""
    if fmt == "pdf":
        buffer = pdf.generate_report_pdf(cooperative, title, subtitle, headers, rows)
        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{stem}.pdf"'
        return response
    buffer = excel.from_rows(stem.replace("-", " ").title(), headers, rows)
    response = HttpResponse(buffer, content_type=XLSX_CONTENT_TYPE)
    response["Content-Disposition"] = f'attachment; filename="{stem}.xlsx"'
    return response


class InvoicePdfView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("billing.view")]

    def get(self, request: Request, invoice_id: str) -> HttpResponse:
        invoice = get_object_or_404(
            Invoice.objects.select_related("cooperative", "customer")
            .prefetch_related("lines__product"),
            pk=invoice_id, cooperative_id=request.user.cooperative_id,
        )
        buffer = pdf.generate_invoice_pdf(invoice)
        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{invoice.invoice_number}.pdf"'
        return response


# ===========================================================================
# Exports Excel / PDF
# ===========================================================================

class MembersExportView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("reports.view")]

    def get(self, request: Request) -> HttpResponse:
        fmt = request.query_params.get("output", "xlsx")
        cooperative = request.user.cooperative
        headers, rows = data.members_rows(cooperative)
        return _export_response(
            cooperative, fmt, "membres", "Adhérents & Membres", "", headers, rows,
        )


class StockMovementsExportView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("reports.view")]

    def get(self, request: Request) -> HttpResponse:
        fmt = request.query_params.get("output", "xlsx")
        cooperative = request.user.cooperative
        date_from = _parse_date(request.query_params.get("date_from"))
        date_to = _parse_date(request.query_params.get("date_to"))
        movement_type = request.query_params.get("movement_type") or None
        warehouse_id = request.query_params.get("warehouse_id") or None
        headers, rows = data.stock_movements_rows(
            cooperative, date_from=date_from, date_to=date_to,
            movement_type=movement_type, warehouse_id=warehouse_id,
        )
        return _export_response(
            cooperative, fmt, "mouvements-stock", "Mouvements de Stock", "", headers, rows,
        )


class SalesOrdersExportView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("reports.view")]

    def get(self, request: Request) -> HttpResponse:
        fmt = request.query_params.get("output", "xlsx")
        cooperative = request.user.cooperative
        date_from = _parse_date(request.query_params.get("date_from"))
        date_to = _parse_date(request.query_params.get("date_to"))
        status_filter = request.query_params.get("status") or None
        customer_id = request.query_params.get("customer_id") or None
        headers, rows = data.sales_orders_rows(
            cooperative, date_from=date_from, date_to=date_to,
            status=status_filter, customer_id=customer_id,
        )
        return _export_response(
            cooperative, fmt, "commandes-vente", "Commandes de Vente", "", headers, rows,
        )


class PurchaseOrdersExportView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("reports.view")]

    def get(self, request: Request) -> HttpResponse:
        fmt = request.query_params.get("output", "xlsx")
        cooperative = request.user.cooperative
        date_from = _parse_date(request.query_params.get("date_from"))
        date_to = _parse_date(request.query_params.get("date_to"))
        status_filter = request.query_params.get("status") or None
        supplier_id = request.query_params.get("supplier_id") or None
        headers, rows = data.purchase_orders_rows(
            cooperative, date_from=date_from, date_to=date_to,
            status=status_filter, supplier_id=supplier_id,
        )
        return _export_response(
            cooperative, fmt, "commandes-achat", "Commandes d'Achat", "", headers, rows,
        )


class PartnersExportView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("reports.view")]

    def get(self, request: Request) -> HttpResponse:
        fmt = request.query_params.get("output", "xlsx")
        cooperative = request.user.cooperative
        kind = request.query_params.get("kind") or None
        status_filter = request.query_params.get("status") or None
        headers, rows = data.partners_rows(cooperative, kind=kind, status=status_filter)
        return _export_response(
            cooperative, fmt, "partenaires", "Partenaires", "", headers, rows,
        )


class InvoicesExportView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("reports.view")]

    def get(self, request: Request) -> HttpResponse:
        fmt = request.query_params.get("output", "xlsx")
        cooperative = request.user.cooperative
        date_from = _parse_date(request.query_params.get("date_from"))
        date_to = _parse_date(request.query_params.get("date_to"))
        status_filter = request.query_params.get("status") or None
        customer_id = request.query_params.get("customer_id") or None
        headers, rows = data.invoices_rows(
            cooperative, date_from=date_from, date_to=date_to,
            status=status_filter, customer_id=customer_id,
        )
        return _export_response(
            cooperative, fmt, "factures", "Factures", "", headers, rows,
        )


class StockLevelsExportView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("reports.view")]

    def get(self, request: Request) -> HttpResponse:
        fmt = request.query_params.get("output", "xlsx")
        cooperative = request.user.cooperative
        warehouse_id = request.query_params.get("warehouse_id") or None
        headers, rows = data.stock_levels_rows(cooperative, warehouse_id=warehouse_id)
        return _export_response(
            cooperative, fmt, "niveaux-stock", "Niveaux de Stock", "", headers, rows,
        )


class AccountingJournalExportView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("reports.view")]

    def get(self, request: Request) -> HttpResponse:
        fmt = request.query_params.get("output", "xlsx")
        cooperative = request.user.cooperative
        period = request.query_params.get("period") or None
        journal_id = request.query_params.get("journal_id") or None
        headers, rows = data.accounting_journal_rows(
            cooperative, period=period, journal_id=journal_id,
        )
        return _export_response(
            cooperative, fmt, "journal-comptable", "Journal Comptable", "", headers, rows,
        )


# ===========================================================================
# Aperçu à l'écran (preview JSON)
# ===========================================================================

class ReportPreviewView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("reports.view")]

    def get(self, request: Request, report: str) -> Response:
        qp = request.query_params
        cooperative = request.user.cooperative

        builders = {
            "members": lambda: data.members_rows(cooperative),
            "stock-movements": lambda: data.stock_movements_rows(
                cooperative,
                date_from=_parse_date(qp.get("date_from")),
                date_to=_parse_date(qp.get("date_to")),
                movement_type=qp.get("movement_type") or None,
                warehouse_id=qp.get("warehouse_id") or None,
            ),
            "sales-orders": lambda: data.sales_orders_rows(
                cooperative,
                date_from=_parse_date(qp.get("date_from")),
                date_to=_parse_date(qp.get("date_to")),
                status=qp.get("status") or None,
                customer_id=qp.get("customer_id") or None,
            ),
            "purchase-orders": lambda: data.purchase_orders_rows(
                cooperative,
                date_from=_parse_date(qp.get("date_from")),
                date_to=_parse_date(qp.get("date_to")),
                status=qp.get("status") or None,
                supplier_id=qp.get("supplier_id") or None,
            ),
            "partners": lambda: data.partners_rows(
                cooperative,
                kind=qp.get("kind") or None,
                status=qp.get("status") or None,
            ),
            "invoices": lambda: data.invoices_rows(
                cooperative,
                date_from=_parse_date(qp.get("date_from")),
                date_to=_parse_date(qp.get("date_to")),
                status=qp.get("status") or None,
                customer_id=qp.get("customer_id") or None,
            ),
            "stock-levels": lambda: data.stock_levels_rows(
                cooperative,
                warehouse_id=qp.get("warehouse_id") or None,
            ),
            "accounting-journal": lambda: data.accounting_journal_rows(
                cooperative,
                period=qp.get("period") or None,
                journal_id=qp.get("journal_id") or None,
            ),
        }

        builder = builders.get(report)
        if builder is None:
            return Response(
                {"detail": f"Rapport inconnu : {report}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        headers, rows = builder()
        preview = [
            [data.format_report_cell(value) for value in row]
            for row in rows[:PREVIEW_LIMIT]
        ]
        return Response({
            "report": report,
            "columns": headers,
            "rows": preview,
            "total": len(rows),
            "truncated": len(rows) > PREVIEW_LIMIT,
        })
