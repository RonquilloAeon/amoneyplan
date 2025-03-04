"""Tests for the GraphQL API schema."""

from typing import Any, Dict

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


@pytest.mark.django_db(transaction=True)
class TestGraphQLAPI:
    """Tests for GraphQL API."""

    def execute_query(self, client: Client, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a GraphQL query and return the response."""
        data = {
            "query": query,
            "variables": variables,
        }
        response = client.post("/graphql/", data=data, content_type="application/json")
        return response.json()["data"]  # Extract the data field from the response

    def test_money_plan_query(self, client, money_planner):
        """Test querying a money plan."""
        query = """
        query GetMoneyPlan($planId: GlobalID!) {
            moneyPlan(planId: $planId) {
                id
                initialBalance
                remainingBalance
                accounts {
                    id
                    name
                    buckets {
                        bucketName
                        category
                        allocatedAmount
                    }
                }
                isCommitted
            }
        }
        """
        # First create a plan
        create_plan_mutation = """
        mutation StartPlan($input: PlanStartInput!) {
            moneyPlan {
                startPlan(input: $input) {
                    success
                    moneyPlan {
                        id
                    }
                }
            }
        }
        """
        variables = {"input": {"initialBalance": 1000.0, "notes": "Test plan"}}

        result = self.execute_query(client, create_plan_mutation, variables)
        assert "errors" not in result
        plan_id = result["moneyPlan"]["startPlan"]["moneyPlan"]["id"]

        # Add an account with a bucket to satisfy invariants
        add_account_mutation = """
        mutation AddAccount($input: AddAccountInput!) {
            moneyPlan {
                addAccount(input: $input) {
                    success
                    moneyPlan {
                        id
                    }
                }
            }
        }
        """
        account_variables = {
            "input": {
                "planId": plan_id,
                "name": "Test Account",
                "buckets": [{"bucketName": "Default", "category": "default", "allocatedAmount": 1000.0}],
            }
        }

        result = self.execute_query(client, add_account_mutation, account_variables)
        assert result["moneyPlan"]["addAccount"]["success"]

        # Now query the created plan
        result = self.execute_query(client, query, {"planId": plan_id})
        assert "errors" not in result
        assert result["moneyPlan"]["initialBalance"] == 1000.0
        assert result["moneyPlan"]["isCommitted"] is False
        assert len(result["moneyPlan"]["accounts"]) == 1
        assert result["moneyPlan"]["accounts"][0]["name"] == "Test Account"

    def test_create_and_commit_plan(self, client, money_planner):
        """Test creating a plan, adding accounts/buckets, and committing it."""
        # Create a new plan
        create_plan_mutation = """
        mutation StartPlan($input: PlanStartInput!) {
            moneyPlan {
                startPlan(input: $input) {
                    success
                    moneyPlan {
                        id
                        initialBalance
                    }
                }
            }
        }
        """
        variables = {"input": {"initialBalance": 1000.0, "notes": "Test plan with accounts"}}

        result = self.execute_query(client, create_plan_mutation, variables)
        assert "errors" not in result
        plan_id = result["moneyPlan"]["startPlan"]["moneyPlan"]["id"]

        # Add an account with buckets that sum to initial balance
        add_account_mutation = """
        mutation AddAccount($input: AddAccountInput!) {
            moneyPlan {
                addAccount(input: $input) {
                    success
                    moneyPlan {
                        id
                        accounts {
                            id
                            name
                            buckets {
                                bucketName
                                allocatedAmount
                            }
                        }
                    }
                }
            }
        }
        """
        account_variables = {
            "input": {
                "planId": plan_id,
                "name": "Test Account",
                "buckets": [
                    {"bucketName": "Savings", "category": "savings", "allocatedAmount": 600.0},
                    {"bucketName": "Bills", "category": "expenses", "allocatedAmount": 400.0},
                ],
            }
        }

        result = self.execute_query(client, add_account_mutation, account_variables)
        assert "errors" not in result
        assert result["moneyPlan"]["addAccount"]["success"]

        # Verify account and buckets were created
        accounts = result["moneyPlan"]["addAccount"]["moneyPlan"]["accounts"]
        assert len(accounts) == 1
        buckets = accounts[0]["buckets"]
        assert len(buckets) == 2
        assert buckets[0]["bucketName"] == "Savings"
        assert buckets[0]["allocatedAmount"] == 600.0
        assert buckets[1]["bucketName"] == "Bills"
        assert buckets[1]["allocatedAmount"] == 400.0

        # Commit the plan - should succeed since allocations equal initial balance
        commit_mutation = """
        mutation CommitPlan($input: CommitPlanInput!) {
            moneyPlan {
                commitPlan(input: $input) {
                    success
                    moneyPlan {
                        id
                        isCommitted
                        initialBalance
                        remainingBalance
                    }
                }
            }
        }
        """
        commit_variables = {"input": {"planId": plan_id}}

        result = self.execute_query(client, commit_mutation, commit_variables)
        assert "errors" not in result
        assert result["moneyPlan"]["commitPlan"]["success"]
        assert result["moneyPlan"]["commitPlan"]["moneyPlan"]["isCommitted"]
        assert result["moneyPlan"]["commitPlan"]["moneyPlan"]["remainingBalance"] == 0.0

    def test_allocation_invariants(self, client, money_planner):
        """Test that plan allocations must equal initial balance for commit."""
        # Create a plan
        create_plan_mutation = """
        mutation StartPlan($input: PlanStartInput!) {
            moneyPlan {
                startPlan(input: $input) {
                    success
                    moneyPlan {
                        id
                    }
                }
            }
        }
        """
        variables = {"input": {"initialBalance": 1000.0, "notes": "Test plan invariants"}}

        result = self.execute_query(client, create_plan_mutation, variables)
        plan_id = result["moneyPlan"]["startPlan"]["moneyPlan"]["id"]

        # Add an account with buckets that don't sum to initial balance
        add_account_mutation = """
        mutation AddAccount($input: AddAccountInput!) {
            moneyPlan {
                addAccount(input: $input) {
                    success
                    error {
                        message
                    }
                }
            }
        }
        """
        account_variables = {
            "input": {
                "planId": plan_id,
                "name": "Test Account",
                "buckets": [
                    {
                        "bucketName": "Savings",
                        "category": "savings",
                        "allocatedAmount": 500.0,  # Only allocating half
                    }
                ],
            }
        }

        result = self.execute_query(client, add_account_mutation, account_variables)
        assert "errors" not in result

        # Try to commit - should fail
        commit_mutation = """
        mutation CommitPlan($input: CommitPlanInput!) {
            moneyPlan {
                commitPlan(input: $input) {
                    success
                    error {
                        message
                    }
                }
            }
        }
        """
        commit_variables = {"input": {"planId": plan_id}}

        result = self.execute_query(client, commit_mutation, commit_variables)
        assert "errors" not in result
        assert not result["moneyPlan"]["commitPlan"]["success"]
        assert "equal initial balance" in result["moneyPlan"]["commitPlan"]["error"]["message"].lower()

    def test_plan_isolation(self, client, money_planner):
        """Test that plans are properly isolated in the database."""
        # Create first plan
        create_plan_mutation = """
        mutation StartPlan($input: PlanStartInput!) {
            moneyPlan {
                startPlan(input: $input) {
                    error {
                        message
                    }
                    success
                    moneyPlan {
                        id
                        initialBalance
                    }
                }
            }
        }
        """
        variables1 = {"input": {"initialBalance": 1000.0, "notes": "Plan 1"}}

        result1 = self.execute_query(client, create_plan_mutation, variables1)
        plan1_id = result1["moneyPlan"]["startPlan"]["moneyPlan"]["id"]

        # Add an account with a bucket that allocates the full balance
        add_account_mutation = """
        mutation AddAccount($input: AddAccountInput!) {
            moneyPlan {
                addAccount(input: $input) {
                    success
                    moneyPlan {
                        id
                    }
                }
            }
        }
        """
        account_variables = {
            "input": {
                "planId": plan1_id,
                "name": "Test Account",
                "buckets": [{"bucketName": "Default", "category": "default", "allocatedAmount": 1000.0}],
            }
        }

        result = self.execute_query(client, add_account_mutation, account_variables)
        assert result["moneyPlan"]["addAccount"]["success"]

        # Commit the first plan before creating the second one
        commit_mutation = """
        mutation CommitPlan($input: CommitPlanInput!) {
            moneyPlan {
                commitPlan(input: $input) {
                    success
                    error {
                        message
                    }
                }
            }
        }
        """
        commit_variables = {"input": {"planId": plan1_id}}
        commit_result = self.execute_query(client, commit_mutation, commit_variables)
        assert commit_result["moneyPlan"]["commitPlan"]["success"], "Failed to commit first plan"

        # Create second plan
        variables2 = {"input": {"initialBalance": 2000.0, "notes": "Plan 2"}}

        result2 = self.execute_query(client, create_plan_mutation, variables2)
        plan2_id = result2["moneyPlan"]["startPlan"]["moneyPlan"]["id"]

        # Add account to second plan as well
        account_variables2 = {
            "input": {
                "planId": plan2_id,
                "name": "Test Account 2",
                "buckets": [{"bucketName": "Default", "category": "default", "allocatedAmount": 2000.0}],
            }
        }
        result = self.execute_query(client, add_account_mutation, account_variables2)
        assert result["moneyPlan"]["addAccount"]["success"]

        # Query both plans to verify they're separate
        query = """
        query GetMoneyPlan($planId: GlobalID!) {
            moneyPlan(planId: $planId) {
                id
                initialBalance
                notes
                accounts {
                    id
                    name
                    buckets {
                        bucketName
                        allocatedAmount
                    }
                }
            }
        }
        """

        result1 = self.execute_query(client, query, {"planId": plan1_id})
        result2 = self.execute_query(client, query, {"planId": plan2_id})

        assert result1["moneyPlan"]["initialBalance"] == 1000.0
        assert result1["moneyPlan"]["notes"] == "Plan 1"
        assert len(result1["moneyPlan"]["accounts"]) == 1
        assert result1["moneyPlan"]["accounts"][0]["name"] == "Test Account"
        assert result1["moneyPlan"]["accounts"][0]["buckets"][0]["allocatedAmount"] == 1000.0

        assert result2["moneyPlan"]["initialBalance"] == 2000.0
        assert result2["moneyPlan"]["notes"] == "Plan 2"
        assert len(result2["moneyPlan"]["accounts"]) == 1
        assert result2["moneyPlan"]["accounts"][0]["name"] == "Test Account 2"
        assert result2["moneyPlan"]["accounts"][0]["buckets"][0]["allocatedAmount"] == 2000.0
