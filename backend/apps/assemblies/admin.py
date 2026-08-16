from __future__ import annotations

from django.contrib import admin

from apps.assemblies.models import Assembly, AssemblyAttendance


class AssemblyAttendanceInline(admin.TabularInline):
    model = AssemblyAttendance
    extra = 0


@admin.register(Assembly)
class AssemblyAdmin(admin.ModelAdmin):
    list_display = ["title", "assembly_type", "scheduled_date", "status", "cooperative"]
    list_filter = ["status", "assembly_type", "cooperative"]
    search_fields = ["title"]
    inlines = [AssemblyAttendanceInline]
    readonly_fields = ["created_at", "updated_at"]
