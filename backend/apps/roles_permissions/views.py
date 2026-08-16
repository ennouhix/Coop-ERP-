"""
Vues du module roles_permissions.

Endpoints :
- GET  /api/v1/roles/permissions/  -> accès effectifs par rôle (panneau admin)
- PUT  /api/v1/roles/permissions/  -> personnaliser les accès d'un/plusieurs rôles
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsCooperativeMember, IsOwnerOrAdmin
from apps.roles_permissions import services
from apps.roles_permissions.matrix import MODULES


class RolePermissionsView(APIView):
    """Lecture et mise à jour des accès module par rôle de la coopérative."""

    permission_classes = [IsAuthenticated, IsCooperativeMember, IsOwnerOrAdmin]

    def _payload(self, roles: dict[str, list[str]]) -> dict[str, object]:
        return {"modules": MODULES, "roles": roles}

    def get(self, request: Request) -> Response:
        roles = services.effective_modules_per_role(cooperative_id=request.user.cooperative_id)
        return Response(self._payload(roles))

    def put(self, request: Request) -> Response:
        try:
            roles = services.update_role_modules(
                cooperative_id=request.user.cooperative_id, payload=request.data
            )
        except services.RolePermissionsError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self._payload(roles))
