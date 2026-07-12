"""
Vues du module inventory.

Endpoints :
- GET  /api/v1/inventory/stock-levels/            -> niveaux de stock actuels (filtrables)
- GET  /api/v1/inventory/stock-levels/low-stock/  -> produits sous leur seuil minimum
- GET  /api/v1/inventory/movements/               -> historique des mouvements (lecture seule)
- POST /api/v1/inventory/movements/in/            -> entrée de stock
- POST /api/v1/inventory/movements/out/           -> sortie de stock
- POST /api/v1/inventory/movements/transfer/      -> transfert entre entrepôts

Aucune route PATCH/DELETE n'existe pour StockMovement : c'est ainsi que
l'immuabilité du ledger est garantie au niveau API, pas seulement au
niveau d'une règle métier qu'on pourrait contourner.
"""
from __future__ import annotations

from django.db.models import F
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsCooperativeMember
from apps.catalog.models import Product
from apps.inventory import services
from apps.inventory.filters import StockLevelFilter, StockMovementFilter
from apps.inventory.models import StockLevel, StockMovement
from apps.inventory.serializers import (
    StockLevelSerializer,
    StockMovementInSerializer,
    StockMovementOutSerializer,
    StockMovementSerializer,
    StockMovementTransferSerializer,
)
from apps.roles_permissions.permissions import RequirePermission
from apps.warehouses.models import Warehouse


class _InventoryPermissionMixin:
    def get_permissions(self):  # noqa: ANN201
        base = [IsAuthenticated(), IsCooperativeMember()]
        write_methods = {"POST", "PATCH", "PUT", "DELETE"}
        code = "stock.edit" if self.request.method in write_methods else "stock.view"
        base.append(RequirePermission(code)())
        return base


class StockLevelListView(_InventoryPermissionMixin, generics.ListAPIView):
    serializer_class = StockLevelSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = StockLevelFilter

    def get_queryset(self):  # noqa: ANN201
        return StockLevel.objects.select_related("product", "warehouse", "product__unit").all()


class LowStockListView(_InventoryPermissionMixin, generics.ListAPIView):
    """Lignes produit/entrepôt dont la quantité est sous le seuil défini sur la fiche produit."""

    serializer_class = StockLevelSerializer

    def get_queryset(self):  # noqa: ANN201
        return (
            StockLevel.objects.select_related("product", "warehouse", "product__unit")
            .filter(quantity__lt=F("product__minimum_stock_threshold"))
        )


class StockMovementListView(_InventoryPermissionMixin, generics.ListAPIView):
    """Historique en lecture seule — voir la docstring du module pour l'immuabilité."""

    serializer_class = StockMovementSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = StockMovementFilter

    def get_queryset(self):  # noqa: ANN201
        return StockMovement.objects.select_related(
            "product", "warehouse", "destination_warehouse", "created_by"
        ).all()


def _get_tenant_product(request: Request, product_id) -> Product:  # noqa: ANN001
    return get_object_or_404(Product, pk=product_id, cooperative_id=request.user.cooperative_id)


def _get_tenant_warehouse(request: Request, warehouse_id) -> Warehouse:  # noqa: ANN001
    return get_object_or_404(Warehouse, pk=warehouse_id, cooperative_id=request.user.cooperative_id)


class StockMovementInView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("stock.edit")]

    def post(self, request: Request) -> Response:
        serializer = StockMovementInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        product = _get_tenant_product(request, data["product_id"])
        warehouse = _get_tenant_warehouse(request, data["warehouse_id"])

        movement = services.record_stock_in(
            product=product, warehouse=warehouse, quantity=data["quantity"], actor=request.user,
            reason=data["reason"], reference=data["reference"], notes=data["notes"],
        )
        return Response(StockMovementSerializer(movement).data, status=status.HTTP_201_CREATED)


class StockMovementOutView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("stock.edit")]

    def post(self, request: Request) -> Response:
        serializer = StockMovementOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        product = _get_tenant_product(request, data["product_id"])
        warehouse = _get_tenant_warehouse(request, data["warehouse_id"])

        try:
            movement = services.record_stock_out(
                product=product, warehouse=warehouse, quantity=data["quantity"], actor=request.user,
                reason=data["reason"], reference=data["reference"], notes=data["notes"],
            )
        except services.InsufficientStockError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)

        return Response(StockMovementSerializer(movement).data, status=status.HTTP_201_CREATED)


class StockMovementTransferView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("stock.edit")]

    def post(self, request: Request) -> Response:
        serializer = StockMovementTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        product = _get_tenant_product(request, data["product_id"])
        from_warehouse = _get_tenant_warehouse(request, data["from_warehouse_id"])
        to_warehouse = _get_tenant_warehouse(request, data["to_warehouse_id"])

        try:
            movement = services.record_stock_transfer(
                product=product, from_warehouse=from_warehouse, to_warehouse=to_warehouse,
                quantity=data["quantity"], actor=request.user,
                reference=data["reference"], notes=data["notes"],
            )
        except (services.InsufficientStockError, services.InvalidMovementError) as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)

        return Response(StockMovementSerializer(movement).data, status=status.HTTP_201_CREATED)
