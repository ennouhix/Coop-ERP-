"""Filtres pour la liste des partenaires."""

from __future__ import annotations

import django_filters

from apps.partners.models import Partner, PartnerStatus


class PartnerFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=PartnerStatus.choices)
    is_customer = django_filters.BooleanFilter()
    is_supplier = django_filters.BooleanFilter()

    class Meta:
        model = Partner
        fields = ["status", "is_customer", "is_supplier"]
