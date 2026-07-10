from __future__ import annotations

from django.contrib import admin

from apps.users.models import Invitation


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ["email", "cooperative", "role", "status", "expires_at", "created_at"]
    list_filter = ["status", "role"]
    search_fields = ["email"]
    readonly_fields = ["token", "created_at", "updated_at"]
