"""
Matrice de permissions par rôle — fondation RBAC réutilisée par TOUS les
futurs modules métier (stock, ventes, achats, facturation...).

Choix d'architecture assumé : une matrice statique en code plutôt qu'un
modèle `Permission` en base de données. Justification :
- Les rôles (OWNER/ADMIN/STAFF/ACCOUNTANT) sont fixes et peu nombreux en V1,
  pas de besoin de rôles custom créés dynamiquement par le client.
- Une matrice en code est versionnée avec le code (revue de PR obligatoire
  pour changer une permission), alors qu'une table modifiable en admin
  serait une surface d'attaque si un accès admin est compromis.
- Zéro requête DB supplémentaire pour vérifier une permission.

Évolution prévue (documentée en fin d'Epic) : si des coopératives
demandent des rôles personnalisés, migrer vers un modèle `Permission`
en base sans casser l'API `has_permission(role, code)` ci-dessous.
"""
from __future__ import annotations

from apps.authentication.models import UserRole

# Format des codes : "<module>.<action>". Chaque futur module (Epic 6+)
# enregistrera ses propres codes ici au fur et à mesure de sa construction.
PERMISSIONS_MATRIX: dict[str, set[str]] = {
    UserRole.OWNER: {"*"},  # OWNER a tous les droits, toujours.
    UserRole.ADMIN: {
        "users.view", "users.invite", "users.edit_role", "users.deactivate",
        "cooperative.view", "cooperative.edit",
        "members.view", "members.edit",
        "partners.view", "partners.edit",
        "catalog.view", "catalog.edit",
        "stock.view", "stock.edit",
        "purchases.view", "purchases.edit",
        "sales.view", "sales.edit",
        "billing.view", "billing.edit",
        "reports.view",
    },
    UserRole.ACCOUNTANT: {
        "users.view",
        "cooperative.view",
        "members.view",
        "partners.view", "partners.edit",
        "catalog.view",
        "stock.view",
        "purchases.view",
        "sales.view",
        "billing.view", "billing.edit",
        "reports.view",
    },
    UserRole.STAFF: {
        "users.view",
        "cooperative.view",
        "members.view", "members.edit",
        "partners.view", "partners.edit",
        "catalog.view",
        "stock.view",
        "sales.view", "sales.edit",
    },
}


def has_permission(role: str, code: str) -> bool:
    """Vérifie si un rôle donné possède le code de permission demandé."""
    allowed = PERMISSIONS_MATRIX.get(role, set())
    return "*" in allowed or code in allowed
