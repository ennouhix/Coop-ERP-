"""
Configuration locale de repli : postgres est introuvable/authentifié
(sinon : `docker compose up -d` dans infra/), on travaille donc sur une
base SQLite locale pour développer et générer les données de démo.

Usage :
    DJANGO_SETTINGS_MODULE=config.settings._local_sqlite python3 manage.py migrate
    DJANGO_SETTINGS_MODULE=config.settings._local_sqlite python3 manage.py seed_demo_data --reset
"""

from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/tmp/coop_erp.sqlite3",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
