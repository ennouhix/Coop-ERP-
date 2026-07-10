"""
Modèle User custom.

Note d'architecture : le RBAC détaillé (rôles personnalisés, permissions
granulaires par module) arrive à l'Epic 3 avec un modèle `Role` dédié.
Le champ `role` ici est un RBAC minimal (choix fixes) suffisant pour
démarrer l'authentification et le filtrage de base dès l'Epic 1, sans
bloquer les autres modules qui ont besoin de savoir "qui peut faire quoi"
en attendant l'Epic 3.
"""
from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    OWNER = "owner", "Propriétaire / Gérant"
    ADMIN = "admin", "Administrateur"
    STAFF = "staff", "Employé"
    ACCOUNTANT = "accountant", "Comptable"


class User(AbstractUser):
    """
    Utilisateur de la plateforme. Rattaché à UNE coopérative (un utilisateur
    ne travaille que pour une seule coopérative dans la V1). C'est ce
    `cooperative_id` que TenantMiddleware lit pour résoudre le tenant actif
    à chaque requête, et que le JWT embarque comme claim.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    cooperative = models.ForeignKey(
        "cooperatives.Cooperative",
        on_delete=models.CASCADE,
        related_name="users",
        null=True,   # null uniquement pour un superadmin plateforme (équipe support interne)
        blank=True,
    )
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.STAFF)
    phone_number = models.CharField(max_length=20, blank=True)
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self) -> str:
        return self.email
