"""
Vues du module purchases.

Endpoints :
- GET/POST  /api/v1/purchases/orders/               -> liste / création
- GET       /api/v1/purchases/orders/{id}/           -> détail
- POST      /api/v1/purchases/orders/{id}/confirm/   -> confirmation (purchases.edit)
- POST      /api/v1/purchases/orders/{id}/receive/   -> réception (purchases.receive)
- POST      /api/v1/purchases/orders/{id}/cancel/    -> annulation (purchases.edit)
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
from apps.catalog.models import Product
from apps.partners.models import Partner
from apps.purchases import services
from apps.purchases.models import PurchaseOrder, PurchaseOrderStatus
from apps.purchases.serializers import (
    PurchaseOrderCreateSerializer,
    PurchaseOrderSerializer,
    PurchaseReceiptSerializer,
)
from apps.roles_permissions.permissions import RequirePermission
from apps.warehouses.models import Warehouse


class PurchaseOrderListCreateView(generics.ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "supplier"]
    ordering_fields = ["order_date", "created_at"]

    def get_queryset(self):  # noqa: ANN201
        return PurchaseOrder.objects.select_related("supplier", "warehouse").prefetch_related("lines__product").all()

    def get_permissions(self):  # noqa: ANN201
        base = [IsAuthenticated(), IsCooperativeMember()]
        code = "purchases.edit" if self.request.method == "POST" else "purchases.view"
        base.append(RequirePermission(code)())
        return base

    def get_serializer_class(self):  # noqa: ANN201
        return PurchaseOrderCreateSerializer if self.request.method == "POST" else PurchaseOrderSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = PurchaseOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        cooperative_id = request.user.cooperative_id

        supplier = get_object_or_404(Partner, pk=data["supplier_id"], cooperative_id=cooperative_id)
        warehouse = get_object_or_404(Warehouse, pk=data["warehouse_id"], cooperative_id=cooperative_id)

        resolved_lines = []
        for line in data["lines"]:
            product = get_object_or_404(Product, pk=line["product_id"], cooperative_id=cooperative_id)
            resolved_lines.append(
                {"product": product, "quantity_ordered": line["quantity_ordered"], "unit_price": line["unit_price"]}
            )

        try:
            order = services.create_purchase_order(
                cooperative=request.user.cooperative, supplier=supplier, warehouse=warehouse,
                lines=resolved_lines, actor=request.user,
                order_date=data["order_date"], expected_delivery_date=data.get("expected_delivery_date"),
                notes=data["notes"],
            )
        except services.PurchaseOrderError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)

        return Response(PurchaseOrderSerializer(order).data, status=status.HTTP_201_CREATED)


class PurchaseOrderDetailView(generics.RetrieveAPIView):
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("purchases.view")]

    def get_queryset(self):  # noqa: ANN201
        return PurchaseOrder.objects.select_related("supplier", "warehouse").prefetch_related("lines__product").all()


class PurchaseOrderConfirmView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("purchases.edit")]

    def post(self, request: Request, order_id: str) -> Response:
        order = get_object_or_404(PurchaseOrder, pk=order_id, cooperative_id=request.user.cooperative_id)
        try:
            services.confirm_purchase_order(order=order, actor=request.user)
        except services.PurchaseOrderError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PurchaseOrderSerializer(order).data, status=status.HTTP_200_OK)


class PurchaseOrderCancelView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("purchases.edit")]

    def post(self, request: Request, order_id: str) -> Response:
        order = get_object_or_404(PurchaseOrder, pk=order_id, cooperative_id=request.user.cooperative_id)
        try:
            services.cancel_purchase_order(order=order, actor=request.user)
        except services.PurchaseOrderError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PurchaseOrderSerializer(order).data, status=status.HTTP_200_OK)


class PurchaseOrderReceiveView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("purchases.receive")]

    def post(self, request: Request, order_id: str) -> Response:
        order = get_object_or_404(PurchaseOrder, pk=order_id, cooperative_id=request.user.cooperative_id)
        serializer = PurchaseReceiptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            services.record_purchase_receipt(
                order=order, actor=request.user, receipts=serializer.validated_data["receipts"]
            )
        except services.PurchaseOrderError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)

        order.refresh_from_db()
        return Response(PurchaseOrderSerializer(order).data, status=status.HTTP_200_OK)
