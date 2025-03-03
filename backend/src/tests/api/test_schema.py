"""Tests for the GraphQL API schema."""

from typing import Any, Dict

import pytest
from django.apps import apps
from strawberry.django.test import GraphQLTestClient

from amoneyplan.api.schema import schema
from amoneyplan.money_plans.application import MoneyPlanner


@pytest.fixture
def graphql_client() -> GraphQLTestClient:
    """Create a GraphQL test client."""
    return GraphQLTestClient(schema)


@pytest.fixture
def money_planner(db) -> MoneyPlanner:
    """Get the money planner service."""
    return apps.get_app_config("money_plans").money_planner


class TestGraphQLAPI:
    """Base class for GraphQL API tests."""

    @pytest.fixture(autouse=True)
    def setup(self, graphql_client: GraphQLTestClient, money_planner: MoneyPlanner):
        """Set up test environment."""
        self.client = graphql_client
        self.money_planner = money_planner

    def execute_query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a GraphQL query and return the response.

        Args:
            query: The GraphQL query string
            variables: Optional variables for the query

        Returns:
            The JSON response from the query
        """
        response = self.client.query(query, variables)
        return response.data

    def test_money_plan_query(self):
        """Test querying a money plan."""
        query = """
        query GetMoneyPlan($planId: ID!) {
            moneyPlan(planId: $planId) {
                id
                initialBalance
                remainingBalance
                accounts {
                    edges {
                        node {
                            accountName
                            buckets {
                                edges {
                                    node {
                                        bucketName
                                        category
                                        allocatedAmount
                                    }
                                }
                            }
                        }
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

        result = self.execute_query(create_plan_mutation, variables)
        assert "errors" not in result
        plan_id = result["moneyPlan"]["startPlan"]["moneyPlan"]["id"]

        # Now query the created plan
        result = self.execute_query(query, {"planId": plan_id})
        assert "errors" not in result
        assert result["moneyPlan"]["initialBalance"] == 1000.0
        assert result["moneyPlan"]["isCommitted"] is False

    def test_create_and_commit_plan(self):
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

        result = self.execute_query(create_plan_mutation, variables)
        assert "errors" not in result
        plan_id = result["moneyPlan"]["startPlan"]["moneyPlan"]["id"]

        # Add an account with buckets
        add_account_mutation = """
        mutation AddAccount($input: AddAccountInput!) {
            moneyPlan {
                addAccount(input: $input) {
                    success
                    moneyPlan {
                        id
                        accounts {
                            edges {
                                node {
                                    accountName
                                    buckets {
                                        edges {
                                            node {
                                                bucketName
                                                allocatedAmount
                                            }
                                        }
                                    }
                                }
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
                "accountName": "Test Account",
                "buckets": [
                    {"bucketName": "Savings", "category": "savings", "allocatedAmount": 600.0},
                    {"bucketName": "Bills", "category": "expenses", "allocatedAmount": 400.0},
                ],
            }
        }

        result = self.execute_query(add_account_mutation, account_variables)
        assert "errors" not in result
        assert result["moneyPlan"]["addAccount"]["success"]

        # Commit the plan
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

        result = self.execute_query(commit_mutation, commit_variables)
        assert "errors" not in result
        assert result["moneyPlan"]["commitPlan"]["success"]
        assert result["moneyPlan"]["commitPlan"]["moneyPlan"]["isCommitted"]
        assert result["moneyPlan"]["commitPlan"]["moneyPlan"]["remainingBalance"] == 0.0

    def test_allocation_invariants(self):
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

        result = self.execute_query(create_plan_mutation, variables)
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
                "accountName": "Test Account",
                "buckets": [
                    {
                        "bucketName": "Savings",
                        "category": "savings",
                        "allocatedAmount": 500.0,  # Only allocating half
                    }
                ],
            }
        }

        result = self.execute_query(add_account_mutation, account_variables)
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

        result = self.execute_query(commit_mutation, commit_variables)
        assert "errors" not in result
        assert not result["moneyPlan"]["commitPlan"]["success"]
        assert "equal initial balance" in result["moneyPlan"]["commitPlan"]["error"]["message"].lower()

    def test_plan_isolation(self):
        """Test that plans are properly isolated in the database."""
        # Create first plan
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
        variables1 = {"input": {"initialBalance": 1000.0, "notes": "Plan 1"}}

        result1 = self.execute_query(create_plan_mutation, variables1)
        plan1_id = result1["moneyPlan"]["startPlan"]["moneyPlan"]["id"]

        # Create second plan
        variables2 = {"input": {"initialBalance": 2000.0, "notes": "Plan 2"}}

        result2 = self.execute_query(create_plan_mutation, variables2)
        plan2_id = result2["moneyPlan"]["startPlan"]["moneyPlan"]["id"]

        # Query both plans to verify they're separate
        query = """
        query GetMoneyPlan($planId: ID!) {
            moneyPlan(planId: $planId) {
                id
                initialBalance
                notes
            }
        }
        """

        result1 = self.execute_query(query, {"planId": plan1_id})
        result2 = self.execute_query(query, {"planId": plan2_id})

        assert result1["moneyPlan"]["initialBalance"] == 1000.0
        assert result1["moneyPlan"]["notes"] == "Plan 1"
        assert result2["moneyPlan"]["initialBalance"] == 2000.0
        assert result2["moneyPlan"]["notes"] == "Plan 2"
