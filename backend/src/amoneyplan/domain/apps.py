"""
Domain app configuration.
"""
from django.apps import AppConfig


class DomainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'amoneyplan.domain'
    verbose_name = 'Money Plan Domain'