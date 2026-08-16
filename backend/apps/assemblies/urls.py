from __future__ import annotations

from django.urls import path

from apps.assemblies.views import (
    AssemblyAttendanceListCreateView,
    AssemblyDetailView,
    AssemblyListCreateView,
)

app_name = "assemblies"

urlpatterns = [
    path("", AssemblyListCreateView.as_view(), name="list-create"),
    path("<uuid:pk>/", AssemblyDetailView.as_view(), name="detail"),
    path(
        "<uuid:assembly_id>/attendance/",
        AssemblyAttendanceListCreateView.as_view(),
        name="attendance",
    ),
]
