import pytest

from .utils import TestGraphQLAPI


@pytest.mark.django_db(transaction=True)
class TestAccountManagement(TestGraphQLAPI):
    def test_reuse_account_after_deletion(self, client):
        """Test that an account can be reused after being deleted from a plan."""
        # Get a test user
        user = self.get_test_user(client)

        # Create a new plan
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
        variables = {"input": {"initialBalance": 1000.0, "notes": "Test plan"}}

        result = self.execute_query(client, create_plan_mutation, user=user, variables=variables)
        assert "errors" not in result
        plan_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Add an account with buckets
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
                "name": "Test Account",
                "buckets": [{"name": "Default", "category": "default", "allocatedAmount": 1000.0}],
            }
        }

        result = self.execute_query(client, add_account_mutation, user=user, variables=account_variables)
        assert "errors" not in result
        account_id = result["moneyPlan"]["addAccount"]["data"]["id"]

        # Remove the account
        remove_account_mutation = """
        mutation RemoveAccount($input: RemoveAccountInput!) {
            moneyPlan {
                removeAccount(input: $input) {
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
        remove_variables = {
            "input": {
                "planId": plan_id,
                "accountId": account_id,
            }
        }

        result = self.execute_query(client, remove_account_mutation, user=user, variables=remove_variables)
        assert "errors" not in result
        assert "data" in result["moneyPlan"]["removeAccount"]

        # Try to add the same account again
        result = self.execute_query(client, add_account_mutation, user=user, variables=account_variables)
        assert "errors" not in result
        assert "data" in result["moneyPlan"]["addAccount"]

        # Verify the account was added back
        query = """
        query GetMoneyPlan($id: GlobalID!) {
            moneyPlan(id: $id) {
                id
                accounts {
                    id
                    name
                    buckets {
                        name
                        category
                        allocatedAmount
                    }
                }
            }
        }
        """
        result = self.execute_query(client, query, user=user, variables={"id": plan_id})
        assert "errors" not in result
        assert len(result["moneyPlan"]["accounts"]) == 1
        assert result["moneyPlan"]["accounts"][0]["name"] == "Test Account"
        assert len(result["moneyPlan"]["accounts"][0]["buckets"]) == 1
        assert result["moneyPlan"]["accounts"][0]["buckets"][0]["allocatedAmount"] == 1000.0
