"""
Stockage du tenant courant dans le contexte de la requête (contextvars).
Utilise contextvars plutôt que threading.local car compatible async
(Django ASGI, Celery, futurs workers async).
"""

from __future__ import annotations

import contextvars
from uuid import UUID

_current_tenant: contextvars.ContextVar[UUID | None] = contextvars.ContextVar(
    "current_tenant", default=None
)


def set_current_tenant(tenant_id: UUID | None) -> None:
    """Définit le tenant actif pour le contexte d'exécution courant."""
    _current_tenant.set(tenant_id)


def get_current_tenant() -> UUID | None:
    """Retourne le tenant actif, ou None si aucun (ex: tâche système)."""
    return _current_tenant.get()
