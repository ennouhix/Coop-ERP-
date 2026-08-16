from __future__ import annotations

from django.urls import path

from apps.members.views import (
    MemberDeactivateView,
    MemberDetailView,
    MemberListCreateView,
    MemberReactivateView,
    ShareTransactionDetailView,
    ShareTransactionListCreateView,
)

app_name = "members"

urlpatterns = [
    path("", MemberListCreateView.as_view(), name="list-create"),
    path("<uuid:pk>/", MemberDetailView.as_view(), name="detail"),
    path("<uuid:member_id>/deactivate/", MemberDeactivateView.as_view(), name="deactivate"),
    path("<uuid:member_id>/reactivate/", MemberReactivateView.as_view(), name="reactivate"),
    path("shares/", ShareTransactionListCreateView.as_view(), name="shares-list-create"),
    path("shares/<uuid:pk>/", ShareTransactionDetailView.as_view(), name="shares-detail"),
]
