"""
WSGI config for monitoring project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application


# Activate virtualenv
activate_path = os.path.expanduser("/usr/share/DJANGO_MONITORING_APP/venv/bin/activate_this.py")
with open(activate_path) as act:
    exec(act.read(), dict(__file__=activate_path))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "monitoring.settings")

application = get_wsgi_application()
