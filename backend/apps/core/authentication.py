"""
Authentification JWT qui résout le tenant courant AU MOMENT où DRF
authentifie l'utilisateur.

Pourquoi ce fichier existe (bug critique corrigé à l'Epic 4) :

TenantMiddleware (middleware Django classique) s'exécute AVANT que DRF
n'ait authentifié quoi que ce soit. Django ne peuple `request.user` via
son AuthenticationMiddleware que pour l'auth par session/cookie — notre
API étant en JWT stateless, `request.user` reste `AnonymousUser` à ce
stade, et TenantMiddleware ne pouvait donc JAMAIS lire le bon tenant.
Résultat concret : TenantManager ne filtrait jamais rien, et un
utilisateur d'une coopérative pouvait voir les données de toutes les
autres. C'est le bug le plus grave possible dans un SaaS multi-tenant.

Correctif : on résout le tenant directement dans la classe
d'authentification DRF, exécutée par APIView.dispatch() juste avant que
la vue ne s'exécute — donc avant toute évaluation de queryset.
TenantMiddleware reste en place uniquement comme filet de sécurité pour
réinitialiser le contexte à None entre deux requêtes traitées par le même
thread/worker (defense in depth).
"""
from __future__ import annotations

from typing import Any, Optional

from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.core.context import set_current_tenant


class TenantAwareJWTAuthentication(JWTAuthentication):
    def authenticate(self, request: Any) -> Optional[tuple]:
        result = super().authenticate(request)
        if result is not None:
            user, _token = result
            set_current_tenant(getattr(user, "cooperative_id", None))
        return result
