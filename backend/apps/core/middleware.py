"""
Filet de sécurité : garantit que le contexte tenant est remis à zéro au
début et à la fin de chaque requête, quel que soit le worker/thread qui la
traite. La RÉSOLUTION effective du tenant se fait désormais dans
apps.core.authentication.TenantAwareJWTAuthentication, exécutée par DRF
au moment de l'authentification (voir ce fichier pour le détail du bug
que ce changement corrige).
"""
from __future__ import annotations

from typing import Callable

from django.http import HttpRequest, HttpResponse

from apps.core.context import set_current_tenant


class TenantMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        set_current_tenant(None)
        try:
            response = self.get_response(request)
        finally:
            set_current_tenant(None)
        return response
