from __future__ import annotations

from django.urls import path

from apps.contributions.views import (
    ContributionDetailView,
    ContributionListCreateView,
    ContributionMarkPaidView,
)

app_name = "contributions"

urlpatterns = [
    path("", ContributionListCreateView.as_view(), name="list-create"),
    path("<uuid:pk>/", ContributionDetailView.as_view(), name="detail"),
    path("<uuid:pk>/mark-paid/", ContributionMarkPaidView.as_view(), name="mark-paid"),
]
