from __future__ import annotations

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.authentication.views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
)
from apps.cooperatives.views import ActivateAccountView, PortalRegisterView

app_name = "authentication"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    # Portail public : inscription + validation d'email. Les vues vivent dans
    # apps.cooperatives (elles créent le tenant) mais sont exposées sous le
    # namespace auth car elles font partie du parcours d'entrée dans l'ERP.
    path("register/", PortalRegisterView.as_view(), name="register"),
    path("register/verify/", ActivateAccountView.as_view(), name="register-verify"),
    path("password/change/", ChangePasswordView.as_view(), name="change-password"),
    path("password/reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path(
        "password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
]
