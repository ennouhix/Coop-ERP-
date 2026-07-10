from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.authentication.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = ["email", "username", "role", "cooperative", "is_active", "is_staff"]
    list_filter = ["role", "is_active", "cooperative"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering = ["email"]

    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Coopérative & Rôle", {"fields": ("cooperative", "role", "phone_number")}),
    )
