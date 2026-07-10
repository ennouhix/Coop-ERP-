"""
Vues du module partners.

Endpoints :
- GET/POST   /api/v1/partners/                -> liste (recherche + filtres) / création
- GET/PATCH  /api/v1/partners/{id}/            -> détail / modification
- POST       /api/v1/partners/{id}/deactivate/ -> désactivation
- POST       /api/v1/partners/{id}/reactivate/ -> réactivation
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
from apps.partners.filters import PartnerFilter
from apps.partners.models import Partner
from apps.partners.serializers import PartnerCreateSerializer, PartnerSerializer
from apps.partners.services import create_partner
from apps.roles_permissions.permissions import RequirePermission


class PartnerListCreateView(generics.ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PartnerFilter
    search_fields = ["code", "name", "phone_number", "ice"]
    ordering_fields = ["name", "code", "created_at"]

    def get_queryset(self):  # noqa: ANN201
        # Toujours en méthode, jamais en attribut de classe : voir le
        # correctif détaillé dans apps/members/views.py (Epic 4).
        return Partner.objects.all()

    def get_permissions(self):  # noqa: ANN201
        base = [IsAuthenticated(), IsCooperativeMember()]
        code = "partners.edit" if self.request.method == "POST" else "partners.view"
        base.append(RequirePermission(code)())
        return base

    def get_serializer_class(self):  # noqa: ANN201
        return PartnerCreateSerializer if self.request.method == "POST" else PartnerSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = PartnerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            partner = create_partner(cooperative=request.user.cooperative, **serializer.validated_data)
        except DjangoValidationError as exc:
            return Response({"error": {"message": "; ".join(exc.messages)}}, status=status.HTTP_400_BAD_REQUEST)

        return Response(PartnerSerializer(partner).data, status=status.HTTP_201_CREATED)


class PartnerDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = PartnerSerializer

    def get_queryset(self):  # noqa: ANN201
        return Partner.objects.all()

    def get_permissions(self):  # noqa: ANN201
        base = [IsAuthenticated(), IsCooperativeMember()]
        code = "partners.edit" if self.request.method in {"PATCH", "PUT"} else "partners.view"
        base.append(RequirePermission(code)())
        return base

    def update(self, request: Request, *args, **kwargs) -> Response:
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()

        try:
            updated.full_clean()
        except DjangoValidationError as exc:
            return Response({"error": {"message": "; ".join(exc.messages)}}, status=status.HTTP_400_BAD_REQUEST)

        return Response(PartnerSerializer(updated).data, status=status.HTTP_200_OK)


class PartnerDeactivateView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("partners.edit")]

    def post(self, request: Request, partner_id: str) -> Response:
        partner = get_object_or_404(Partner, pk=partner_id, cooperative_id=request.user.cooperative_id)
        partner.status = "inactive"
        partner.is_active = False
        partner.save(update_fields=["status", "is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class PartnerReactivateView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("partners.edit")]

    def post(self, request: Request, partner_id: str) -> Response:
        partner = get_object_or_404(
            Partner.all_objects, pk=partner_id, cooperative_id=request.user.cooperative_id
        )
        partner.status = "active"
        partner.is_active = True
        partner.save(update_fields=["status", "is_active"])
        return Response(PartnerSerializer(partner).data, status=status.HTTP_200_OK)
