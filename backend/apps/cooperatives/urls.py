from __future__ import annotations

from django.urls import path

from apps.cooperatives.views import (
    CooperativeEmailConfigView,
    CooperativeEmailTestView,
    CooperativeLogoUploadView,
    CooperativeMeView,
    CooperativeRegisterView,
    EmailNotificationListView,
)

app_name = "cooperatives"

urlpatterns = [
    path("register/", CooperativeRegisterView.as_view(), name="register"),
    path("me/", CooperativeMeView.as_view(), name="me"),
    path("me/logo/", CooperativeLogoUploadView.as_view(), name="me-logo"),
    path("me/email/", CooperativeEmailConfigView.as_view(), name="me-email-config"),
    path("me/email/test/", CooperativeEmailTestView.as_view(), name="me-email-test"),
    path("me/notifications/", EmailNotificationListView.as_view(), name="me-notifications"),
]
