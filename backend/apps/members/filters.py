"""Filtres pour la liste des membres."""

from __future__ import annotations

import django_filters

from apps.members.models import (
    Member,
    MemberStatus,
    MemberType,
    ShareTransaction,
    ShareTransactionType,
)


class MemberFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=MemberStatus.choices)
    member_type = django_filters.ChoiceFilter(choices=MemberType.choices)
    join_date_after = django_filters.DateFilter(field_name="join_date", lookup_expr="gte")
    join_date_before = django_filters.DateFilter(field_name="join_date", lookup_expr="lte")

    class Meta:
        model = Member
        fields = ["status", "member_type", "join_date_after", "join_date_before"]


class ShareTransactionFilter(django_filters.FilterSet):
    member_id = django_filters.UUIDFilter(field_name="member_id")
    transaction_type = django_filters.ChoiceFilter(choices=ShareTransactionType.choices)
    date_after = django_filters.DateFilter(field_name="transaction_date", lookup_expr="gte")
    date_before = django_filters.DateFilter(field_name="transaction_date", lookup_expr="lte")

    class Meta:
        model = ShareTransaction
        fields = ["member_id", "transaction_type", "date_after", "date_before"]
