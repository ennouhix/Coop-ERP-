"""
Vues du module billing.

Endpoints :
- GET/POST  /api/v1/billing/invoices/                    -> liste / création manuelle
- POST      /api/v1/billing/invoices/from-order/          -> génération depuis une commande de vente
- GET       /api/v1/billing/invoices/{id}/                -> détail
- POST      /api/v1/billing/invoices/{id}/issue/          -> DRAFT -> ISSUED
- POST      /api/v1/billing/invoices/{id}/cancel/         -> annulation
- POST      /api/v1/billing/invoices/{id}/payments/       -> enregistrer un paiement
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsCooperativeMember
from apps.billing import services
from apps.billing.models import Invoice
from apps.billing.serializers import (
    InvoiceFromOrderSerializer,
    InvoiceSerializer,
    ManualInvoiceCreateSerializer,
    RecordPaymentSerializer,
)
from apps.catalog.models import Product
from apps.partners.models import Partner
from apps.roles_permissions.permissions import RequirePermission
from apps.sales.models import SalesOrder


class InvoiceListCreateView(generics.ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "customer"]
    ordering_fields = ["issue_date", "due_date", "created_at"]

    def get_queryset(self):  # noqa: ANN201
        return (
            Invoice.objects.select_related("customer", "sales_order")
            .prefetch_related("lines__product", "payments")
            .all()
        )

    def get_permissions(self):  # noqa: ANN201
        base = [IsAuthenticated(), IsCooperativeMember()]
        code = "billing.edit" if self.request.method == "POST" else "billing.view"
        base.append(RequirePermission(code)())
        return base

    def get_serializer_class(self):  # noqa: ANN201
        return ManualInvoiceCreateSerializer if self.request.method == "POST" else InvoiceSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = ManualInvoiceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        cooperative_id = request.user.cooperative_id

        customer = get_object_or_404(Partner, pk=data["customer_id"], cooperative_id=cooperative_id)

        resolved_lines = []
        for line in data["lines"]:
            product = get_object_or_404(
                Product, pk=line["product_id"], cooperative_id=cooperative_id
            )
            resolved_lines.append(
                {
                    "product": product,
                    "description": line["description"],
                    "quantity": line["quantity"],
                    "unit_price": line["unit_price"],
                }
            )

        try:
            invoice = services.create_manual_invoice(
                cooperative=request.user.cooperative,
                customer=customer,
                lines=resolved_lines,
                actor=request.user,
                issue_date=data["issue_date"],
                due_date=data.get("due_date"),
                notes=data["notes"],
            )
        except services.InvoiceError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)

        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)


class InvoiceFromOrderView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("billing.edit")]

    def post(self, request: Request) -> Response:
        serializer = InvoiceFromOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        order = get_object_or_404(
            SalesOrder, pk=data["order_id"], cooperative_id=request.user.cooperative_id
        )

        try:
            invoice = services.generate_invoice_from_sales_order(
                order=order,
                actor=request.user,
                issue_date=data["issue_date"],
                due_date=data.get("due_date"),
            )
        except services.InvoiceError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)

        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)


class InvoiceDetailView(generics.RetrieveAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("billing.view")]

    def get_queryset(self):  # noqa: ANN201
        return (
            Invoice.objects.select_related("customer", "sales_order")
            .prefetch_related("lines__product", "payments")
            .all()
        )


class InvoiceIssueView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("billing.edit")]

    def post(self, request: Request, invoice_id: str) -> Response:
        invoice = get_object_or_404(
            Invoice, pk=invoice_id, cooperative_id=request.user.cooperative_id
        )
        try:
            services.issue_invoice(invoice=invoice, actor=request.user)
        except services.InvoiceError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)
        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_200_OK)


class InvoiceCancelView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("billing.edit")]

    def post(self, request: Request, invoice_id: str) -> Response:
        invoice = get_object_or_404(
            Invoice, pk=invoice_id, cooperative_id=request.user.cooperative_id
        )
        try:
            services.cancel_invoice(invoice=invoice, actor=request.user)
        except services.InvoiceError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)
        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_200_OK)


class InvoicePaymentView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("billing.edit")]

    def post(self, request: Request, invoice_id: str) -> Response:
        invoice = get_object_or_404(
            Invoice, pk=invoice_id, cooperative_id=request.user.cooperative_id
        )
        serializer = RecordPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            services.record_payment(
                invoice=invoice,
                amount=data["amount"],
                payment_date=data["payment_date"],
                actor=request.user,
                payment_method=data["payment_method"],
                reference=data["reference"],
                notes=data["notes"],
            )
        except services.PaymentError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)

        invoice.refresh_from_db()
        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)
