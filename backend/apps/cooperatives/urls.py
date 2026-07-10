from __future__ import annotations

from django.urls import path

from apps.cooperatives.views import (
    CooperativeLogoUploadView,
    CooperativeMeView,
    CooperativeRegisterView,
)

app_name = "cooperatives"

urlpatterns = [
    path("register/", CooperativeRegisterView.as_view(), name="register"),
    path("me/", CooperativeMeView.as_view(), name="me"),
    path("me/logo/", CooperativeLogoUploadView.as_view(), name="me-logo"),
]
