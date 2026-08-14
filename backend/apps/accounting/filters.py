"""Filtres pour le module Comptabilité."""
from __future__ import annotations

import django_filters

from apps.accounting.models import AccountingEntry


class AccountingEntryFilter(django_filters.FilterSet):
    journal = django_filters.UUIDFilter(field_name="journal")
    is_posted = django_filters.BooleanFilter()
    period = django_filters.CharFilter()
    date_from = django_filters.DateFilter(field_name="entry_date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="entry_date", lookup_expr="lte")

    class Meta:
        model = AccountingEntry
        fields = ["journal", "is_posted", "period", "date_from", "date_to"]
