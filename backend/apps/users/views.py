"""
Vues du module users.

Endpoints :
- GET    /api/v1/users/                      -> liste des membres de l'équipe
- PATCH  /api/v1/users/{id}/role/            -> changer le rôle d'un membre
- POST   /api/v1/users/{id}/deactivate/      -> désactiver un membre
- POST   /api/v1/users/{id}/reactivate/      -> réactiver un membre
- GET    /api/v1/users/invitations/          -> liste des invitations
- POST   /api/v1/users/invitations/          -> créer une invitation
- DELETE /api/v1/users/invitations/{id}/     -> annuler une invitation
- POST   /api/v1/users/invitations/accept/   -> accepter une invitation (public)
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.permissions import IsCooperativeMember, IsOwnerOrAdmin
from apps.authentication.serializers import UserProfileSerializer
from apps.users import services
from apps.users.models import Invitation, InvitationStatus
from apps.users.serializers import (
    AcceptInvitationSerializer,
    ChangeRoleSerializer,
    InvitationCreateSerializer,
    InvitationSerializer,
    TeamMemberSerializer,
)

User = get_user_model()


class TeamMemberListView(generics.ListAPIView):
    """Liste des membres de la coopérative de l'utilisateur connecté."""

    serializer_class = TeamMemberSerializer
    permission_classes = [IsAuthenticated, IsCooperativeMember]

    def get_queryset(self):  # noqa: ANN201
        return User.objects.filter(cooperative_id=self.request.user.cooperative_id).order_by(
            "-role", "first_name"
        )


class ChangeUserRoleView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, IsOwnerOrAdmin]

    def patch(self, request: Request, user_id: str) -> Response:
        target = get_object_or_404(User, pk=user_id, cooperative_id=request.user.cooperative_id)
        serializer = ChangeRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            services.change_user_role(
                actor=request.user, target_user=target, new_role=serializer.validated_data["role"]
            )
        except services.TeamManagementError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)

        return Response(TeamMemberSerializer(target).data, status=status.HTTP_200_OK)


class DeactivateUserView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, IsOwnerOrAdmin]

    def post(self, request: Request, user_id: str) -> Response:
        target = get_object_or_404(User, pk=user_id, cooperative_id=request.user.cooperative_id)
        try:
            services.deactivate_user(actor=request.user, target_user=target)
        except services.TeamManagementError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReactivateUserView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, IsOwnerOrAdmin]

    def post(self, request: Request, user_id: str) -> Response:
        target = get_object_or_404(
            User, pk=user_id, cooperative_id=request.user.cooperative_id
        )
        services.reactivate_user(target_user=target)
        return Response(TeamMemberSerializer(target).data, status=status.HTTP_200_OK)


class InvitationListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, IsOwnerOrAdmin]

    def get_queryset(self):  # noqa: ANN201
        return Invitation.objects.filter(status=InvitationStatus.PENDING)

    def get_serializer_class(self):  # noqa: ANN201
        return InvitationCreateSerializer if self.request.method == "POST" else InvitationSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = InvitationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            invitation = services.create_invitation(
                actor=request.user,
                cooperative=request.user.cooperative,
                email=serializer.validated_data["email"],
                role=serializer.validated_data["role"],
            )
        except services.TeamManagementError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)

        return Response(InvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)


class InvitationCancelView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, IsOwnerOrAdmin]

    def delete(self, request: Request, invitation_id: str) -> Response:
        invitation = get_object_or_404(
            Invitation, pk=invitation_id, cooperative_id=request.user.cooperative_id
        )
        services.cancel_invitation(invitation=invitation)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AcceptInvitationView(APIView):
    """Endpoint public : l'invité n'a pas encore de compte pour s'authentifier."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = services.accept_invitation(
                token=serializer.validated_data["token"],
                password=serializer.validated_data["password"],
                first_name=serializer.validated_data["first_name"],
                last_name=serializer.validated_data["last_name"],
            )
        except services.InvalidInvitationError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        refresh["cooperative_id"] = str(user.cooperative_id)
        refresh["role"] = user.role

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserProfileSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )
