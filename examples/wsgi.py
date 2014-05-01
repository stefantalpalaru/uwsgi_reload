"""
WSGI config for some_proj project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "some_proj.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Django is lazy so make sure most of the modules are loaded by making a request

application({
    'REQUEST_METHOD': 'GET',
    'SERVER_NAME': '127.0.0.1',
    'SERVER_PORT': 80,
    'PATH': '/',
    'wsgi.input': sys.stdin,
}, lambda x, y: None)

