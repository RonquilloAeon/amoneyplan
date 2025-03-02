"""
API app configuration.
"""
from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'amoneyplan.api'
    verbose_name = 'Money Plan API'