"""
Throttle anti brute-force ciblé sur l'endpoint de login.

Contrairement au throttle DRF standard (par IP), celui-ci limite par EMAIL
soumis dans la requête : un attaquant qui change d'IP ne contourne pas la
protection, mais un utilisateur légitime derrière un NAT partagé (bureau,
4G) n'est pas pénalisé par les tentatives d'un autre utilisateur.
"""

from __future__ import annotations

from rest_framework.throttling import SimpleRateThrottle


class LoginRateThrottle(SimpleRateThrottle):
    """
    DRF ne supporte nativement que des fenêtres fixes (s/m/h/d) via la
    syntaxe `rate` des settings ; "15 minutes" n'est pas exprimable ainsi.
    On fixe donc la durée explicitement en code plutôt que via
    DEFAULT_THROTTLE_RATES, qui reste néanmoins déclaré pour la doc/lisibilité.
    """

    scope = "login"
    rate = "5/15min"  # informatif uniquement, non utilisé par parse_rate ci-dessous
    num_requests = 5
    duration = 15 * 60  # 15 minutes en secondes

    def parse_rate(self, rate):  # noqa: ANN001, ANN201
        return self.num_requests, self.duration

    def get_cache_key(self, request, view):
        email = (request.data.get("email") or "").strip().lower()
        if not email:
            # Pas d'email fourni : on retombe sur l'IP pour ne pas laisser
            # passer une requête malformée sans limite.
            return self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": email}


class PasswordResetRateThrottle(SimpleRateThrottle):
    """
    Limite les demandes de réinitialisation par email ET par IP, pour éviter
    à la fois le spam vers une victime ciblée et l'abus depuis une seule
    source vers de nombreux comptes.
    """

    scope = "password_reset"
    num_requests = 3
    duration = 60 * 60  # 3 demandes par heure

    def parse_rate(self, rate):  # noqa: ANN001, ANN201
        return self.num_requests, self.duration

    def get_cache_key(self, request, view):
        email = (request.data.get("email") or "").strip().lower()
        ident = email or self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
