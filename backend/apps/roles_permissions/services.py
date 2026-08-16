"""
Logique métier des permissions de rôle : calcul des accès effectifs et
persistance des personnalisations par coopérative.

Règle de résolution : l'OWNER a toujours accès à tout ; sinon, si des
surcharges existent en base pour (cooperative, role), elles définissent
l'accès complet de ce rôle ; sinon la matrice statique s'applique.
"""

from __future__ import annotations

from typing import Any

from apps.authentication.models import UserRole
from apps.roles_permissions.matrix import (
    EDITABLE_ROLES,
    MODULES,
    default_modules_for_role,
    has_permission,
)
from apps.roles_permissions.models import RoleModuleAccess


class RolePermissionsError(Exception):
    """Payload invalide ou incohérent envoyé par le panneau d'administration."""


def has_permission_for_cooperative(*, cooperative_id, role: str, code: str) -> bool:  # noqa: ANN001
    """
    Vérifie une permission en tenant compte des surcharges de la coopérative.

    En l'absence de surcharge, la matrice statique s'applique avec vérification
    précise du code complet ("<module>.<action>"). Une surcharge accorde quant
    à elle tout le module, sans distinction d'action (l'interface
    d'administration ne gère que des modules).
    """
    if role == UserRole.OWNER:
        return True
    module = code.split(".", 1)[0]
    overrides = set(
        RoleModuleAccess.all_objects.filter(
            cooperative_id=cooperative_id,
            role=role,
            is_active=True,
        ).values_list("module", flat=True)
    )
    if overrides:
        return module in overrides
    return has_permission(role=role, code=code)


def effective_modules_for_role(*, cooperative_id, role: str) -> set[str]:  # noqa: ANN001
    """Modules accessibles à un rôle au sein d'une coopérative (surcharges ou matrice)."""
    overrides = set(
        RoleModuleAccess.all_objects.filter(
            cooperative_id=cooperative_id,
            role=role,
            is_active=True,
        ).values_list("module", flat=True)
    )
    if overrides:
        return overrides
    return default_modules_for_role(role)


def effective_modules_per_role(*, cooperative_id) -> dict[str, list[str]]:  # noqa: ANN001
    """Accès effectif de chaque rôle éditable, pour le panneau d'administration."""
    return {
        role: sorted(effective_modules_for_role(cooperative_id=cooperative_id, role=role))
        for role in EDITABLE_ROLES
    }


def update_role_modules(*, cooperative_id, payload: Any) -> dict[str, list[str]]:  # noqa: ANN001
    """
    Remplace les accès d'un ou plusieurs rôles.

    `payload` attendu : {"<role>": ["<module>", ...], ...}. Chaque rôle fourni
    voit ses surcharges remplacées intégralement par la liste envoyée. Si la
    liste correspond à la matrice statique, aucune surcharge n'est conservée
    (retour à la valeur par défaut).
    """
    if not isinstance(payload, dict):
        raise RolePermissionsError("Payload invalide.")

    valid_roles = set(EDITABLE_ROLES)
    valid_modules = set(MODULES)

    for role, modules in payload.items():
        if role not in valid_roles:
            raise RolePermissionsError(f"Rôle inconnu : {role}")
        if not isinstance(modules, list) or any(
            not isinstance(m, str) or m not in valid_modules for m in modules
        ):
            raise RolePermissionsError(f"Modules invalides pour le rôle {role}.")

    for role, modules in payload.items():
        RoleModuleAccess.all_objects.filter(cooperative_id=cooperative_id, role=role).delete()
        desired = set(modules)
        if desired == default_modules_for_role(role):
            continue
        RoleModuleAccess.all_objects.bulk_create(
            [
                RoleModuleAccess(cooperative_id=cooperative_id, role=role, module=module)
                for module in desired
            ]
        )

    return effective_modules_per_role(cooperative_id=cooperative_id)
