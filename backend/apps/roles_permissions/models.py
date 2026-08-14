"""
Modèle de permissions par rôle, personnalisable par coopérative.

La matrice statique `matrix.PERMISSIONS_MATRIX` reste la valeur par défaut
(zéro requête DB, versionnée avec le code). Ce modèle ne stocke que les
surcharges décidées depuis le panneau d'administration : dès qu'une ou
plusieurs lignes existent pour un couple (cooperative, role), elles
remplacent intégralement la matrice pour ce rôle ; sinon la matrice
s'applique. L'OWNER conserve toujours un accès complet ("*").
"""
from __future__ import annotations

from django.db import models

from apps.authentication.models import UserRole
from apps.core.models import TenantBaseModel


class RoleModuleAccess(TenantBaseModel):
    """Un accès accordé : un rôle donné peut utiliser un module métier."""

    role = models.CharField(max_length=20, choices=UserRole.choices)
    module = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Accès module par rôle"
        verbose_name_plural = "Accès modules par rôle"
        ordering = ["role", "module"]
        constraints = [
            models.UniqueConstraint(
                fields=["cooperative", "role", "module"],
                name="unique_role_module_per_cooperative",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.role} -> {self.module}"
