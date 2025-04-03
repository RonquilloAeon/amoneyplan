import json
from dataclasses import dataclass
from typing import Any, Dict

import pytest
from django.test import Client
from faker import Faker


@dataclass
class TestUser:
    access_token: str
    email: str


class TestGraphQLAPI:
    _fake: Faker | None = None

    @property
    def fake(self) -> Faker:
        if not self._fake:
            self._fake = Faker()

        return self._fake

    """Tests for GraphQL API."""

    def get_test_user(self, client: Client, email: str | None = None) -> TestUser:
        email = email or self.fake.email()
        query = """
        mutation($username: String!, $email: String!, $password: String!) {
            auth {
                register(username: $username, email: $email, password: $password) {
                    success
                    error
                    token
                }
            }
        }
        """
        variables = {
            "username": self.fake.user_name(),
            "email": email,
            "password": self.fake.password(length=12, special_chars=True, digits=True, upper_case=True),
        }
        result = self.execute_query(client, query, variables=variables)

        if result["auth"]["register"]["success"]:
            return TestUser(
                access_token=result["auth"]["register"]["token"],
                email=email,
            )
        else:
            raise Exception(f"Failed to create test user: {json.dumps(result['auth']['register'], indent=2)}")

    def execute_query(
        self,
        client: Client,
        query: str,
        fail_on_error: bool = True,
        user: TestUser | None = None,
        variables: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Execute a GraphQL query and return the response."""
        data = {
            "query": query,
            "variables": variables,
        }
        headers = {}

        if user:
            # If a user is provided, include the access token in the headers
            headers["Authorization"] = f"Bearer {user.access_token}"

        response = client.post(
            "/graphql/", data=json.dumps(data), content_type="application/json", headers=headers
        )
        result = response.json()

        if "errors" in result and fail_on_error:
            pytest.fail(f"errors returned: {result['errors']}")

        return result["data"]

    def create_money_plan(self, client: Client, initial_balance: float, notes: str) -> str:
        """Helper method to create a money plan and return its ID."""
        # Get a test user if one doesn't exist
        user = self.get_test_user(client)

        create_plan_mutation = """
        mutation StartPlan($input: PlanStartInput!) {
            moneyPlan {
                startPlan(input: $input) {
                    ...on Success {
                        data
                    }
                    ...on ApplicationError {
                        message
                    }
                    ...on UnexpectedError {
                        message
                    }
                }
            }
        }
        """
        variables = {"input": {"initialBalance": initial_balance, "notes": notes}}
        result = self.execute_query(client, create_plan_mutation, user=user, variables=variables)
        return result["moneyPlan"]["startPlan"]["data"]["id"]

    def add_account_with_full_balance(
        self, client: Client, plan_id: str, initial_balance: float, account_name: str
    ) -> str:
        """Helper method to add an account that allocates the full balance."""
        # Get a test user if one doesn't exist
        user = self.get_test_user(client)

        add_account_mutation = """
        mutation AddAccount($input: AddAccountInput!) {
            moneyPlan {
                addAccount(input: $input) {
                    ...on Success {
                        data
                    }
                    ...on ApplicationError {
                        message
                    }
                    ...on UnexpectedError {
                        message
                    }
                }
            }
        }
        """
        account_variables = {
            "input": {
                "planId": plan_id,
                "name": account_name,
                "buckets": [{"name": "Default", "category": "default", "allocatedAmount": initial_balance}],
            }
        }
        result = self.execute_query(client, add_account_mutation, user=user, variables=account_variables)
        return result["moneyPlan"]["addAccount"]["data"]["id"]

    def commit_plan(self, client: Client, plan_id: str) -> bool:
        """Helper method to commit a plan and return success status."""
        # Get a test user if one doesn't exist
        user = self.get_test_user(client)

        commit_mutation = """
        mutation CommitPlan($input: CommitPlanInput!) {
            moneyPlan {
                commitPlan(input: $input) {
                    ...on Success {
                        data
                    }
                    ...on ApplicationError {
                        message
                    }
                    ...on UnexpectedError {
                        message
                    }
                }
            }
        }
        """
        commit_variables = {"input": {"planId": plan_id}}
        result = self.execute_query(client, commit_mutation, user=user, variables=commit_variables)
        return "data" in result["moneyPlan"]["commitPlan"]

    def create_test_plan(self, client, user, initial_balance=1000.0, notes="Test Plan") -> tuple[str, str]:
        """Create a test plan with a single account and bucket."""
        create_plan_mutation = """
        mutation StartPlan($input: PlanStartInput!) {
            moneyPlan {
                startPlan(input: $input) {
                    ...on Success {
                        data
                    }
                    ...on ApplicationError {
                        message
                    }
                    ...on UnexpectedError {
                        message
                    }
                }
            }
        }
        """
        variables = {"input": {"initialBalance": initial_balance, "notes": notes}}

        result = self.execute_query(client, create_plan_mutation, user=user, variables=variables)
        plan_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Create an account first
        account_id = self.add_account(client, user, "Test Account")

        # Add the account to the plan
        add_account_mutation = """
        mutation AddAccount($input: AddAccountInput!) {
            moneyPlan {
                addAccount(input: $input) {
                    ...on Success {
                        data
                    }
                    ...on ApplicationError {
                        message
                    }
                    ...on UnexpectedError {
                        message
                    }
                }
            }
        }
        """
        account_variables = {
            "input": {
                "planId": plan_id,
                "accountId": account_id,
                "buckets": [{"name": "Default", "category": "default", "allocatedAmount": initial_balance}],
            }
        }

        result = self.execute_query(client, add_account_mutation, user=user, variables=account_variables)
        return plan_id, account_id

    def create_account(self, client: Client, user: TestUser, name: str) -> str:
        """Helper method to create an account and return its ID."""
        add_account_mutation = """
        mutation CreateAccount($input: CreateAccountInput!) {
            account {
                create(input: $input) {
                    ...on Success {
                        data
                    }
                    ...on ApplicationError {
                        message
                    }
                    ...on UnexpectedError {
                        message
                    }
                }
            }
        }
        """
        variables = {"input": {"name": name}}
        result = self.execute_query(client, add_account_mutation, user=user, variables=variables)
        return result["account"]["create"]["data"]["id"]
