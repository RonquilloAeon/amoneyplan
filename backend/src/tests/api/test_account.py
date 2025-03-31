import pytest
from strawberry.relay import to_base64

from .utils import TestGraphQLAPI


@pytest.mark.django_db(transaction=True)
class TestAccountSchema(TestGraphQLAPI):
    def test_accounts_query(self, client, money_planner):
        """Test querying user's accounts."""
        # Get a test user
        user = self.get_test_user(client)

        # First create a plan to work within
        result = self.execute_query(
            client,
            """
            mutation StartPlan($input: PlanStartInput!) {
                moneyPlan {
                    startPlan(input: $input) {
                        ... on Success {
                            data
                        }
                        ... on ApplicationError {
                            message
                        }
                        ... on UnexpectedError {
                            message
                        }
                    }
                }
            }
            """,
            user=user,
            variables={"input": {"initialBalance": 1000.0}},
        )
        assert "errors" not in result
        plan_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Add three accounts to the plan with different names
        test_account_names = ["Test Account 1", "Test Account 2", "Test Account 3"]
        for account_name in test_account_names:
            result = self.execute_query(
                client,
                """
                mutation AddAccount($input: AddAccountInput!) {
                    moneyPlan {
                        addAccount(input: $input) {
                            ... on Success {
                                data
                            }
                            ... on ApplicationError {
                                message
                            }
                            ... on UnexpectedError {
                                message
                            }
                        }
                    }
                }
                """,
                user=user,
                variables={
                    "input": {
                        "planId": plan_id,
                        "name": account_name,
                        "buckets": [
                            {"bucketName": "Default", "category": "default", "allocatedAmount": 100.0}
                        ],
                    }
                },
            )
            assert "errors" not in result

        # Now query the standalone accounts
        result = self.execute_query(
            client,
            """
            query GetAccounts {
                accounts {
                    id
                    name
                }
            }
            """,
            user=user,
        )

        # Verify the query results
        assert "errors" not in result
        assert "accounts" in result

        # Check that all accounts are returned
        returned_accounts = result["accounts"]
        assert len(returned_accounts) >= len(test_account_names)

        # Check that all our created accounts are in the returned results
        returned_names = [account["name"] for account in returned_accounts]
        for name in test_account_names:
            assert name in returned_names

    def test_change_account_configuration(self, client, money_planner):
        """Test changing the bucket configuration for an account."""
        # Get a test user
        user = self.get_test_user(client)

        # First create a plan and add an account
        result = self.execute_query(
            client,
            """
            mutation StartPlan($input: PlanStartInput!) {
                moneyPlan {
                    startPlan(input: $input) {
                        ... on Success {
                            data
                        }
                        ... on ApplicationError {
                            message
                        }
                        ... on UnexpectedError {
                            message
                        }
                    }
                }
            }
            """,
            user=user,
            variables={"input": {"initialBalance": 1000.0}},
        )
        assert "errors" not in result
        plan_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Add an account with initial buckets
        result = self.execute_query(
            client,
            """
            mutation AddAccount($input: AddAccountInput!) {
                moneyPlan {
                    addAccount(input: $input) {
                        ... on Success {
                            data
                        }
                        ... on ApplicationError {
                            message
                        }
                        ... on UnexpectedError {
                            message
                        }
                    }
                }
            }
            """,
            user=user,
            variables={
                "input": {
                    "planId": plan_id,
                    "name": "Test Account",
                    "buckets": [
                        {
                            "bucketName": "Savings",
                            "category": "savings",
                            "allocatedAmount": 400.0,
                        },
                        {
                            "bucketName": "Bills",
                            "category": "expenses",
                            "allocatedAmount": 300.0,
                        },
                    ],
                }
            },
        )
        assert "errors" not in result
        account_id = result["moneyPlan"]["addAccount"]["data"]["id"]

        # Now change the account configuration
        result = self.execute_query(
            client,
            """
            mutation ChangeAccountConfiguration($input: AccountConfigurationChangeInput!) {
                moneyPlan {
                    changeAccountConfiguration(input: $input) {
                        ... on Success {
                            data
                        }
                        ... on ApplicationError {
                            message
                        }
                        ... on UnexpectedError {
                            message
                        }
                    }
                }
            }
            """,
            user=user,
            variables={
                "input": {
                    "planId": plan_id,
                    "accountId": account_id,
                    "newBucketConfig": [
                        {
                            "bucketName": "Emergency Fund",
                            "category": "savings",
                            "allocatedAmount": 500.0,
                        },
                        {
                            "bucketName": "Utilities",
                            "category": "expenses",
                            "allocatedAmount": 100.0,
                        },
                    ],
                }
            },
        )
        assert "errors" not in result
        assert "data" in result["moneyPlan"]["changeAccountConfiguration"]

        # Verify the changes through a separate query to check bucket config
        query_result = self.execute_query(
            client,
            """
            query GetMoneyPlan($planId: GlobalID!) {
                moneyPlan(planId: $planId) {
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
                }
            }
            """,
            user=user,
            variables={"planId": plan_id},
        )

        assert "errors" not in query_result
        plan = query_result["moneyPlan"]
        account = plan["accounts"][0]
        buckets = {b["bucketName"]: b for b in account["buckets"]}

        # Old buckets should be gone
        assert "Savings" not in buckets
        assert "Bills" not in buckets

        # New buckets should be present with correct amounts
        assert "Emergency Fund" in buckets
        assert buckets["Emergency Fund"]["allocatedAmount"] == 500.0
        assert buckets["Utilities"]["allocatedAmount"] == 100.0

        # Remaining balance should reflect the changes (1000 - 600 = 400 remaining)
        assert plan["remainingBalance"] == 400.0

        # Test error cases
        # Try to change configuration of non-existent account
        result = self.execute_query(
            client,
            """
            mutation ChangeAccountConfiguration($input: AccountConfigurationChangeInput!) {
                moneyPlan {
                    changeAccountConfiguration(input: $input) {
                        ... on Success {
                            data
                        }
                        ... on ApplicationError {
                            message
                        }
                        ... on UnexpectedError {
                            message
                        }
                    }
                }
            }
            """,
            user=user,
            variables={
                "input": {
                    "planId": plan_id,
                    "accountId": to_base64(
                        "Account", "00000000-0000-0000-0000-000000000000"
                    ),  # Non-existent account ID
                    "newBucketConfig": [
                        {
                            "bucketName": "Test",
                            "category": "test",
                            "allocatedAmount": 100.0,
                        }
                    ],
                }
            },
        )
        assert "errors" not in result
        assert "message" in result["moneyPlan"]["changeAccountConfiguration"]
        assert "Account with ID" in result["moneyPlan"]["changeAccountConfiguration"]["message"]

    def test_change_account_configuration_already_committed(self, client, money_planner):
        """Test that we cannot change the bucket configuration for an account in a committed plan."""
        # Get a test user
        user = self.get_test_user(client)

        result = self.execute_query(
            client,
            """
            mutation StartPlan($input: PlanStartInput!) {
                moneyPlan {
                    startPlan(input: $input) {
                        ... on Success {
                            data
                        }
                        ... on ApplicationError {
                            message
                        }
                        ... on UnexpectedError {
                            message
                        }
                    }
                }
            }
            """,
            user=user,
            variables={"input": {"initialBalance": 700}},
        )
        assert "errors" not in result
        plan_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Add an account with buckets
        result = self.execute_query(
            client,
            """
            mutation AddAccount($input: AddAccountInput!) {
                moneyPlan {
                    addAccount(input: $input) {
                        ... on Success {
                            data
                        }
                        ... on ApplicationError {
                            message
                        }
                        ... on UnexpectedError {
                            message
                        }
                    }
                }
            }
            """,
            user=user,
            variables={
                "input": {
                    "planId": plan_id,
                    "name": "Test Account",
                    "buckets": [
                        {
                            "bucketName": "Savings",
                            "category": "savings",
                            "allocatedAmount": 400.0,
                        },
                        {
                            "bucketName": "Bills",
                            "category": "expenses",
                            "allocatedAmount": 300.0,
                        },
                    ],
                }
            },
        )
        assert "errors" not in result
        account_id = result["moneyPlan"]["addAccount"]["data"]["id"]

        # Commit the plan
        result = self.execute_query(
            client,
            """
            mutation CommitPlan($input: CommitPlanInput!) {
                moneyPlan {
                    commitPlan(input: $input) {
                        ... on Success {
                            data
                        }
                        ... on ApplicationError {
                            message
                        }
                        ... on UnexpectedError {
                            message
                        }
                    }
                }
            }
            """,
            user=user,
            variables={"input": {"planId": plan_id}},
        )
        assert "errors" not in result

        # Try to change configuration in a committed plan
        result = self.execute_query(
            client,
            """
            mutation ChangeAccountConfiguration($input: AccountConfigurationChangeInput!) {
                moneyPlan {
                    changeAccountConfiguration(input: $input) {
                        ... on Success {
                            data
                        }
                        ... on ApplicationError {
                            message
                        }
                        ... on UnexpectedError {
                            message
                        }
                    }
                }
            }
            """,
            user=user,
            variables={
                "input": {
                    "planId": plan_id,
                    "accountId": account_id,
                    "newBucketConfig": [
                        {
                            "bucketName": "Test",
                            "category": "test",
                            "allocatedAmount": 100.0,
                        }
                    ],
                }
            },
        )
        assert "errors" not in result
        assert "message" in result["moneyPlan"]["changeAccountConfiguration"]
        assert (
            "Cannot change account configuration in a committed plan"
            in result["moneyPlan"]["changeAccountConfiguration"]["message"]
        )

    @pytest.mark.parametrize("is_checked", [True, False])
    def test_account_check(self, client, money_planner, is_checked):
        """Test setting the checked state of an account."""
        # Get a test user
        user = self.get_test_user(client)

        # First create a plan and add an account
        result = self.execute_query(
            client,
            """
            mutation StartPlan($input: PlanStartInput!) {
                moneyPlan {
                    startPlan(input: $input) {
                        ... on Success {
                            data
                        }
                        ... on ApplicationError {
                            message
                        }
                        ... on UnexpectedError {
                            message
                        }
                    }
                }
            }
            """,
            user=user,
            variables={"input": {"initialBalance": 1000.0, "notes": "Test Plan"}},
        )
        assert "errors" not in result
        plan_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Add an account with a bucket to satisfy invariants
        result = self.execute_query(
            client,
            """
            mutation AddAccount($input: AddAccountInput!) {
                moneyPlan {
                    addAccount(input: $input) {
                        ... on Success {
                            data
                        }
                        ... on ApplicationError {
                            message
                        }
                        ... on UnexpectedError {
                            message
                        }
                    }
                }
            }
            """,
            user=user,
            variables={
                "input": {
                    "planId": plan_id,
                    "name": "Test Account",
                    "buckets": [{"bucketName": "Default", "category": "default", "allocatedAmount": 1000.0}],
                }
            },
        )
        assert "errors" not in result
        account_id = result["moneyPlan"]["addAccount"]["data"]["id"]

        if is_checked:
            # Commit the plan if needed for the test
            commit_mutation = """
            mutation CommitPlan($input: CommitPlanInput!) {
                moneyPlan {
                    commitPlan(input: $input) {
                        ... on Success {
                            data
                        }
                        ... on ApplicationError {
                            message
                        }
                        ... on UnexpectedError {
                            message
                        }
                    }
                }
            }
            """
            commit_variables = {"input": {"planId": plan_id}}
            commit_result = self.execute_query(client, commit_mutation, user=user, variables=commit_variables)
            assert "data" in commit_result["moneyPlan"]["commitPlan"]

        # Check off the account
        result = self.execute_query(
            client,
            """
            mutation SetAccountCheckedState($input: SetAccountCheckedStateInput!) {
                moneyPlan {
                    setAccountCheckedState(input: $input) {
                        ... on Success {
                            data
                        }
                        ... on ApplicationError {
                            message
                        }
                        ... on UnexpectedError {
                            message
                        }
                    }
                }
            }
            """,
            user=user,
            variables={
                "input": {
                    "planId": plan_id,
                    "accountId": account_id,
                    "isChecked": True,
                }
            },
        )
        assert "errors" not in result
        assert "data" in result["moneyPlan"]["setAccountCheckedState"]

        # Verify the account is checked via query
        query_result = self.execute_query(
            client,
            """
            query GetMoneyPlan($planId: GlobalID!) {
                moneyPlan(planId: $planId) {
                    accounts {
                        id
                        isChecked
                    }
                }
            }
            """,
            user=user,
            variables={"planId": plan_id},
        )

        assert query_result["moneyPlan"]["accounts"][0]["isChecked"] is True

        # Uncheck the account
        for request in range(2):
            result = self.execute_query(
                client,
                """
                mutation SetAccountCheckedState($input: SetAccountCheckedStateInput!) {
                    moneyPlan {
                        setAccountCheckedState(input: $input) {
                            ... on Success {
                                data
                            }
                            ... on ApplicationError {
                                message
                            }
                            ... on UnexpectedError {
                                message
                            }
                        }
                    }
                }
                """,
                user=user,
                variables={
                    "input": {
                        "planId": plan_id,
                        "accountId": account_id,
                        "isChecked": False,
                    }
                },
            )
            assert "errors" not in result

            if request == 0:
                assert "data" in result["moneyPlan"]["setAccountCheckedState"]

                # Verify the account is unchecked via query
                query_result = self.execute_query(
                    client,
                    """
                    query GetMoneyPlan($planId: GlobalID!) {
                        moneyPlan(planId: $planId) {
                            accounts {
                                id
                                isChecked
                            }
                        }
                    }
                    """,
                    user=user,
                    variables={"planId": plan_id},
                )

                assert query_result["moneyPlan"]["accounts"][0]["isChecked"] is False
            else:
                assert "message" in result["moneyPlan"]["setAccountCheckedState"]
                assert (
                    result["moneyPlan"]["setAccountCheckedState"]["message"] == "Account is already unchecked"
                )
