"""
ASGI config for kakeibo_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# --- 追加ここから ---
from django.core.management import call_command
try:
    call_command('migrate')
except Exception as e:
    print("Migration error:", e)
# --- 追加ここまで ---

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kakeibo_project.settings")

application = get_asgi_application()
