from __future__ import annotations

from django.contrib import admin

from apps.contributions.models import Contribution


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "product",
        "quantity",
        "unit_price",
        "contribution_date",
        "status",
        "cooperative",
    ]
    list_filter = ["status", "campaign", "cooperative"]
    search_fields = ["member__first_name", "member__last_name", "campaign"]
    readonly_fields = ["created_at", "updated_at"]
