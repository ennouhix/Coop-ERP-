"""
Vues du module members.

Endpoints :
- GET    /api/v1/members/                -> liste (recherche + filtres)
- POST   /api/v1/members/                -> créer un membre
- GET    /api/v1/members/{id}/           -> détail
- PATCH  /api/v1/members/{id}/           -> modifier
- POST   /api/v1/members/{id}/deactivate/ -> désactiver
- POST   /api/v1/members/{id}/reactivate/ -> réactiver

Parts sociales :
- GET    /api/v1/members/shares/         -> historique des mouvements
- POST   /api/v1/members/shares/         -> souscription ou retrait de parts
- GET    /api/v1/members/shares/{id}/    -> détail d'un mouvement
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
from apps.members import services
from apps.members.filters import MemberFilter, ShareTransactionFilter
from apps.members.models import Member, ShareTransaction, ShareTransactionType
from apps.members.serializers import (
    MemberCreateSerializer,
    MemberSerializer,
    ShareTransactionCreateSerializer,
    ShareTransactionSerializer,
)
from apps.members.services import create_member
from apps.roles_permissions.permissions import RequirePermission


class MemberListCreateView(generics.ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MemberFilter
    search_fields = ["member_number", "first_name", "last_name", "phone_number", "cin"]
    ordering_fields = ["last_name", "join_date", "member_number"]

    def get_queryset(self):  # noqa: ANN201
        # IMPORTANT : ne JAMAIS définir `queryset = Member.objects.all()` en
        # attribut de classe ici. Un attribut de classe est évalué une seule
        # fois à l'import du module (donc avant toute requête, sans tenant
        # dans le contexte) : le filtre de TenantManager se figerait sans
        # jamais filtrer. get_queryset() en méthode garantit une évaluation
        # fraîche à CHAQUE requête, une fois le tenant résolu par
        # TenantAwareJWTAuthentication.
        #
        # `all_objects` (pas `objects`) : le manager par défaut filtre
        # automatiquement is_active=True, ce qui rendrait un membre
        # désactivé invisible PARTOUT (y compris avec le filtre
        # ?status=inactive), donnant l'impression trompeuse d'une
        # suppression alors que la ligne existe toujours en base.
        # `all_objects` n'appliquant aucun filtrage automatique (ni tenant,
        # ni is_active), on restaure l'isolation multi-tenant manuellement.
        return Member.all_objects.filter(cooperative_id=self.request.user.cooperative_id)

    def get_permissions(self):  # noqa: ANN201
        base = [IsAuthenticated(), IsCooperativeMember()]
        if self.request.method == "POST":
            base.append(RequirePermission("members.edit")())
        else:
            base.append(RequirePermission("members.view")())
        return base

    def get_serializer_class(self):  # noqa: ANN201
        return MemberCreateSerializer if self.request.method == "POST" else MemberSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = MemberCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        member = create_member(cooperative=request.user.cooperative, **serializer.validated_data)
        return Response(MemberSerializer(member).data, status=status.HTTP_201_CREATED)


class MemberDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = MemberSerializer

    def get_queryset(self):  # noqa: ANN201
        # Même raison qu'au-dessus : sans all_objects, accéder à la fiche
        # d'un membre qu'on vient de désactiver renverrait une 404,
        # empêchant même de le réactiver depuis sa propre page.
        return Member.all_objects.filter(cooperative_id=self.request.user.cooperative_id)

    def get_permissions(self):  # noqa: ANN201
        base = [IsAuthenticated(), IsCooperativeMember()]
        code = "members.edit" if self.request.method in {"PATCH", "PUT"} else "members.view"
        base.append(RequirePermission(code)())
        return base


class MemberDeactivateView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("members.edit")]

    def post(self, request: Request, member_id: str) -> Response:
        member = get_object_or_404(Member, pk=member_id, cooperative_id=request.user.cooperative_id)
        member.status = "inactive"
        member.is_active = False
        member.save(update_fields=["status", "is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class MemberReactivateView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("members.edit")]

    def post(self, request: Request, member_id: str) -> Response:
        member = get_object_or_404(
            Member.all_objects, pk=member_id, cooperative_id=request.user.cooperative_id
        )
        member.status = "active"
        member.is_active = True
        member.save(update_fields=["status", "is_active"])
        return Response(MemberSerializer(member).data, status=status.HTTP_200_OK)


class ShareTransactionListCreateView(generics.ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ShareTransactionFilter
    ordering_fields = ["transaction_date", "created_at"]

    def get_queryset(self):  # noqa: ANN201
        return ShareTransaction.all_objects.filter(
            cooperative_id=self.request.user.cooperative_id
        ).select_related("member")

    def get_permissions(self):  # noqa: ANN201
        base = [IsAuthenticated(), IsCooperativeMember()]
        code = "members.edit" if self.request.method == "POST" else "members.view"
        base.append(RequirePermission(code)())
        return base

    def get_serializer_class(self):  # noqa: ANN201
        return (
            ShareTransactionCreateSerializer
            if self.request.method == "POST"
            else ShareTransactionSerializer
        )

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = ShareTransactionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        member = get_object_or_404(
            Member, pk=data["member_id"], cooperative_id=request.user.cooperative_id
        )
        try:
            if data["transaction_type"] == ShareTransactionType.REDEMPTION:
                record = services.redeem_shares(
                    cooperative=request.user.cooperative,
                    member=member,
                    shares_count=data["shares_count"],
                    amount_per_share=data["amount_per_share"],
                    transaction_date=data.get("transaction_date"),
                    notes=data["notes"],
                )
            else:
                record = services.subscribe_shares(
                    cooperative=request.user.cooperative,
                    member=member,
                    shares_count=data["shares_count"],
                    amount_per_share=data["amount_per_share"],
                    transaction_date=data.get("transaction_date"),
                    notes=data["notes"],
                )
        except services.InvalidSharesError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ShareTransactionSerializer(record).data, status=status.HTTP_201_CREATED)


class ShareTransactionDetailView(generics.RetrieveAPIView):
    """Lecture seule d'un mouvement de parts (le ledger des parts est immuable)."""

    serializer_class = ShareTransactionSerializer

    def get_queryset(self):  # noqa: ANN201
        return ShareTransaction.all_objects.filter(
            cooperative_id=self.request.user.cooperative_id
        ).select_related("member")

    def get_permissions(self):  # noqa: ANN201
        return [IsAuthenticated(), IsCooperativeMember(), RequirePermission("members.view")()]
