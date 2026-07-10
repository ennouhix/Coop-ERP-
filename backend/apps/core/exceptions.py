"""
Gestionnaire d'exceptions centralisé pour DRF.

Uniformise le format des erreurs de l'API sur toute la plateforme :
{
    "error": {
        "code": "validation_error",
        "message": "...",
        "details": {...}
    }
}
"""
from __future__ import annotations

from typing import Any, Optional

from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc: Exception, context: dict) -> Optional[Response]:
    response = exception_handler(exc, context)

    if response is not None:
        error_code = getattr(exc, "default_code", "error")
        response.data = {
            "error": {
                "code": error_code,
                "message": _extract_message(response.data),
                "details": response.data,
            }
        }
    return response


def _extract_message(data: Any) -> str:
    if isinstance(data, dict) and "detail" in data:
        return str(data["detail"])
    if isinstance(data, list) and data:
        return str(data[0])
    return "Une erreur est survenue."
