"""
Vues du catalogue.

Endpoints :
- GET/POST   /api/v1/catalog/units/           -> unités de mesure
- GET/PATCH  /api/v1/catalog/units/{id}/
- GET/POST   /api/v1/catalog/categories/      -> catégories (hiérarchiques)
- GET/PATCH  /api/v1/catalog/categories/{id}/
- GET/POST   /api/v1/catalog/products/        -> produits (recherche + filtres)
- GET/PATCH  /api/v1/catalog/products/{id}/
- POST       /api/v1/catalog/products/{id}/deactivate/
- POST       /api/v1/catalog/products/{id}/reactivate/
"""

from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsCooperativeMember
from apps.catalog.filters import ProductFilter
from apps.catalog.models import Category, Product, Unit
from apps.catalog.serializers import (
    CategorySerializer,
    ProductCreateSerializer,
    ProductSerializer,
    UnitSerializer,
)
from apps.catalog.services import create_product
from apps.roles_permissions.permissions import RequirePermission


class _CatalogPermissionMixin:
    """Factorise la règle commune : lecture pour tous, écriture réservée par RBAC."""

    def get_permissions(self):  # noqa: ANN201
        base = [IsAuthenticated(), IsCooperativeMember()]
        write_methods = {"POST", "PATCH", "PUT", "DELETE"}
        code = "catalog.edit" if self.request.method in write_methods else "catalog.view"
        base.append(RequirePermission(code)())
        return base


class UnitListCreateView(_CatalogPermissionMixin, generics.ListCreateAPIView):
    serializer_class = UnitSerializer

    def get_queryset(self):  # noqa: ANN201
        return Unit.objects.all()

    def perform_create(self, serializer) -> None:  # noqa: ANN001
        serializer.save(cooperative=self.request.user.cooperative)


class UnitDetailView(_CatalogPermissionMixin, generics.RetrieveUpdateAPIView):
    serializer_class = UnitSerializer

    def get_queryset(self):  # noqa: ANN201
        return Unit.objects.all()


class CategoryListCreateView(_CatalogPermissionMixin, generics.ListCreateAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):  # noqa: ANN201
        return Category.objects.all()

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = CategorySerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        category = Category(cooperative=request.user.cooperative, **serializer.validated_data)

        try:
            category.full_clean()
        except DjangoValidationError as exc:
            return Response(
                {"error": {"message": "; ".join(exc.messages)}}, status=status.HTTP_400_BAD_REQUEST
            )

        category.save()
        return Response(
            CategorySerializer(category, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class CategoryDetailView(_CatalogPermissionMixin, generics.RetrieveUpdateAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):  # noqa: ANN201
        return Category.objects.all()

    def update(self, request: Request, *args, **kwargs) -> Response:
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()

        try:
            updated.full_clean()
        except DjangoValidationError as exc:
            return Response(
                {"error": {"message": "; ".join(exc.messages)}}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            CategorySerializer(updated, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


class ProductListCreateView(_CatalogPermissionMixin, generics.ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["sku", "barcode"]
    ordering_fields = ["sku", "created_at"]

    def get_queryset(self):  # noqa: ANN201
        return Product.all_objects.filter(
            cooperative_id=self.request.user.cooperative_id
        ).select_related("category", "unit")

    def get_serializer_class(self):  # noqa: ANN201
        return ProductCreateSerializer if self.request.method == "POST" else ProductSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = ProductCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        product = create_product(cooperative=request.user.cooperative, **serializer.validated_data)
        return Response(
            ProductSerializer(product, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ProductDetailView(_CatalogPermissionMixin, generics.RetrieveUpdateAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):  # noqa: ANN201
        return Product.all_objects.filter(
            cooperative_id=self.request.user.cooperative_id
        ).select_related("category", "unit")


class ProductDeactivateView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("catalog.edit")]

    def post(self, request: Request, product_id: str) -> Response:
        product = get_object_or_404(
            Product, pk=product_id, cooperative_id=request.user.cooperative_id
        )
        product.is_active = False
        product.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductReactivateView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("catalog.edit")]

    def post(self, request: Request, product_id: str) -> Response:
        # all_objects : un produit désactivé est invisible via le manager
        # filtré par défaut (piège déjà rencontré à l'Epic 5).
        product = get_object_or_404(
            Product.all_objects, pk=product_id, cooperative_id=request.user.cooperative_id
        )
        product.is_active = True
        product.save(update_fields=["is_active"])
        return Response(
            ProductSerializer(product, context={"request": request}).data, status=status.HTTP_200_OK
        )
