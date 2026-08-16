"""
Logique métier de création de coopérative.

La création d'une coopérative et de son premier utilisateur (OWNER) doit
être atomique : on ne veut jamais d'une coopérative sans propriétaire, ni
d'un utilisateur OWNER sans coopérative valide derrière lui.

Deux parcours coexistent :
- `register_cooperative`            : création immédiate, compte owner actif
  tout de suite (inscription historique, retourne des tokens JWT).
- `request_cooperative_registration`: parcours portail — le compte owner est
  créé INACTIF en attendant que la personne valide son email via le lien
  reçu. `activate_cooperative_owner` active ensuite le compte.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.audit.services import log_activity
from apps.authentication.models import UserRole
from apps.cooperatives.models import (
    ACTIVATION_VALIDITY_DAYS,
    ActivationStatus,
    Cooperative,
    CooperativeActivation,
)

User = get_user_model()


@dataclass(frozen=True)
class CooperativeRegistrationData:
    cooperative_name: str
    owner_email: str
    owner_password: str
    owner_first_name: str
    owner_last_name: str


def generate_unique_slug(name: str) -> str:
    """
    Génère un slug unique à partir du nom. En cas de collision (deux
    coopératives au nom identique ou très proche), ajoute un suffixe
    numérique incrémental plutôt que de faire échouer l'inscription.
    """
    base_slug = slugify(name)[:240] or "cooperative"
    slug = base_slug
    suffix = 1
    while Cooperative.objects.filter(slug=slug).exists():
        suffix += 1
        slug = f"{base_slug}-{suffix}"
    return slug


@transaction.atomic
def register_cooperative(data: CooperativeRegistrationData) -> tuple[Cooperative, User]:
    """
    Crée la coopérative puis son utilisateur OWNER dans la même transaction.
    Toute exception ici annule les deux créations (rollback complet).
    """
    cooperative = Cooperative.objects.create(
        name=data.cooperative_name,
        slug=generate_unique_slug(data.cooperative_name),
    )

    owner = User.objects.create_user(
        username=data.owner_email,  # pas de username séparé en V1, on réutilise l'email
        email=data.owner_email,
        password=data.owner_password,
        first_name=data.owner_first_name,
        last_name=data.owner_last_name,
        cooperative=cooperative,
        role=UserRole.OWNER,
    )

    return cooperative, owner


class InvalidActivationError(Exception):
    """Levée quand un jeton d'activation est inconnu, expiré ou déjà utilisé."""


@transaction.atomic
def request_cooperative_registration(
    data: CooperativeRegistrationData,
) -> tuple[Cooperative, User, CooperativeActivation]:
    """
    Parcours portail : crée coopérative + owner INACTIF + jeton d'activation,
    puis envoie l'email de confirmation. Le compte ne sera activable qu'avec
    le lien reçu (validation de l'email en deux étapes).
    """
    cooperative = Cooperative.objects.create(
        name=data.cooperative_name,
        slug=generate_unique_slug(data.cooperative_name),
    )

    owner = User.objects.create_user(
        username=data.owner_email,
        email=data.owner_email,
        password=data.owner_password,
        first_name=data.owner_first_name,
        last_name=data.owner_last_name,
        cooperative=cooperative,
        role=UserRole.OWNER,
        is_active=False,  # en attente de validation de l'email
    )

    activation = CooperativeActivation.objects.create(cooperative=cooperative, user=owner)

    _send_activation_email(activation)

    log_activity(
        cooperative=cooperative,
        actor=owner,
        action="cooperative.registration_requested",
        target_type="Cooperative",
        target_id=cooperative.id,
        target_repr=cooperative.name,
        metadata={"email": owner.email},
    )

    return cooperative, owner, activation


def _send_activation_email(activation: CooperativeActivation) -> None:
    link = f"{settings.FRONTEND_URL}/activate-account?token={activation.token}"
    send_cooperative_email(
        cooperative=activation.cooperative,
        subject=f"Activez votre compte — {activation.cooperative.name}",
        message=(
            f"Bonjour {activation.user.first_name},\n\n"
            f"Votre coopérative « {activation.cooperative.name} » a été créée sur Coop-ERP. "
            f"Pour activer votre compte et commencer à travailler, "
            f"cliquez sur ce lien (valable {ACTIVATION_VALIDITY_DAYS} jours) :\n\n"
            f"{link}\n\n"
            "Si vous n'êtes pas à l'origine de cette inscription, ignorez cet email."
        ),
        recipient_list=[activation.user.email],
    )


def send_cooperative_email(
    *,
    cooperative,
    subject: str,
    message: str,
    recipient_list: list[str],
    from_email: str | None = None,
    html_message: str | None = None,
    attachments: list[tuple[str, bytes, str]] | None = None,
) -> None:
    """
    Envoie un email en utilisant la config SMTP de la coopérative si elle
    existe et est active, sinon utilise le backend Django global.

    ``attachments`` est une liste de tuples ``(filename, content, mimetype)``
    pour joindre des fichiers (ex: un PDF de facture).
    """
    from apps.cooperatives.models import CooperativeEmailConfig

    try:
        config = CooperativeEmailConfig.objects.get(cooperative=cooperative)
    except CooperativeEmailConfig.DoesNotExist:
        config = None

    if config and config.is_configured and config.smtp_host and config.from_email:
        _send_via_cooperative_smtp(
            config=config,
            subject=subject,
            message=message,
            recipient_list=recipient_list,
            from_email=from_email,
            html_message=html_message,
            attachments=attachments,
        )
    else:
        from django.core.mail import EmailMessage

        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=from_email,
            to=recipient_list,
        )
        if html_message:
            email.content_subtype = "alternative"
            email.body = ""
            from email.mime.text import MIMEText

            plain_part = MIMEText(message, "plain", "utf-8")
            html_part = MIMEText(html_message, "html", "utf-8")
            email.msg_alternative = [plain_part, html_part]
            email.body = message

        for filename, content, mimetype in (attachments or []):
            email.attach(filename, content, mimetype)

        email.send(fail_silently=False)


def _send_via_cooperative_smtp(
    *,
    config,
    subject: str,
    message: str,
    recipient_list: list[str],
    from_email: str | None = None,
    html_message: str | None = None,
    attachments: list[tuple[str, bytes, str]] | None = None,
) -> None:
    """Envoie un email via le serveur SMTP configuré pour la coopérative."""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    sender = from_email or config.from_email
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipient_list)

    msg.attach(MIMEText(message, "plain", "utf-8"))
    if html_message:
        msg.attach(MIMEText(html_message, "html", "utf-8"))

    for filename, content, _mimetype in (attachments or []):
        from email import encoders
        from email.mime.base import MIMEBase

        part = MIMEBase("application", "octet-stream")
        part.set_payload(content)
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{filename}"',
        )
        msg.attach(part)

    if config.smtp_use_tls:
        server = smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=15)
        server.starttls()
    else:
        server = smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=15)

    try:
        if config.smtp_username and config.smtp_password:
            server.login(config.smtp_username, config.smtp_password)
        server.sendmail(sender, recipient_list, msg.as_string())
    finally:
        server.quit()


@transaction.atomic
def activate_cooperative_owner(*, token: str) -> User:
    """
    Active le compte owner associé au jeton, s'il est valide (pending, non
    expiré). Le jeton devient à usage unique : une fois utilisé, il ne peut
    plus servir, même avec un email relu.
    """
    activation = CooperativeActivation.objects.filter(
        token=token, status=ActivationStatus.PENDING
    ).first()
    if activation is None:
        raise InvalidActivationError("Ce lien d'activation est invalide ou a déjà été utilisé.")
    if activation.is_expired:
        raise InvalidActivationError("Ce lien d'activation a expiré.")

    owner = activation.user
    owner.is_active = True
    owner.save(update_fields=["is_active"])

    activation.status = ActivationStatus.USED
    activation.activated_at = timezone.now()
    activation.save(update_fields=["status", "activated_at", "updated_at"])

    log_activity(
        cooperative=activation.cooperative,
        actor=owner,
        action="cooperative.registration_activated",
        target_type="User",
        target_id=owner.id,
        target_repr=owner.email,
    )

    return owner
