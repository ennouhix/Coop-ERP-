"""
Permissions RBAC de base.

RBAC minimal ici (basé sur le champ `role` de User) pour débloquer les
modules qui ont besoin de vérifications immédiates. L'Epic 3 introduira un
modèle `Permission` granulaire par module/action ; ces classes resteront
valides comme garde-fous de haut niveau (ex: "il faut au moins être admin
pour accéder à cette vue") au-dessus des permissions fines.
"""

from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsCooperativeMember(BasePermission):
    """Refuse l'accès à tout utilisateur non rattaché à une coopérative."""

    message = "Vous devez appartenir à une coopérative pour accéder à cette ressource."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.cooperative_id)


class IsOwnerOrAdmin(BasePermission):
    """Réservé aux rôles OWNER et ADMIN de la coopérative."""

    message = "Action réservée aux propriétaires et administrateurs de la coopérative."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in {"owner", "admin"}
        )


class IsSameCooperativeObject(BasePermission):
    """
    Permission au niveau objet : vérifie que l'objet consulté/modifié
    appartient bien à la coopérative de l'utilisateur connecté.

    Filet de sécurité complémentaire au TenantManager (défense en
    profondeur) : même si un queryset non filtré était utilisé par erreur
    dans une vue (ex: apps.core.models.TenantBaseModel.all_objects), cette
    permission bloque l'accès à un objet d'un autre tenant.
    """

    message = "Cette ressource n'appartient pas à votre coopérative."

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:  # noqa: ANN001
        obj_cooperative_id = getattr(obj, "cooperative_id", None)
        return obj_cooperative_id == request.user.cooperative_id
