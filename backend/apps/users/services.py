"""
Logique métier du module users : invitations et garde-fous sur les rôles.

Le garde-fou "dernier OWNER" est centralisé ici pour être appliqué de
façon identique partout où un rôle/statut peut changer (édition de rôle,
désactivation) — jamais dupliqué dans les vues.
"""
from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from apps.audit.services import log_activity
from apps.authentication.models import UserRole
from apps.users.models import Invitation, InvitationStatus

User = get_user_model()


class TeamManagementError(Exception):
    """Erreur métier générique du module (message destiné à être affiché tel quel)."""


class InvalidInvitationError(Exception):
    """Token d'invitation invalide, expiré, ou déjà utilisé."""


def _assert_not_last_owner(user) -> None:  # noqa: ANN001
    """
    Empêche de désactiver ou de rétrograder le dernier OWNER d'une
    coopérative. Sans ce garde-fou, une coopérative pourrait se retrouver
    sans aucun propriétaire, la rendant impossible à administrer.
    """
    if user.role != UserRole.OWNER:
        return
    other_owners = User.objects.filter(
        cooperative_id=user.cooperative_id, role=UserRole.OWNER, is_active=True
    ).exclude(pk=user.pk)
    if not other_owners.exists():
        raise TeamManagementError(
            "Impossible de modifier ce compte : c'est le dernier propriétaire de la coopérative."
        )


def change_user_role(*, actor, target_user, new_role: str) -> None:  # noqa: ANN001
    """
    Change le rôle de `target_user`. `actor` est l'utilisateur qui effectue
    l'action (déjà vérifié OWNER/ADMIN au niveau permission DRF, mais les
    règles fines OWNER-only sont vérifiées ici, au plus près de la donnée).
    """
    if target_user.pk == actor.pk:
        raise TeamManagementError("Vous ne pouvez pas modifier votre propre rôle.")

    if actor.role != UserRole.OWNER and (
        target_user.role == UserRole.OWNER or new_role == UserRole.OWNER
    ):
        raise TeamManagementError("Seul un propriétaire peut attribuer ou modifier le rôle propriétaire.")

    if new_role != UserRole.OWNER:
        _assert_not_last_owner(target_user)

    old_role = target_user.role
    target_user.role = new_role
    target_user.save(update_fields=["role"])

    log_activity(
        cooperative=target_user.cooperative, actor=actor, action="user.role_changed",
        target_type="User", target_id=target_user.id, target_repr=target_user.email,
        metadata={"old_role": old_role, "new_role": new_role},
    )


def deactivate_user(*, actor, target_user) -> None:  # noqa: ANN001
    if target_user.pk == actor.pk:
        raise TeamManagementError("Vous ne pouvez pas vous désactiver vous-même.")

    if actor.role != UserRole.OWNER and target_user.role == UserRole.OWNER:
        raise TeamManagementError("Seul un propriétaire peut désactiver un autre propriétaire.")

    _assert_not_last_owner(target_user)
    target_user.is_active = False
    target_user.save(update_fields=["is_active"])

    log_activity(
        cooperative=target_user.cooperative, actor=actor, action="user.deactivated",
        target_type="User", target_id=target_user.id, target_repr=target_user.email,
    )


def reactivate_user(*, target_user) -> None:  # noqa: ANN001
    target_user.is_active = True
    target_user.save(update_fields=["is_active"])


@transaction.atomic
def create_invitation(*, actor, cooperative, email: str, role: str) -> Invitation:  # noqa: ANN001
    email = email.lower().strip()

    if User.objects.filter(cooperative=cooperative, email__iexact=email, is_active=True).exists():
        raise TeamManagementError("Cette personne est déjà membre de la coopérative.")

    if Invitation.objects.filter(
        cooperative=cooperative, email__iexact=email, status=InvitationStatus.PENDING
    ).exists():
        raise TeamManagementError("Une invitation est déjà en attente pour cet email.")

    if role == UserRole.OWNER and actor.role != UserRole.OWNER:
        raise TeamManagementError("Seul un propriétaire peut inviter un autre propriétaire.")

    invitation = Invitation.objects.create(
        cooperative=cooperative, email=email, role=role, invited_by=actor
    )
    _send_invitation_email(invitation)

    log_activity(
        cooperative=cooperative, actor=actor, action="user.invited",
        target_type="Invitation", target_id=invitation.id, target_repr=invitation.email,
        metadata={"role": role},
    )

    return invitation


def _send_invitation_email(invitation: Invitation) -> None:
    link = f"{settings.FRONTEND_URL}/accept-invitation?token={invitation.token}"
    send_mail(
        subject=f"Invitation à rejoindre {invitation.cooperative.name} — Coop ERP",
        message=(
            f"Vous avez été invité(e) à rejoindre {invitation.cooperative.name} "
            f"en tant que {invitation.get_role_display()}.\n\n"
            f"Cliquez sur ce lien pour créer votre compte (valable 7 jours) :\n{link}\n\n"
            "Si vous ne connaissez pas l'origine de cette invitation, ignorez cet email."
        ),
        from_email=None,
        recipient_list=[invitation.email],
        fail_silently=False,
    )


@transaction.atomic
def accept_invitation(*, token: str, password: str, first_name: str, last_name: str) -> "User":
    invitation = Invitation.objects.filter(token=token, status=InvitationStatus.PENDING).first()
    if invitation is None:
        raise InvalidInvitationError("Invitation invalide ou déjà utilisée.")
    if invitation.is_expired:
        raise InvalidInvitationError("Cette invitation a expiré.")
    if User.objects.filter(email__iexact=invitation.email).exists():
        raise InvalidInvitationError("Un compte existe déjà avec cet email.")

    user = User.objects.create_user(
        username=invitation.email,
        email=invitation.email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        cooperative=invitation.cooperative,
        role=invitation.role,
    )

    invitation.status = InvitationStatus.ACCEPTED
    invitation.accepted_at = timezone.now()
    invitation.save(update_fields=["status", "accepted_at"])

    return user


def cancel_invitation(*, invitation: Invitation) -> None:
    invitation.status = InvitationStatus.CANCELLED
    invitation.save(update_fields=["status"])
