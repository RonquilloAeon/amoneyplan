import pytest
from strawberry.relay import to_base64

from .utils import TestGraphQLAPI


@pytest.mark.django_db(transaction=True)
class TestAccountSchema(TestGraphQLAPI):
    def test_change_account_configuration(self, client, money_planner):
        """Test changing the bucket configuration for an account."""
        # First create a plan and add an account
        result = self.execute_query(
            client,
            """
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
            """,
            {"input": {"initialBalance": 1000.0}},
        )
        assert "errors" not in result
        plan_id = result["moneyPlan"]["startPlan"]["moneyPlan"]["id"]

        # Add an account with initial buckets
        result = self.execute_query(
            client,
            """
            mutation AddAccount($input: AddAccountInput!) {
                moneyPlan {
                    addAccount(input: $input) {
                        success
                        moneyPlan {
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
                }
            }
            """,
            {
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
        assert result["moneyPlan"]["addAccount"]["success"]
        account = result["moneyPlan"]["addAccount"]["moneyPlan"]["accounts"][0]
        account_id = account["id"]

        # Now change the account configuration
        result = self.execute_query(
            client,
            """
            mutation ChangeAccountConfiguration($input: AccountConfigurationChangeInput!) {
                moneyPlan {
                    changeAccountConfiguration(input: $input) {
                        success
                        moneyPlan {
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
                        error {
                            message
                        }
                    }
                }
            }
            """,
            {
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
        assert result["moneyPlan"]["changeAccountConfiguration"]["success"]

        # Verify the changes
        plan = result["moneyPlan"]["changeAccountConfiguration"]["moneyPlan"]
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
                        success
                        error {
                            message
                        }
                    }
                }
            }
            """,
            {
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
        assert not result["moneyPlan"]["changeAccountConfiguration"]["success"]
        assert "Account with ID" in result["moneyPlan"]["changeAccountConfiguration"]["error"]["message"]

    def test_change_account_configuration_already_committed(self, client, money_planner):
        """Test that we cannot change the bucket configuration for an account in a committed plan."""
        result = self.execute_query(
            client,
            """
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
            """,
            {"input": {"initialBalance": 700}},
        )
        assert "errors" not in result
        plan_id = result["moneyPlan"]["startPlan"]["moneyPlan"]["id"]

        # Add an account with buckets
        result = self.execute_query(
            client,
            """
            mutation AddAccount($input: AddAccountInput!) {
                moneyPlan {
                    addAccount(input: $input) {
                        success
                        moneyPlan {
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
                }
            }
            """,
            {
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
        account = result["moneyPlan"]["addAccount"]["moneyPlan"]["accounts"][0]
        account_id = account["id"]

        # Try to change configuration in a committed plan
        result = self.execute_query(
            client,
            """
            mutation CommitPlan($input: CommitPlanInput!) {
                moneyPlan {
                    commitPlan(input: $input) {
                        success
                    }
                }
            }
            """,
            {"input": {"planId": plan_id}},
        )
        assert "errors" not in result

        result = self.execute_query(
            client,
            """
            mutation ChangeAccountConfiguration($input: AccountConfigurationChangeInput!) {
                moneyPlan {
                    changeAccountConfiguration(input: $input) {
                        success
                        error {
                            message
                        }
                        moneyPlan {
                            accounts {
                                id
                                name
                            }
                        }
                    }
                }
            }
            """,
            {
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
        assert not result["moneyPlan"]["changeAccountConfiguration"]["success"]
        assert (
            "Cannot change account configuration in a committed plan"
            in result["moneyPlan"]["changeAccountConfiguration"]["error"]["message"]
        )

    @pytest.mark.parametrize("is_checked", [True, False])
    def test_account_check(self, client, money_planner, is_checked):
        """Test setting the checked state of an account."""
        # First create a plan and add an account
        plan_id = self.create_money_plan(client, 1000.0, "Test Plan")
        account_id = self.add_account_with_full_balance(client, plan_id, 1000.0, "Test Account")

        if is_checked:
            self.commit_plan(client, plan_id)

        # Check off the account
        result = self.execute_query(
            client,
            """
            mutation SetAccountCheckedState($input: SetAccountCheckedStateInput!) {
                moneyPlan {
                    setAccountCheckedState(input: $input) {
                        success
                        moneyPlan {
                            accounts {
                                id
                                isChecked
                            }
                        }
                    }
                }
            }
            """,
            {
                "input": {
                    "planId": plan_id,
                    "accountId": account_id,
                    "isChecked": True,
                }
            },
        )

        assert "errors" not in result
        assert result["moneyPlan"]["setAccountCheckedState"]["success"]
        assert result["moneyPlan"]["setAccountCheckedState"]["moneyPlan"]["accounts"][0]["isChecked"]

        # Uncheck the account
        for request in range(2):
            result = self.execute_query(
                client,
                """
                mutation SetAccountCheckedState($input: SetAccountCheckedStateInput!) {
                    moneyPlan {
                        setAccountCheckedState(input: $input) {
                            success
                            error {
                                message
                            }
                            moneyPlan {
                                accounts {
                                    id
                                    isChecked
                                }
                            }
                        }
                    }
                }
                """,
                {
                    "input": {
                        "planId": plan_id,
                        "accountId": account_id,
                        "isChecked": False,
                    }
                },
            )

            assert "errors" not in result

            if request == 0:
                assert result["moneyPlan"]["setAccountCheckedState"]["success"]
                assert not result["moneyPlan"]["setAccountCheckedState"]["moneyPlan"]["accounts"][0][
                    "isChecked"
                ]
            else:
                assert not result["moneyPlan"]["setAccountCheckedState"]["success"]
                assert (
                    result["moneyPlan"]["setAccountCheckedState"]["error"]["message"]
                    == "Account is already unchecked"
                )
