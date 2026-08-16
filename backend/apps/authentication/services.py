"""
Logique métier de réinitialisation de mot de passe.

Réutilise PasswordResetTokenGenerator de Django (même mécanisme que
l'admin Django) : le token encode un hash dépendant du mot de passe actuel
et de la dernière connexion, donc il devient automatiquement invalide dès
que l'utilisateur se connecte ou change son mot de passe entre-temps.

Règle de sécurité importante : on ne révèle JAMAIS si un email existe ou
non dans la base (`request_password_reset` retourne toujours succès côté
API), pour ne pas permettre l'énumération des comptes existants.
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

User = get_user_model()
logger = logging.getLogger(__name__)

token_generator = PasswordResetTokenGenerator()


def request_password_reset(email: str) -> None:
    """
    Envoie un email de réinitialisation si le compte existe.
    Ne lève jamais d'erreur et ne révèle jamais si l'email est inconnu.
    """
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user is None:
        logger.info("Demande de reset pour un email inconnu ou inactif : %s", email)
        return

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = token_generator.make_token(user)
    reset_link = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"

    from apps.cooperatives.services import send_cooperative_email

    send_cooperative_email(
        cooperative=getattr(user, "cooperative", None),
        subject="Réinitialisation de votre mot de passe — Coop ERP",
        message=(
            f"Bonjour {user.first_name or user.email},\n\n"
            f"Cliquez sur ce lien pour réinitialiser votre mot de passe "
            f"(valable 1 heure) :\n{reset_link}\n\n"
            "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email."
        ),
        recipient_list=[user.email],
    )


class InvalidResetTokenError(Exception):
    """Levée quand le couple (uid, token) est invalide, expiré, ou déjà utilisé."""


def confirm_password_reset(uid: str, token: str, new_password: str) -> None:
    """Valide le token et applique le nouveau mot de passe."""
    try:
        user_pk = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_pk, is_active=True)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError) as exc:
        raise InvalidResetTokenError("Lien de réinitialisation invalide.") from exc

    if not token_generator.check_token(user, token):
        raise InvalidResetTokenError("Lien de réinitialisation invalide ou expiré.")

    user.set_password(new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    user.save(update_fields=["password", "failed_login_attempts", "locked_until"])

    _blacklist_all_tokens_for(user)


def _blacklist_all_tokens_for(user) -> None:  # noqa: ANN001
    """Révoque tous les refresh tokens actifs après un reset (précaution sécurité)."""
    from rest_framework_simplejwt.exceptions import TokenError
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
    from rest_framework_simplejwt.tokens import RefreshToken

    for outstanding in OutstandingToken.objects.filter(user=user):
        try:
            RefreshToken(outstanding.token).blacklist()
        except TokenError:
            continue
