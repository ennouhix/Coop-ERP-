"""
Modèle du journal d'activité — ledger immuable, même philosophie que
StockMovement (Epic 8) et Payment (Epic 11) : uniquement des INSERT,
jamais d'UPDATE/DELETE.

Pas de GenericForeignKey vers les objets métier : target_type/target_id/
target_repr suffisent pour un journal consulté par des humains, et
évitent tout risque d'import circulaire entre apps.audit et les 13 autres
apps du projet.
"""

from __future__ import annotations

from django.db import models

from apps.core.models import TenantBaseModel


class AuditLog(TenantBaseModel):
    """
    Une entrée du journal d'activité.

    `action` est une chaîne libre suivant la convention "<module>.<événement>"
    (ex: "stock.in", "user.role_changed", "invoice.issued") plutôt qu'un
    enum Django : la liste des actions va grandir à chaque futur module, un
    choices figé forcerait une migration à chaque ajout.
    """

    actor = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=100, db_index=True)

    target_type = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    target_repr = models.CharField(
        max_length=255, blank=True, help_text="Libellé humain, ex: 'FAC-00001'."
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Détails structurés, ex: {'old_role': 'staff', 'new_role': 'admin'}.",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = "Entrée du journal d'activité"
        verbose_name_plural = "Journal d'activité"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["cooperative", "action"]),
            models.Index(fields=["cooperative", "target_type", "target_id"]),
            models.Index(fields=["cooperative", "actor"]),
        ]

    def __str__(self) -> str:
        who = self.actor.email if self.actor else "système"
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {who} — {self.action} — {self.target_repr}"
