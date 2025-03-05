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
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "strawberry.django",
            "eventsourcing_django",
            "amoneyplan.money_plans",
            "amoneyplan.eventsourcing_runner",
            "amoneyplan.api",
        ],
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ],
        ROOT_URLCONF="amoneyplan.urls",
        SECRET_KEY="test-key-not-for-production",
        EVENT_SOURCING_SETTINGS={
            "PERSISTENCE_MODULE": "eventsourcing.sqlite",
            "SNAPSHOT_PERIOD": 0,  # Disable snapshots for testing
        },
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "APP_DIRS": True,
                "OPTIONS": {
                    "context_processors": [
                        "django.contrib.auth.context_processors.auth",
                        "django.contrib.messages.context_processors.messages",
                    ],
                },
            },
        ],
    )
    django.setup()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests."""
    pass  # This fixture does nothing but depends on the db fixture
