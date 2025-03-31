import pytest
from faker import Faker


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests."""
    pass  # This fixture does nothing but depends on the db fixture


@pytest.fixture
def fake() -> Faker:
    return Faker()
