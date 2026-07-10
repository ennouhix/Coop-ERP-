from __future__ import annotations

from django.urls import path

from apps.partners.views import (
    PartnerDeactivateView,
    PartnerDetailView,
    PartnerListCreateView,
    PartnerReactivateView,
)

app_name = "partners"

urlpatterns = [
    path("", PartnerListCreateView.as_view(), name="list-create"),
    path("<uuid:pk>/", PartnerDetailView.as_view(), name="detail"),
    path("<uuid:partner_id>/deactivate/", PartnerDeactivateView.as_view(), name="deactivate"),
    path("<uuid:partner_id>/reactivate/", PartnerReactivateView.as_view(), name="reactivate"),
]
