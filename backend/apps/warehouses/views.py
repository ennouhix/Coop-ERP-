"""
Vues du module warehouses.

Endpoints :
- GET/POST   /api/v1/warehouses/                    -> liste / création
- GET/PATCH  /api/v1/warehouses/{id}/                -> détail / modification
- POST       /api/v1/warehouses/{id}/set-default/    -> définir comme entrepôt par défaut
- POST       /api/v1/warehouses/{id}/deactivate/     -> désactivation
- POST       /api/v1/warehouses/{id}/reactivate/     -> réactivation
"""
from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsCooperativeMember
from apps.roles_permissions.permissions import RequirePermission
from apps.warehouses.models import Warehouse
from apps.warehouses.serializers import WarehouseCreateSerializer, WarehouseSerializer
from apps.warehouses.services import create_warehouse, set_default_warehouse


class _WarehousePermissionMixin:
    def get_permissions(self):  # noqa: ANN201
        base = [IsAuthenticated(), IsCooperativeMember()]
        write_methods = {"POST", "PATCH", "PUT", "DELETE"}
        code = "warehouses.edit" if self.request.method in write_methods else "warehouses.view"
        base.append(RequirePermission(code)())
        return base


class WarehouseListCreateView(_WarehousePermissionMixin, generics.ListCreateAPIView):
    def get_queryset(self):  # noqa: ANN201
        return Warehouse.all_objects.filter(cooperative_id=self.request.user.cooperative_id).select_related("manager")

    def get_serializer_class(self):  # noqa: ANN201
        return WarehouseCreateSerializer if self.request.method == "POST" else WarehouseSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = WarehouseCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        warehouse = create_warehouse(cooperative=request.user.cooperative, **serializer.validated_data)
        return Response(WarehouseSerializer(warehouse).data, status=status.HTTP_201_CREATED)


class WarehouseDetailView(_WarehousePermissionMixin, generics.RetrieveUpdateAPIView):
    serializer_class = WarehouseSerializer

    def get_queryset(self):  # noqa: ANN201
        return Warehouse.all_objects.filter(cooperative_id=self.request.user.cooperative_id).select_related("manager")


class WarehouseSetDefaultView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("warehouses.edit")]

    def post(self, request: Request, warehouse_id: str) -> Response:
        warehouse = get_object_or_404(
            Warehouse, pk=warehouse_id, cooperative_id=request.user.cooperative_id
        )
        set_default_warehouse(warehouse=warehouse)
        return Response(WarehouseSerializer(warehouse).data, status=status.HTTP_200_OK)


class WarehouseDeactivateView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("warehouses.edit")]

    def post(self, request: Request, warehouse_id: str) -> Response:
        warehouse = get_object_or_404(
            Warehouse, pk=warehouse_id, cooperative_id=request.user.cooperative_id
        )
        if warehouse.is_default:
            return Response(
                {"error": {"message": "Impossible de désactiver l'entrepôt par défaut. Définissez-en un autre d'abord."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        warehouse.is_active = False
        warehouse.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class WarehouseReactivateView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("warehouses.edit")]

    def post(self, request: Request, warehouse_id: str) -> Response:
        warehouse = get_object_or_404(
            Warehouse.all_objects, pk=warehouse_id, cooperative_id=request.user.cooperative_id
        )
        warehouse.is_active = True
        warehouse.save(update_fields=["is_active"])
        return Response(WarehouseSerializer(warehouse).data, status=status.HTTP_200_OK)
