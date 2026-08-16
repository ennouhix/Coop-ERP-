"""
Modèle Cooperative — le tenant racine du système.

Enrichi à l'Epic 2 : informations légales marocaines (ICE, RC), adresse,
logo, et cycle de vie de l'abonnement (essai gratuit puis plans payants).
"""

from __future__ import annotations

import secrets
from decimal import Decimal

from django.db import models
from django.utils import timezone

from apps.cooperatives.validators import ice_validator, phone_validator
from apps.core.models import BaseModel, TenantBaseModel

TRIAL_DURATION_DAYS = 14


class SubscriptionPlan(models.TextChoices):
    TRIAL = "trial", "Essai gratuit"
    BASIC = "basic", "Basique"
    PRO = "pro", "Pro"


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "active", "Actif"
    TRIAL = "trial", "En période d'essai"
    SUSPENDED = "suspended", "Suspendu"
    CANCELLED = "cancelled", "Résilié"


def default_trial_end() -> timezone.datetime:
    return timezone.now() + timezone.timedelta(days=TRIAL_DURATION_DAYS)


class Cooperative(BaseModel):
    """
    Représente une coopérative cliente (un tenant). N'hérite PAS de
    TenantBaseModel car elle EST le tenant, elle n'appartient pas à un tenant.
    """

    # --- Identité ---
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True, editable=False)
    logo = models.ImageField(upload_to="cooperatives/logos/", null=True, blank=True)

    # --- Informations légales (Maroc) ---
    legal_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Raison sociale officielle si différente du nom usuel.",
    )
    ice = models.CharField(
        "ICE",
        max_length=15,
        blank=True,
        validators=[ice_validator],
        help_text="Identifiant Commun de l'Entreprise (15 chiffres).",
    )
    rc_number = models.CharField("Registre de Commerce", max_length=50, blank=True)

    # --- Contact & adresse ---
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True, validators=[phone_validator])
    address = models.CharField(max_length=500, blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)

    # --- Préférences ---
    default_language = models.CharField(
        max_length=2, choices=[("fr", "Français"), ("ar", "العربية")], default="fr"
    )
    share_value = models.DecimalField(
        "Valeur de la part sociale",
        max_digits=12,
        decimal_places=2,
        default=Decimal("100.00"),
        help_text="Valeur nominale d'une part sociale (MAD).",
    )

    # --- Abonnement ---
    subscription_plan = models.CharField(
        max_length=10, choices=SubscriptionPlan.choices, default=SubscriptionPlan.TRIAL
    )
    subscription_status = models.CharField(
        max_length=10, choices=SubscriptionStatus.choices, default=SubscriptionStatus.TRIAL
    )
    trial_ends_at = models.DateTimeField(default=default_trial_end)

    class Meta:
        verbose_name = "Coopérative"
        verbose_name_plural = "Coopératives"

    def __str__(self) -> str:
        return self.name

    @property
    def is_trial_expired(self) -> bool:
        return (
            self.subscription_status == SubscriptionStatus.TRIAL
            and timezone.now() > self.trial_ends_at
        )


ACTIVATION_VALIDITY_DAYS = 7


def generate_activation_token() -> str:
    """Token opaque à usage unique, non devinable (256 bits d'entropie)."""
    return secrets.token_urlsafe(32)


def default_activation_expiry() -> timezone.datetime:
    return timezone.now() + timezone.timedelta(days=ACTIVATION_VALIDITY_DAYS)


class CooperativeEmailConfig(TenantBaseModel):
    """
    Configuration SMTP d'une coopérative.

    Permet à chaque coopérative d'envoyer des emails avec ses propres
    identifiants SMTP (invitation, activation, notifications...).
    Le mot de passe est chiffré avant stockage via Fernet.
    """

    # --- Serveur SMTP ---
    smtp_host = models.CharField("Serveur SMTP", max_length=255, blank=True)
    smtp_port = models.PositiveIntegerField("Port SMTP", default=587)
    smtp_username = models.CharField("Utilisateur SMTP", max_length=255, blank=True)
    smtp_password = models.CharField("Mot de passe SMTP", max_length=500, blank=True)
    smtp_use_tls = models.BooleanField("Utiliser TLS", default=True)

    # --- Expéditeur ---
    from_name = models.CharField(
        "Nom de l'expéditeur",
        max_length=255,
        blank=True,
        help_text="Nom affiché dans les emails envoyés (ex: Ma Coopérative).",
    )
    from_email = models.EmailField(
        "Adresse de l'expéditeur",
        blank=True,
        help_text="Adresse email source (ex: noreply@ma-cooperative.com).",
    )

    # --- Statut ---
    is_configured = models.BooleanField(
        "Configuration active",
        default=False,
        help_text="Coché pour utiliser cette config SMTP au lieu du serveur global.",
    )

    class Meta:
        verbose_name = "Configuration email"
        verbose_name_plural = "Configurations email"
        indexes = [models.Index(fields=["cooperative"])]

    def __str__(self) -> str:
        status = "active" if self.is_configured else "inactive"
        return f"Email({self.cooperative.name}, {status})"

    @property
    def display_from(self) -> str:
        """Retourne l'adresse complète expéditeur au format 'Nom <email>'."""
        if self.from_name and self.from_email:
            return f"{self.from_name} <{self.from_email}>"
        return self.from_email or ""


class EmailNotificationStatus(models.TextChoices):
    PENDING = "pending", "En attente"
    SENT = "sent", "Envoyé"
    FAILED = "failed", "Échoué"


class EmailNotificationType(models.TextChoices):
    INVOICE_ISSUED = "invoice_issued", "Facture émise"
    PAYMENT_RECEIVED = "payment_received", "Paiement reçu"
    CONTRIBUTION_PENDING = "contribution_pending", "Cotisation en attente"
    OVERDUE_REMINDER = "overdue_reminder", "Rappel de retard"
    INVITATION = "invitation", "Invitation"
    ACTIVATION = "activation", "Activation de compte"
    PASSWORD_RESET = "password_reset", "Réinitialisation de mot de passe"


class EmailNotification(TenantBaseModel):
    """
    Journal des emails envoyés par les coopératives.

    Chaque enregistrement correspond à un email effectivement envoyé (ou en
    attente/échoué). Permet de tracer l'historique des notifications dans
    l'interface d'administration.
    """

    notification_type = models.CharField(
        max_length=30,
        choices=EmailNotificationType.choices,
    )
    recipient_email = models.EmailField("Destinataire")
    recipient_name = models.CharField("Nom du destinataire", max_length=255, blank=True)
    subject = models.CharField("Objet", max_length=500)
    status = models.CharField(
        max_length=10,
        choices=EmailNotificationStatus.choices,
        default=EmailNotificationStatus.PENDING,
    )
    error_message = models.TextField("Message d'erreur", blank=True)
    metadata = models.JSONField("Métadonnées", default=dict, blank=True)

    class Meta:
        verbose_name = "Notification email"
        verbose_name_plural = "Notifications email"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["cooperative", "status"]),
            models.Index(fields=["cooperative", "notification_type"]),
        ]

    def __str__(self) -> str:
        return (
            f"Email({self.notification_type}, {self.recipient_email}, "
            f"{self.status})"
        )


class ActivationStatus(models.TextChoices):
    PENDING = "pending", "En attente"
    USED = "used", "Utilisé"


class CooperativeActivation(TenantBaseModel):
    """
    Jeton d'activation d'un compte owner créé via le portail public.

    Le compte owner est créé inactif (is_active=False) tant que la personne
    n'a pas cliqué le lien reçu par email. Ce modèle porte le jeton à usage
    unique et sa date d'expiration — même mécanisme que Invitation.
    """

    user = models.OneToOneField(
        "authentication.User", on_delete=models.CASCADE, related_name="activation"
    )
    token = models.CharField(
        max_length=64, unique=True, default=generate_activation_token, editable=False
    )
    status = models.CharField(
        max_length=10, choices=ActivationStatus.choices, default=ActivationStatus.PENDING
    )
    expires_at = models.DateTimeField(default=default_activation_expiry)
    activated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Activation de compte"
        verbose_name_plural = "Activations de comptes"
        indexes = [models.Index(fields=["cooperative", "status"])]

    def __str__(self) -> str:
        return f"Activation({self.user.email}, {self.status})"

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at
