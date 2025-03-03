from django.apps import AppConfig
from eventsourcing.domain import DomainEventProtocol
from eventsourcing.persistence import Transcoder
from eventsourcing.system import SingleThreadedRunner


class RunnerConfig(AppConfig):
    name = 'amoneyplan.eventsourcing_runner'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        pass  # Normally you'd set up your runner and system here if needed