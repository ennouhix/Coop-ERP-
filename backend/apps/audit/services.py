"""
Point d'entrée unique du journal d'activité, appelé depuis les
services.py des autres modules (authentication, users, inventory,
purchases, sales, billing).

Volontairement minimal : une seule fonction, aucune dépendance vers les
modèles métier des autres apps (uniquement des chaînes), pour rester
importable de partout sans jamais créer de cycle d'import.
"""

from __future__ import annotations

from typing import Any

from apps.audit.models import AuditLog
from apps.cooperatives.models import Cooperative


def log_activity(
    *,
    cooperative: Cooperative,
    actor: Any | None,
    action: str,
    target_type: str = "",
    target_id: str = "",
    target_repr: str = "",
    metadata: dict | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """
    Crée une entrée du journal. Appelée à l'intérieur des transactions
    métier existantes : si cet appel échoue, l'action déclenchante échoue
    aussi (cohérence assumée, voir la docstring de l'Epic 14).
    """
    return AuditLog.objects.create(
        cooperative=cooperative,
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id else "",
        target_repr=target_repr,
        metadata=metadata or {},
        ip_address=ip_address,
    )
