"""Pytest configuration for the test suite."""

import os

import django
import pytest
from django.conf import settings


# Configure Django settings for testing
def pytest_configure():
    """Configure Django for testing."""
    # Set the SQLite database name for event sourcing
    os.environ["SQLITE_DBNAME"] = ":memory:"

    settings.configure(
        DEBUG=False,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "amoneyplan.money_plans",
            "amoneyplan.eventsourcing_runner",
            "amoneyplan.api",
        ],
        MIDDLEWARE=[],
        ROOT_URLCONF="amoneyplan.urls",
        SECRET_KEY="test-key-not-for-production",
        EVENT_SOURCING_SETTINGS={
            "PERSISTENCE_MODULE": "eventsourcing.sqlite",
            "SNAPSHOT_PERIOD": 0,  # Disable snapshots for testing
        },
    )
    django.setup()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests."""
    pass  # This fixture does nothing but depends on the db fixture
