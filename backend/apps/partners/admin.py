from __future__ import annotations

from django.contrib import admin

from apps.partners.models import Partner


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "cooperative", "is_customer", "is_supplier", "status"]
    list_filter = ["status", "is_customer", "is_supplier", "cooperative"]
    search_fields = ["code", "name", "phone_number", "ice"]
    readonly_fields = ["code", "created_at", "updated_at"]
