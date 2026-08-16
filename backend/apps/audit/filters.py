"""Filtres pour consulter le journal d'activité."""

from __future__ import annotations

import django_filters

from apps.audit.models import AuditLog


class AuditLogFilter(django_filters.FilterSet):
    action = django_filters.CharFilter(field_name="action", lookup_expr="istartswith")
    actor = django_filters.UUIDFilter(field_name="actor_id")
    target_type = django_filters.CharFilter(field_name="target_type", lookup_expr="iexact")
    target_id = django_filters.CharFilter(field_name="target_id")
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = AuditLog
        fields = ["action", "actor", "target_type", "target_id", "created_after", "created_before"]
