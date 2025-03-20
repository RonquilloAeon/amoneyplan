from typing import Any, Dict

from django.test import Client


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

    def create_money_plan(self, client: Client, initial_balance: float, notes: str) -> str:
        """Helper method to create a money plan and return its ID."""
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
        variables = {"input": {"initialBalance": initial_balance, "notes": notes}}
        result = self.execute_query(client, create_plan_mutation, variables)
        return result["moneyPlan"]["startPlan"]["moneyPlan"]["id"]

    def add_account_with_full_balance(
        self, client: Client, plan_id: str, initial_balance: float, account_name: str
    ) -> str:
        """Helper method to add an account that allocates the full balance."""
        add_account_mutation = """
        mutation AddAccount($input: AddAccountInput!) {
            moneyPlan {
                addAccount(input: $input) {
                    success
                    moneyPlan {
                        accounts {
                            id
                        }
                    }
                }
            }
        }
        """
        account_variables = {
            "input": {
                "planId": plan_id,
                "name": account_name,
                "buckets": [
                    {"bucketName": "Default", "category": "default", "allocatedAmount": initial_balance}
                ],
            }
        }
        result = self.execute_query(client, add_account_mutation, account_variables)
        return result["moneyPlan"]["addAccount"]["moneyPlan"]["accounts"][0]["id"]

    def commit_plan(self, client: Client, plan_id: str) -> bool:
        """Helper method to commit a plan and return success status."""
        commit_mutation = """
        mutation CommitPlan($input: CommitPlanInput!) {
            moneyPlan {
                commitPlan(input: $input) {
                    success
                }
            }
        }
        """
        commit_variables = {"input": {"planId": plan_id}}
        result = self.execute_query(client, commit_mutation, commit_variables)
        return result["moneyPlan"]["commitPlan"]["success"]
