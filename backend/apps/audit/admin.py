from __future__ import annotations

from django.contrib import admin

from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "actor", "action", "target_type", "target_repr", "cooperative"]
    list_filter = ["action", "target_type", "cooperative"]
    search_fields = ["target_repr", "target_id"]
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request) -> bool:  # noqa: ANN001
        return False  # une entrée se crée UNIQUEMENT via apps.audit.services.log_activity

    def has_delete_permission(self, request, obj=None) -> bool:  # noqa: ANN001
        return False

    def has_change_permission(self, request, obj=None) -> bool:  # noqa: ANN001
        return False
