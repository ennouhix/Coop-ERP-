"""
Vues du module authentification.

Endpoints exposés (voir urls.py) :
- POST   /api/v1/auth/login/            -> obtenir access + refresh token
- POST   /api/v1/auth/refresh/          -> renouveler l'access token
- POST   /api/v1/auth/logout/           -> blacklister le refresh token
- GET    /api/v1/auth/me/               -> profil de l'utilisateur connecté
- PATCH  /api/v1/auth/me/               -> mise à jour partielle du profil
- POST   /api/v1/auth/password/change/  -> changer son mot de passe
"""

from __future__ import annotations

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.audit.services import log_activity
from apps.authentication import services
from apps.authentication.models import User
from apps.authentication.serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserProfileSerializer,
)
from apps.authentication.throttling import LoginRateThrottle, PasswordResetRateThrottle


class LoginView(TokenObtainPairView):
    """Authentifie un utilisateur et retourne un couple access/refresh token."""

    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]

    def post(self, request: Request, *args, **kwargs) -> Response:
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            email = request.data.get("email")
            user = User.objects.filter(email__iexact=email).first() if email else None
            if user is not None and user.cooperative_id:
                log_activity(
                    cooperative=user.cooperative,
                    actor=user,
                    action="user.login",
                    target_type="User",
                    target_id=user.id,
                    target_repr=user.email,
                    ip_address=request.META.get("REMOTE_ADDR"),
                )
        return response


class LogoutView(APIView):
    """
    Invalide le refresh token fourni (blacklist), pour que la déconnexion
    soit réelle et immédiate — pas seulement "le client a oublié le token".
    Un token blacklisté est refusé par TokenRefreshView même s'il n'a pas
    encore expiré.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": {"code": "missing_field", "message": "Le champ 'refresh' est requis."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return Response(
                {
                    "error": {
                        "code": "invalid_token",
                        "message": "Token de rafraîchissement invalide.",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.user.cooperative_id:
            log_activity(
                cooperative=request.user.cooperative,
                actor=request.user,
                action="user.logout",
                target_type="User",
                target_id=request.user.id,
                target_repr=request.user.email,
            )

        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    """Consultation et mise à jour du profil de l'utilisateur connecté."""

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):  # noqa: ANN201
        return self.request.user


class ChangePasswordView(APIView):
    """
    Change le mot de passe de l'utilisateur connecté et blackliste tous ses
    refresh tokens actifs (RG-5) : un token émis avant le changement de mot
    de passe ne doit plus permettre de se maintenir connecté indéfiniment,
    notamment si le changement fait suite à une suspicion de compromission.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        self._blacklist_all_tokens_for(user)

        return Response({"message": "Mot de passe modifié avec succès."}, status=status.HTTP_200_OK)

    @staticmethod
    def _blacklist_all_tokens_for(user) -> None:  # noqa: ANN001
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

        outstanding_tokens = OutstandingToken.objects.filter(user=user)
        for outstanding in outstanding_tokens:
            try:
                RefreshToken(outstanding.token).blacklist()
            except TokenError:
                continue


class PasswordResetRequestView(APIView):
    """
    Déclenche l'envoi d'un email de réinitialisation. Toujours 200, que
    l'email existe ou non (anti-énumération de comptes), throttlé pour
    éviter le spam d'emails vers une victime.
    """

    permission_classes: list = []
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request: Request) -> Response:
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.request_password_reset(serializer.validated_data["email"])
        return Response(
            {"message": "Si ce compte existe, un email de réinitialisation a été envoyé."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """Applique le nouveau mot de passe après validation du lien reçu par email."""

    permission_classes: list = []

    def post(self, request: Request) -> Response:
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            services.confirm_password_reset(
                uid=serializer.validated_data["uid"],
                token=serializer.validated_data["token"],
                new_password=serializer.validated_data["new_password"],
            )
        except services.InvalidResetTokenError as exc:
            return Response(
                {"error": {"code": "invalid_token", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": "Mot de passe réinitialisé avec succès."}, status=status.HTTP_200_OK
        )
