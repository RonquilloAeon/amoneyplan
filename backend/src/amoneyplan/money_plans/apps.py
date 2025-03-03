"""
Domain app configuration.
"""
from django.apps import AppConfig
from django.conf import settings

from .application import MoneyPlanner


class DomainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'amoneyplan.money_plans'
    verbose_name = 'Money Plans'

    def ready(self) -> None:
        self.money_planner = MoneyPlanner(env=settings.EVENT_SOURCING_SETTINGS)
