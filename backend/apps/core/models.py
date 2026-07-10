"""
Modèles de base partagés par toute l'application.

Toute table métier appartenant à une coopérative doit hériter de
TenantBaseModel (sauf tables globales : User, Cooperative elle-même,
tables de configuration système).
"""
from __future__ import annotations

import uuid
from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """
    Modèle abstrait de base : UUID en clé primaire, timestamps automatiques,
    soft-delete et traçabilité de création/modification.

    Justification :
    - UUID plutôt qu'auto-increment : évite l'énumération d'IDs (sécurité),
      indispensable en SaaS multi-tenant où les IDs ne doivent jamais fuiter
      d'information sur le volume de données d'un tenant.
    - Soft delete : dans un ERP, on ne supprime jamais réellement une donnée
      liée à des mouvements comptables/stock. On la désactive.
    """

    id: uuid.UUID = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_created",
        on_delete=models.SET_NULL,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_updated",
        on_delete=models.SET_NULL,
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def soft_delete(self) -> None:
        """Désactive l'enregistrement sans le supprimer physiquement."""
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_active", "deleted_at"])

    def restore(self) -> None:
        """Réactive un enregistrement précédemment soft-delete."""
        self.is_active = True
        self.deleted_at = None
        self.save(update_fields=["is_active", "deleted_at"])


class TenantManager(models.Manager):
    """
    Manager qui filtre AUTOMATIQUEMENT sur le tenant courant.

    C'est la pièce centrale de l'isolation multi-tenant : un développeur
    qui écrit `Product.objects.all()` obtient UNIQUEMENT les produits de la
    coopérative active, sans jamais avoir à y penser explicitement. Il est
    impossible d'oublier ce filtre par erreur, contrairement à un filtrage
    manuel répété dans chaque vue.
    """

    def get_queryset(self) -> models.QuerySet[Any]:
        from apps.core.context import get_current_tenant

        qs = super().get_queryset().filter(is_active=True)
        tenant = get_current_tenant()
        if tenant is not None:
            qs = qs.filter(cooperative_id=tenant)
        return qs


class TenantBaseModel(BaseModel):
    """
    Modèle abstrait pour toute donnée appartenant à une coopérative (tenant).
    Ajoute le champ `cooperative` obligatoire, indexé, et un manager filtrant.
    """

    cooperative = models.ForeignKey(
        "cooperatives.Cooperative",
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_set",
        db_index=True,
    )

    objects = TenantManager()
    all_objects = models.Manager()  # accès non filtré : scripts admin, migrations, Celery système

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["cooperative", "is_active"]),
        ]
