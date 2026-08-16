"""
Vue du module audit.

Endpoint :
- GET /api/v1/audit/logs/  -> historique complet, filtrable
  (par action, acteur, type de cible, période)

Aucune route de modification/suppression : l'immuabilité du journal est
garantie par l'absence même de la route, comme pour StockMovement (Epic 8).
"""

from __future__ import annotations

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.audit.filters import AuditLogFilter
from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.authentication.permissions import IsCooperativeMember
from apps.roles_permissions.permissions import RequirePermission


class AuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("audit.view")]
    filter_backends = [DjangoFilterBackend]
    filterset_class = AuditLogFilter

    def get_queryset(self):  # noqa: ANN201
        return AuditLog.objects.select_related("actor").all()
