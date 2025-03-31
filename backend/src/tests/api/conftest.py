import pytest
from django.apps import apps
from django.test import Client

from amoneyplan.money_plans.use_cases import MoneyPlanUseCases


@pytest.fixture
def client():
    """A Django test client instance."""
    return Client()


@pytest.fixture
def money_planner(transactional_db):
    """Create a fresh MoneyPlanUseCases instance for each test."""
    planner = MoneyPlanUseCases()
    if apps.is_installed("amoneyplan.money_plans"):
        try:
            apps.get_app_config("money_plans").money_planner = planner
        except AttributeError:
            # App config might not have money_planner attribute in test environment
            pass
    return planner
