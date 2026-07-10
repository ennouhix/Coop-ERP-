"""Configuration spécifique à l'environnement de développement local."""
from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += ["django_extensions"] if False else []  # placeholder, activer si besoin

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
