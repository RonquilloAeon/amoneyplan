"""
Money Plans app configuration.
"""

from django.apps import AppConfig


class MoneyPlansConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "amoneyplan.money_plans"
    verbose_name = "Money Plans"

    def ready(self) -> None:
        # Import here to avoid circular imports
        from .use_cases import MoneyPlanUseCases

        self.money_planner = MoneyPlanUseCases()
