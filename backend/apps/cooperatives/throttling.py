"""
Throttle dédié à l'inscription — endpoint public, donc particulièrement
exposé à l'abus (création massive de fausses coopératives, spam).
"""

from __future__ import annotations

from rest_framework.throttling import SimpleRateThrottle


class RegistrationRateThrottle(SimpleRateThrottle):
    """Limite les inscriptions par IP : 5 par heure suffisent à un usage légitime."""

    scope = "registration"
    num_requests = 5
    duration = 60 * 60

    def parse_rate(self, rate):  # noqa: ANN001, ANN201
        return self.num_requests, self.duration

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}
