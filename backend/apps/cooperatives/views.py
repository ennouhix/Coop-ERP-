"""
Vues du module cooperatives.

Endpoints exposés (voir urls.py) :
- POST   /api/v1/cooperatives/register/     -> inscription self-service (public)
- GET    /api/v1/cooperatives/me/           -> infos de ma coopérative
- PATCH  /api/v1/cooperatives/me/           -> mise à jour (OWNER/ADMIN uniquement)
- POST   /api/v1/cooperatives/me/logo/      -> upload du logo (OWNER/ADMIN uniquement)
"""
from __future__ import annotations

from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.permissions import IsCooperativeMember, IsOwnerOrAdmin
from apps.authentication.serializers import UserProfileSerializer
from apps.cooperatives.serializers import (
    CooperativeLogoSerializer,
    CooperativeRegistrationSerializer,
    CooperativeSerializer,
    CooperativeUpdateSerializer,
)
from apps.cooperatives.services import CooperativeRegistrationData, register_cooperative
from apps.cooperatives.throttling import RegistrationRateThrottle


class CooperativeRegisterView(APIView):
    """
    Inscription self-service. Crée la coopérative + son OWNER, puis
    retourne directement une paire de tokens JWT pour éviter à
    l'utilisateur de devoir se reconnecter juste après son inscription.
    """

    permission_classes = [AllowAny]
    throttle_classes = [RegistrationRateThrottle]

    def post(self, request: Request) -> Response:
        serializer = CooperativeRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        cooperative, owner = register_cooperative(
            CooperativeRegistrationData(
                cooperative_name=payload["cooperative_name"],
                owner_email=payload["owner_email"],
                owner_password=payload["owner_password"],
                owner_first_name=payload["owner_first_name"],
                owner_last_name=payload["owner_last_name"],
            )
        )

        refresh = RefreshToken.for_user(owner)
        refresh["cooperative_id"] = str(cooperative.id)
        refresh["role"] = owner.role

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserProfileSerializer(owner).data,
                "cooperative": CooperativeSerializer(cooperative).data,
            },
            status=status.HTTP_201_CREATED,
        )


class CooperativeMeView(generics.RetrieveUpdateAPIView):
    """
    Consultation (tout membre) et mise à jour (OWNER/ADMIN uniquement) des
    informations de la coopérative de l'utilisateur connecté.
    """

    permission_classes = [IsAuthenticated, IsCooperativeMember]

    def get_object(self):  # noqa: ANN201
        return self.request.user.cooperative

    def get_serializer_class(self):  # noqa: ANN201
        if self.request.method in {"PATCH", "PUT"}:
            return CooperativeUpdateSerializer
        return CooperativeSerializer

    def get_permissions(self):  # noqa: ANN201
        if self.request.method in {"PATCH", "PUT"}:
            return [IsAuthenticated(), IsCooperativeMember(), IsOwnerOrAdmin()]
        return [IsAuthenticated(), IsCooperativeMember()]

    def update(self, request: Request, *args, **kwargs) -> Response:
        response = super().update(request, *args, **kwargs)
        # On répond avec la représentation complète (lecture), pas le
        # sous-ensemble modifiable, pour que le frontend n'ait pas à
        # recharger la ressource après une sauvegarde.
        response.data = CooperativeSerializer(self.get_object()).data
        return response


class CooperativeLogoUploadView(APIView):
    """Upload/remplacement du logo de la coopérative."""

    permission_classes = [IsAuthenticated, IsCooperativeMember, IsOwnerOrAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request: Request) -> Response:
        cooperative = request.user.cooperative
        serializer = CooperativeLogoSerializer(cooperative, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CooperativeSerializer(cooperative).data, status=status.HTTP_200_OK)
