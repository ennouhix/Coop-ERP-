"""Bases de tests SQLite locales (pas besoin de postgres pour la CI locale).

Usage :
    DJANGO_SETTINGS_MODULE=config.settings._local_test python3 manage.py test
"""

from .test import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/tmp/coop_erp_test.sqlite3",
    }
}
