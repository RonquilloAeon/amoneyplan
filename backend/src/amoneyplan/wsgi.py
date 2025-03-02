"""
WSGI config for amoneyplan project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'amoneyplan.settings')

application = get_wsgi_application()