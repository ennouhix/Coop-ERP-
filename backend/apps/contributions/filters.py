"""Filtres pour la liste des apports."""

from __future__ import annotations

import django_filters

from apps.contributions.models import Contribution, ContributionStatus


class ContributionFilter(django_filters.FilterSet):
    member_id = django_filters.UUIDFilter(field_name="member_id")
    product_id = django_filters.UUIDFilter(field_name="product_id")
    status = django_filters.ChoiceFilter(choices=ContributionStatus.choices)
    campaign = django_filters.CharFilter(lookup_expr="icontains")
    date_after = django_filters.DateFilter(field_name="contribution_date", lookup_expr="gte")
    date_before = django_filters.DateFilter(field_name="contribution_date", lookup_expr="lte")

    class Meta:
        model = Contribution
        fields = ["member_id", "product_id", "status", "campaign", "date_after", "date_before"]
