"""
Vues du module contributions.

Endpoints :
- GET    /api/v1/contributions/                -> liste (filtres)
- POST   /api/v1/contributions/                -> créer un apport
- GET    /api/v1/contributions/{id}/           -> détail (lecture seule)
- POST   /api/v1/contributions/{id}/mark-paid/ -> marquer comme payé

Les apports sont modifiables uniquement à la création : une fois enregistrés,
ils suivent le même principe d'immuabilité que le ledger de stock (un apport
payé ne se corrige pas sans créer un nouvel apport).
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsCooperativeMember
from apps.catalog.models import Product
from apps.contributions import services
from apps.contributions.filters import ContributionFilter
from apps.contributions.models import Contribution
from apps.contributions.serializers import (
    ContributionCreateSerializer,
    ContributionSerializer,
)
from apps.members.models import Member
from apps.roles_permissions.permissions import RequirePermission


class ContributionListCreateView(generics.ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ContributionFilter
    search_fields = ["campaign", "notes", "member__first_name", "member__last_name"]
    ordering_fields = ["contribution_date", "created_at"]

    def get_queryset(self):  # noqa: ANN201
        return Contribution.all_objects.filter(
            cooperative_id=self.request.user.cooperative_id
        ).select_related("member", "product")

    def get_permissions(self):  # noqa: ANN201
        base = [IsAuthenticated(), IsCooperativeMember()]
        code = "contributions.edit" if self.request.method == "POST" else "contributions.view"
        base.append(RequirePermission(code)())
        return base

    def get_serializer_class(self):  # noqa: ANN201
        return (
            ContributionCreateSerializer
            if self.request.method == "POST"
            else ContributionSerializer
        )

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = ContributionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        member = get_object_or_404(
            Member, pk=data["member_id"], cooperative_id=request.user.cooperative_id
        )
        product = get_object_or_404(
            Product, pk=data["product_id"], cooperative_id=request.user.cooperative_id
        )

        contribution = services.create_contribution(
            cooperative=request.user.cooperative,
            member=member,
            product=product,
            quantity=data["quantity"],
            unit_price=data["unit_price"],
            contribution_date=data.get("contribution_date") or timezone.localdate(),
            campaign=data["campaign"],
            status=data["status"],
            notes=data["notes"],
        )
        return Response(ContributionSerializer(contribution).data, status=status.HTTP_201_CREATED)


class ContributionDetailView(generics.RetrieveAPIView):
    serializer_class = ContributionSerializer

    def get_queryset(self):  # noqa: ANN201
        return Contribution.all_objects.filter(
            cooperative_id=self.request.user.cooperative_id
        ).select_related("member", "product")

    def get_permissions(self):  # noqa: ANN201
        return [IsAuthenticated(), IsCooperativeMember(), RequirePermission("contributions.view")()]


class ContributionMarkPaidView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsCooperativeMember,
        RequirePermission("contributions.edit"),
    ]

    def post(self, request: Request, pk: str) -> Response:
        contribution = get_object_or_404(
            Contribution.all_objects, pk=pk, cooperative_id=request.user.cooperative_id
        )
        contribution = services.mark_contribution_paid(contribution=contribution)
        return Response(ContributionSerializer(contribution).data, status=status.HTTP_200_OK)
