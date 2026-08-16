"""Filtres pour la liste des assemblées."""

from __future__ import annotations

import django_filters

from apps.assemblies.models import Assembly, AssemblyStatus, AssemblyType


class AssemblyFilter(django_filters.FilterSet):
    assembly_type = django_filters.ChoiceFilter(choices=AssemblyType.choices)
    status = django_filters.ChoiceFilter(choices=AssemblyStatus.choices)
    date_after = django_filters.DateFilter(field_name="scheduled_date", lookup_expr="gte")
    date_before = django_filters.DateFilter(field_name="scheduled_date", lookup_expr="lte")

    class Meta:
        model = Assembly
        fields = ["assembly_type", "status", "date_after", "date_before"]
