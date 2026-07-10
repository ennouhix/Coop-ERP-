from __future__ import annotations

from django.contrib import admin

from apps.cooperatives.models import Cooperative


@admin.register(Cooperative)
class CooperativeAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "subscription_plan", "subscription_status", "trial_ends_at", "is_active"]
    list_filter = ["subscription_plan", "subscription_status", "is_active"]
    search_fields = ["name", "slug", "ice", "rc_number"]
    readonly_fields = ["slug", "created_at", "updated_at"]
