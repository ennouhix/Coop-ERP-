"""
Vues du module cooperatives.

Endpoints exposés (voir urls.py) :
- POST   /api/v1/cooperatives/register/      -> inscription self-service (public)
- POST   /api/v1/auth/register/              -> inscription portail : email de confirmation
- POST   /api/v1/auth/register/verify/       -> activation du compte via le lien reçu
- GET    /api/v1/cooperatives/me/            -> infos de ma coopérative
- PATCH  /api/v1/cooperatives/me/            -> mise à jour (OWNER/ADMIN uniquement)
- POST   /api/v1/cooperatives/me/logo/       -> upload du logo (OWNER/ADMIN uniquement)
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
from apps.cooperatives.models import CooperativeEmailConfig
from apps.cooperatives.serializers import (
    ActivationSerializer,
    CooperativeEmailConfigSerializer,
    CooperativeLogoSerializer,
    CooperativeRegistrationSerializer,
    CooperativeSerializer,
    CooperativeUpdateSerializer,
    EmailNotificationSerializer,
)
from apps.cooperatives.services import (
    CooperativeRegistrationData,
    InvalidActivationError,
    activate_cooperative_owner,
    register_cooperative,
    request_cooperative_registration,
)
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


class PortalRegisterView(APIView):
    """
    Inscription via le portail public. Identique à CooperativeRegisterView
    sur les données reçues, mais le compte est créé INACTIF : on n'envoie
    aucun jeton d'accès, seulement un email de confirmation. Le futur owner
    n'entrera dans l'ERP qu'après avoir cliqué le lien reçu.
    """

    permission_classes = [AllowAny]
    throttle_classes = [RegistrationRateThrottle]

    def post(self, request: Request) -> Response:
        serializer = CooperativeRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        cooperative, owner, _activation = request_cooperative_registration(
            CooperativeRegistrationData(
                cooperative_name=payload["cooperative_name"],
                owner_email=payload["owner_email"],
                owner_password=payload["owner_password"],
                owner_first_name=payload["owner_first_name"],
                owner_last_name=payload["owner_last_name"],
            )
        )

        return Response(
            {
                "message": (
                    "Un email de confirmation a été envoyé. Cliquez sur le lien "
                    "qu'il contient pour activer votre compte et commencer."
                ),
                "cooperative_name": cooperative.name,
                "email": owner.email,
            },
            status=status.HTTP_201_CREATED,
        )


class ActivateAccountView(APIView):
    """
    Valide le jeton reçu par email et active le compte owner correspondant.
    Retourne directement les tokens JWT (auto-login) pour enchaîner vers
    l'ERP sans nouvelle connexion, comme le fait l'acceptation d'invitation.
    """

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = ActivationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            owner = activate_cooperative_owner(token=serializer.validated_data["token"])
        except InvalidActivationError as exc:
            return Response(
                {"error": {"code": "invalid_token", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refresh = RefreshToken.for_user(owner)
        refresh["cooperative_id"] = str(owner.cooperative_id)
        refresh["role"] = owner.role

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserProfileSerializer(owner).data,
                "cooperative": CooperativeSerializer(owner.cooperative).data,
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

    def delete(self, request: Request) -> Response:
        cooperative = request.user.cooperative
        cooperative.logo.delete(save=False)
        cooperative.logo = None
        cooperative.save(update_fields=["logo"])
        return Response(CooperativeSerializer(cooperative).data, status=status.HTTP_200_OK)


class CooperativeEmailConfigView(generics.RetrieveUpdateAPIView):
    """
    Configuration SMTP de la coopérative.

    GET  : lecture des paramètres email (mot de passe masqué).
    PUT  : mise à jour complète.
    PATCH : mise à jour partielle.
    """

    permission_classes = [IsAuthenticated, IsCooperativeMember, IsOwnerOrAdmin]
    serializer_class = CooperativeEmailConfigSerializer

    def get_object(self):  # noqa: ANN201
        coop = self.request.user.cooperative
        obj, _created = CooperativeEmailConfig.objects.get_or_create(cooperative=coop)
        return obj

    def get_permissions(self):  # noqa: ANN201
        if self.request.method in {"PUT", "PATCH"}:
            return [IsAuthenticated(), IsCooperativeMember(), IsOwnerOrAdmin()]
        return [IsAuthenticated(), IsCooperativeMember()]


class CooperativeEmailTestView(APIView):
    """Test de connexion SMTP avec les paramètres fournis."""

    permission_classes = [IsAuthenticated, IsCooperativeMember, IsOwnerOrAdmin]

    def post(self, request: Request) -> Response:
        import smtplib

        coop = request.user.cooperative
        config, _created = CooperativeEmailConfig.objects.get_or_create(cooperative=coop)
        serializer = CooperativeEmailConfigSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        host = data.get("smtp_host", config.smtp_host)
        port = data.get("smtp_port", config.smtp_port)
        username = data.get("smtp_username", config.smtp_username)
        password = data.get("smtp_password", config.smtp_password)
        use_tls = data.get("smtp_use_tls", config.smtp_use_tls)

        if not host:
            return Response(
                {"success": False, "message": "Le serveur SMTP est obligatoire."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if use_tls:
                server = smtplib.SMTP(host, port, timeout=10)
                server.starttls()
            else:
                server = smtplib.SMTP(host, port, timeout=10)

            if username and password:
                server.login(username, password)

            server.quit()
            return Response({"success": True, "message": "Connexion réussie."})
        except smtplib.SMTPAuthenticationError:
            msg = (
                "Échec de l'authentification. "
                "Vérifiez l'utilisateur et le mot de passe."
            )
            return Response(
                {"success": False, "message": msg},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except smtplib.SMTPConnectError:
            return Response(
                {
                    "success": False,
                    "message": f"Impossible de se connecter à {host}:{port}.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            return Response(
                {"success": False, "message": f"Erreur de connexion : {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class EmailNotificationListView(generics.ListAPIView):
    """
    Journal des emails envoyés par la coopérative.

    Filtrable par type et statut via query params.
    """

    permission_classes = [IsAuthenticated, IsCooperativeMember, IsOwnerOrAdmin]
    serializer_class = EmailNotificationSerializer
    pagination_class = None

    def get_queryset(self):  # noqa: ANN201
        from apps.cooperatives.models import EmailNotification

        qs = EmailNotification.objects.filter(
            cooperative=self.request.user.cooperative
        )
        nt = self.request.query_params.get("notification_type")
        if nt:
            qs = qs.filter(notification_type=nt)
        st = self.request.query_params.get("status")
        if st:
            qs = qs.filter(status=st)
        return qs[:100]
