from __future__ import annotations

from django.urls import path

from apps.roles_permissions.views import RolePermissionsView

app_name = "roles_permissions"

urlpatterns = [
    path("roles/permissions/", RolePermissionsView.as_view(), name="role-permissions"),
]
