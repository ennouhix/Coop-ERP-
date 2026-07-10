"""
Modèle Cooperative — le tenant racine du système.

Enrichi à l'Epic 2 : informations légales marocaines (ICE, RC), adresse,
logo, et cycle de vie de l'abonnement (essai gratuit puis plans payants).
"""
from __future__ import annotations

from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel
from apps.cooperatives.validators import ice_validator, phone_validator

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


def default_trial_end() -> "timezone.datetime":
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
        max_length=255, blank=True, help_text="Raison sociale officielle si différente du nom usuel."
    )
    ice = models.CharField(
        "ICE", max_length=15, blank=True, validators=[ice_validator],
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
    default_language = models.CharField(max_length=2, choices=[("fr", "Français"), ("ar", "العربية")], default="fr")

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
        return self.subscription_status == SubscriptionStatus.TRIAL and timezone.now() > self.trial_ends_at

