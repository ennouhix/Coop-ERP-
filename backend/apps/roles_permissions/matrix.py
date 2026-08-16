"""
Matrice de permissions par rôle — fondation RBAC réutilisée par TOUS les
modules métier (stock, ventes, achats, facturation...).

Choix d'architecture : une matrice statique en code sert de VALEUR PAR
DÉFAUT versionnée (revue de PR obligatoire pour changer une permission).
La classe `RoleModuleAccess` (voir models.py) permet ensuite à chaque
coopérative de surcharger ces valeurs par rôle/module depuis le panneau
d'administration ; tant qu'une coopérative n'a pas défini de surcharge,
la matrice s'applique sans coût supplémentaire.
"""

from __future__ import annotations

from apps.authentication.models import UserRole

# Modules métier exposés dans le panneau d'administration des permissions.
MODULES = [
    "users",
    "cooperative",
    "members",
    "partners",
    "catalog",
    "warehouses",
    "stock",
    "purchases",
    "sales",
    "billing",
    "reports",
    "audit",
    "accounting",
    "documents",
    "settings",
    "assemblies",
    "contributions",
]

# Rôles éditables depuis le panneau admin. L'OWNER est exclu : il a toujours "*".
EDITABLE_ROLES = [UserRole.ADMIN, UserRole.STAFF, UserRole.ACCOUNTANT]

# Format des codes : "<module>.<action>". Chaque futur module (Epic 6+)
# enregistrera ses propres codes ici au fur et à mesure de sa construction.
PERMISSIONS_MATRIX: dict[str, set[str]] = {
    UserRole.OWNER: {"*"},  # OWNER a tous les droits, toujours.
    UserRole.ADMIN: {
        "users.view",
        "users.invite",
        "users.edit_role",
        "users.deactivate",
        "cooperative.view",
        "cooperative.edit",
        "members.view",
        "members.edit",
        "partners.view",
        "partners.edit",
        "catalog.view",
        "catalog.edit",
        "warehouses.view",
        "warehouses.edit",
        "stock.view",
        "stock.edit",
        "purchases.view",
        "purchases.edit",
        "purchases.receive",
        "sales.view",
        "sales.edit",
        "billing.view",
        "billing.edit",
        "reports.view",
        "audit.view",
        "accounting.view",
        "accounting.edit",
        "accounting.post",
        "documents.view",
        "documents.edit",
        "assemblies.view",
        "assemblies.edit",
        "contributions.view",
        "contributions.edit",
        "settings.view",
        "settings.edit",
    },
    UserRole.ACCOUNTANT: {
        "users.view",
        "cooperative.view",
        "members.view",
        "partners.view",
        "partners.edit",
        "catalog.view",
        "warehouses.view",
        "stock.view",
        "purchases.view",
        "sales.view",
        "billing.view",
        "billing.edit",
        "reports.view",
        "accounting.view",
        "accounting.edit",
        "accounting.post",
        "documents.view",
        "assemblies.view",
        "contributions.view",
        "settings.view",
    },
    UserRole.STAFF: {
        "users.view",
        "cooperative.view",
        "members.view",
        "members.edit",
        "partners.view",
        "partners.edit",
        "catalog.view",
        "warehouses.view",
        "stock.view",
        "stock.edit",
        "purchases.view",
        "purchases.receive",
        "sales.view",
        "sales.edit",
        "documents.view",
        "assemblies.view",
        "assemblies.edit",
        "contributions.view",
        "contributions.edit",
        "settings.view",
    },
}


def default_modules_for_role(role: str) -> set[str]:
    """Modules par défaut d'un rôle, dérivés des codes de la matrice statique."""
    return {code.split(".", 1)[0] for code in PERMISSIONS_MATRIX.get(role, set())} - {"*"}


def has_permission(role: str, code: str) -> bool:
    """Vérifie si un rôle donné possède le code de permission demandé (matrice statique)."""
    allowed = PERMISSIONS_MATRIX.get(role, set())
    return "*" in allowed or code in allowed
