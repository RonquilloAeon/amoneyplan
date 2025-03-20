import pytest
from django.apps import apps
from django.conf import settings
from django.test import Client

from amoneyplan.money_plans.application import MoneyPlanner


@pytest.fixture
def client():
    """A Django test client instance."""
    return Client()


@pytest.fixture
def money_planner(transactional_db):
    """Create a fresh MoneyPlanner instance for each test."""
    planner = MoneyPlanner(env=settings.EVENT_SOURCING_SETTINGS)
    apps.get_app_config("money_plans").money_planner = planner
    return planner
