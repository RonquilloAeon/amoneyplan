from django.apps import AppConfig


class MoneyPlansConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "amoneyplan.api"
    verbose_name = "Money Plan API"

    def ready(self) -> None: ...
