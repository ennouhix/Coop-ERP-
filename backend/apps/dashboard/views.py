"""
Vue du module dashboard.

Endpoint :
- GET /api/v1/dashboard/summary/?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
  Sans paramètres : période par défaut = mois courant.
"""
from __future__ import annotations

from datetime import date

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsCooperativeMember
from apps.dashboard.serializers import DashboardSummarySerializer
from apps.dashboard.services import get_dashboard_summary
from apps.roles_permissions.permissions import RequirePermission


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("reports.view")]

    def get(self, request: Request) -> Response:
        date_from = self._parse_date(request.query_params.get("date_from"))
        date_to = self._parse_date(request.query_params.get("date_to"))

        summary = get_dashboard_summary(cooperative=request.user.cooperative, date_from=date_from, date_to=date_to)
        return Response(DashboardSummarySerializer(summary).data)

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        if not value:
            return None
        return date.fromisoformat(value)
