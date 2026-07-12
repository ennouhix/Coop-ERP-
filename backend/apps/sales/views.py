"""
Vues du module sales.

Endpoints :
- GET/POST  /api/v1/sales/orders/               -> liste / création
- GET       /api/v1/sales/orders/{id}/           -> détail
- POST      /api/v1/sales/orders/{id}/confirm/   -> confirmation (contrôle d'encours)
- POST      /api/v1/sales/orders/{id}/deliver/   -> livraison (sortie de stock réelle)
- POST      /api/v1/sales/orders/{id}/cancel/    -> annulation
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
from apps.roles_permissions.permissions import RequirePermission
from apps.sales import services
from apps.sales.models import SalesOrder
from apps.sales.serializers import SalesDeliverySerializer, SalesOrderCreateSerializer, SalesOrderSerializer
from apps.warehouses.models import Warehouse


class SalesOrderListCreateView(generics.ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "customer"]
    ordering_fields = ["order_date", "created_at"]

    def get_queryset(self):  # noqa: ANN201
        return SalesOrder.objects.select_related("customer", "warehouse").prefetch_related("lines__product").all()

    def get_permissions(self):  # noqa: ANN201
        base = [IsAuthenticated(), IsCooperativeMember()]
        code = "sales.edit" if self.request.method == "POST" else "sales.view"
        base.append(RequirePermission(code)())
        return base

    def get_serializer_class(self):  # noqa: ANN201
        return SalesOrderCreateSerializer if self.request.method == "POST" else SalesOrderSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = SalesOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        cooperative_id = request.user.cooperative_id

        customer = get_object_or_404(Partner, pk=data["customer_id"], cooperative_id=cooperative_id)
        warehouse = get_object_or_404(Warehouse, pk=data["warehouse_id"], cooperative_id=cooperative_id)

        resolved_lines = []
        for line in data["lines"]:
            product = get_object_or_404(Product, pk=line["product_id"], cooperative_id=cooperative_id)
            resolved_lines.append(
                {"product": product, "quantity_ordered": line["quantity_ordered"], "unit_price": line["unit_price"]}
            )

        try:
            order = services.create_sales_order(
                cooperative=request.user.cooperative, customer=customer, warehouse=warehouse,
                lines=resolved_lines, actor=request.user,
                order_date=data["order_date"], expected_delivery_date=data.get("expected_delivery_date"),
                notes=data["notes"],
            )
        except services.SalesOrderError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SalesOrderSerializer(order).data, status=status.HTTP_201_CREATED)


class SalesOrderDetailView(generics.RetrieveAPIView):
    serializer_class = SalesOrderSerializer
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("sales.view")]

    def get_queryset(self):  # noqa: ANN201
        return SalesOrder.objects.select_related("customer", "warehouse").prefetch_related("lines__product").all()


class SalesOrderConfirmView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("sales.edit")]

    def post(self, request: Request, order_id: str) -> Response:
        order = get_object_or_404(SalesOrder, pk=order_id, cooperative_id=request.user.cooperative_id)
        try:
            services.confirm_sales_order(order=order, actor=request.user)
        except services.SalesOrderError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SalesOrderSerializer(order).data, status=status.HTTP_200_OK)


class SalesOrderCancelView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("sales.edit")]

    def post(self, request: Request, order_id: str) -> Response:
        order = get_object_or_404(SalesOrder, pk=order_id, cooperative_id=request.user.cooperative_id)
        try:
            services.cancel_sales_order(order=order, actor=request.user)
        except services.SalesOrderError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SalesOrderSerializer(order).data, status=status.HTTP_200_OK)


class SalesOrderDeliverView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("sales.edit")]

    def post(self, request: Request, order_id: str) -> Response:
        order = get_object_or_404(SalesOrder, pk=order_id, cooperative_id=request.user.cooperative_id)
        serializer = SalesDeliverySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            services.record_sales_delivery(
                order=order, actor=request.user, deliveries=serializer.validated_data["deliveries"]
            )
        except services.SalesOrderError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)

        order.refresh_from_db()
        return Response(SalesOrderSerializer(order).data, status=status.HTTP_200_OK)
