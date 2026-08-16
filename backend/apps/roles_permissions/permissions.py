"""
Permission DRF générique, pilotée par un code de permission (matrice de rôles,
surchargée éventuellement par la coopérative via le panneau d'administration).

Usage :

    class ProductViewSet(viewsets.ModelViewSet):
        permission_classes = [IsAuthenticated, RequirePermission("catalog.edit")]

`RequirePermission` est une factory (et non une classe directement
instanciable par DRF), car DRF instancie les permission_classes sans
argument — le pattern factory permet de paramétrer le code malgré cette
contrainte.
"""

from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.roles_permissions.services import has_permission_for_cooperative


def RequirePermission(code: str):  # noqa: N802 (nommage factory intentionnellement PascalCase)
    class _RequirePermission(BasePermission):
        message = f"Permission manquante : {code}"

        def has_permission(self, request: Request, view: APIView) -> bool:
            user = request.user
            return bool(
                user
                and user.is_authenticated
                and user.cooperative_id
                and has_permission_for_cooperative(
                    cooperative_id=user.cooperative_id, role=user.role, code=code
                )
            )

    return _RequirePermission
