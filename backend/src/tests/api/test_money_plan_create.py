from datetime import date, timedelta

import pytest

from .utils import TestGraphQLAPI


@pytest.mark.django_db(transaction=True)
class TestMoneyPlan(TestGraphQLAPI):
    def test_allocation_invariants(self, client):
        """Test that plan allocations must equal initial balance for commit."""
        user = self.get_test_user(client)

        # Create a plan
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
        variables = {"input": {"initialBalance": 1000.0, "notes": "Test plan invariants"}}
        result = self.execute_query(client, create_plan_mutation, user=user, variables=variables)
        plan_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Add an account with buckets that don't sum to initial balance
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
                "buckets": [
                    {
                        "name": "Savings",
                        "category": "savings",
                        "allocatedAmount": 500.0,  # Only allocating half
                    }
                ],
            }
        }
        result = self.execute_query(client, add_account_mutation, user=user, variables=account_variables)
        assert "errors" not in result

        # Try to commit - should fail
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
        assert "equal initial balance" in result["moneyPlan"]["commitPlan"]["message"].lower()

    def test_plan_isolation(self, client):
        """Test that plans are properly isolated in the database."""
        user = self.get_test_user(client)

        # Create first plan
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
        variables1 = {"input": {"initialBalance": 1000.0, "notes": "Plan 1"}}

        result1 = self.execute_query(client, create_plan_mutation, user=user, variables=variables1)
        assert "errors" not in result1
        plan1_id = result1["moneyPlan"]["startPlan"]["data"]["id"]

        # Add an account with a bucket that allocates the full balance
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
                "planId": plan1_id,
                "name": "Test Account",
                "buckets": [{"name": "Default", "category": "default", "allocatedAmount": 1000.0}],
            }
        }

        result = self.execute_query(client, add_account_mutation, user=user, variables=account_variables)
        assert "errors" not in result
        assert "data" in result["moneyPlan"]["addAccount"]

        # Commit first plan
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
        commit_variables = {"input": {"planId": plan1_id}}
        commit_result = self.execute_query(client, commit_mutation, user=user, variables=commit_variables)
        assert "errors" not in commit_result
        assert "data" in commit_result["moneyPlan"]["commitPlan"]

        # Create second plan
        variables2 = {"input": {"initialBalance": 2000.0, "notes": "Plan 2"}}
        result2 = self.execute_query(client, create_plan_mutation, user=user, variables=variables2)
        assert "errors" not in result2
        plan2_id = result2["moneyPlan"]["startPlan"]["data"]["id"]

        # Add an account to second plan
        account_variables2 = {
            "input": {
                "planId": plan2_id,
                "name": "Test Account 2",
                "buckets": [{"name": "Default", "category": "default", "allocatedAmount": 2000.0}],
            }
        }
        result = self.execute_query(client, add_account_mutation, user=user, variables=account_variables2)
        assert "errors" not in result
        assert "data" in result["moneyPlan"]["addAccount"]

        # Query both plans to verify they are isolated
        query = """
        query GetMoneyPlan($id: GlobalID!) {
            moneyPlan(id: $id) {
                id
                initialBalance
                remainingBalance
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

        # Check first plan
        result = self.execute_query(client, query, user=user, variables={"id": plan1_id})
        assert "errors" not in result
        assert result["moneyPlan"]["initialBalance"] == 1000.0
        assert result["moneyPlan"]["remainingBalance"] == 0.0
        assert len(result["moneyPlan"]["accounts"]) == 1
        assert result["moneyPlan"]["accounts"][0]["name"] == "Test Account"
        assert result["moneyPlan"]["accounts"][0]["buckets"][0]["allocatedAmount"] == 1000.0

        # Check second plan
        result = self.execute_query(client, query, user=user, variables={"id": plan2_id})
        assert "errors" not in result
        assert result["moneyPlan"]["initialBalance"] == 2000.0
        assert result["moneyPlan"]["remainingBalance"] == 0.0
        assert len(result["moneyPlan"]["accounts"]) == 1
        assert result["moneyPlan"]["accounts"][0]["name"] == "Test Account 2"
        assert result["moneyPlan"]["accounts"][0]["buckets"][0]["allocatedAmount"] == 2000.0

    def test_cannot_create_multiple_uncommitted_plans(self, client, money_planner):
        """Test that we cannot create multiple uncommitted plans."""
        user = self.get_test_user(client)

        # Create first plan
        create_mutation = """
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

        # Create first plan
        result1 = self.execute_query(
            client,
            create_mutation,
            user=user,
            variables={"input": {"initialBalance": 1000.0, "notes": "First plan"}},
        )
        assert "errors" not in result1
        assert "data" in result1["moneyPlan"]["startPlan"]
        plan1_id = result1["moneyPlan"]["startPlan"]["data"]["id"]

        # Try to create second plan without committing first one
        result2 = self.execute_query(
            client,
            create_mutation,
            user=user,
            variables={"input": {"initialBalance": 2000.0, "notes": "Second plan"}},
        )
        assert "errors" not in result2
        assert "message" in result2["moneyPlan"]["startPlan"]
        assert "uncommitted plan" in result2["moneyPlan"]["startPlan"]["message"].lower()

        # Add account with full balance to satisfy commit invariants
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
                "planId": plan1_id,
                "name": "Account 1",
                "buckets": [{"name": "Default", "category": "default", "allocatedAmount": 1000.0}],
            }
        }
        self.execute_query(client, add_account_mutation, user=user, variables=account_variables)

        # Commit first plan
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
        commit_result = self.execute_query(
            client,
            commit_mutation,
            user=user,
            variables={"input": {"planId": plan1_id}},
        )
        assert "data" in commit_result["moneyPlan"]["commitPlan"]

        # Now we should be able to create another plan
        result3 = self.execute_query(
            client,
            create_mutation,
            user=user,
            variables={"input": {"initialBalance": 2000.0, "notes": "Second plan after commit"}},
        )
        assert "errors" not in result3
        assert "data" in result3["moneyPlan"]["startPlan"]

    def test_start_plan_with_copied_structure(self, client, money_planner):
        """Test starting a plan with structure copied from a specific plan."""
        user = self.get_test_user(client)

        # Create first plan with accounts and buckets
        result = self.execute_query(
            client,
            """
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
            """,
            user=user,
            variables={"input": {"initialBalance": 1000.0, "notes": "Plan 1"}},
        )
        assert "errors" not in result
        plan1_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Add first account with two buckets
        result = self.execute_query(
            client,
            """
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
            """,
            user=user,
            variables={
                "input": {
                    "planId": plan1_id,
                    "name": "Checking Account",
                    "buckets": [
                        {"name": "Bills", "category": "expenses", "allocatedAmount": 600.0},
                        {"name": "Food", "category": "expenses", "allocatedAmount": 200.0},
                    ],
                }
            },
        )
        assert "errors" not in result

        # Add second account with one bucket
        result = self.execute_query(
            client,
            """
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
            """,
            user=user,
            variables={
                "input": {
                    "planId": plan1_id,
                    "name": "Savings Account",
                    "buckets": [
                        {"name": "Emergency Fund", "category": "savings", "allocatedAmount": 200.0},
                    ],
                }
            },
        )
        assert "errors" not in result

        # Commit the plan
        result = self.execute_query(
            client,
            """
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
            """,
            user=user,
            variables={"input": {"planId": plan1_id}},
        )
        assert "errors" not in result
        assert "data" in result["moneyPlan"]["commitPlan"]

        # Now create a second plan with copied structure
        result = self.execute_query(
            client,
            """
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
            """,
            user=user,
            variables={
                "input": {
                    "initialBalance": 2000.0,
                    "notes": "Plan with copied structure",
                    "copyFrom": plan1_id,
                }
            },
        )
        assert "errors" not in result
        assert "data" in result["moneyPlan"]["startPlan"]

        # Verify the new plan has the same account structure but with zero allocations
        new_plan_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Query the new plan to check its structure
        result = self.execute_query(
            client,
            """
            query GetMoneyPlan($id: GlobalID!) {
                moneyPlan(id: $id) {
                    id
                    initialBalance
                    remainingBalance
                    accounts {
                        name
                        buckets {
                            name
                            category
                            allocatedAmount
                        }
                    }
                }
            }
            """,
            user=user,
            variables={"id": new_plan_id},
        )

        new_plan = result["moneyPlan"]
        assert new_plan["initialBalance"] == 2000.0
        assert new_plan["remainingBalance"] == 2000.0  # No allocations yet
        # Should have the same number of accounts
        assert len(new_plan["accounts"]) == 2
        # Verify account names and bucket structure were copied
        accounts = {account["name"]: account for account in new_plan["accounts"]}

        # Check first account (Checking Account)
        checking = accounts.get("Checking Account")
        assert checking is not None
        assert len(checking["buckets"]) == 2
        buckets = {b["name"]: b for b in checking["buckets"]}
        assert "Bills" in buckets
        assert buckets["Bills"]["category"] == "expenses"
        assert buckets["Bills"]["allocatedAmount"] == 0.0  # Zero allocation
        assert "Food" in buckets
        assert buckets["Food"]["category"] == "expenses"
        assert buckets["Food"]["allocatedAmount"] == 0.0  # Zero allocation

        # Check second account (Savings Account)
        savings = accounts.get("Savings Account")
        assert savings is not None
        assert len(savings["buckets"]) == 1
        assert savings["buckets"][0]["name"] == "Emergency Fund"
        assert savings["buckets"][0]["category"] == "savings"
        assert savings["buckets"][0]["allocatedAmount"] == 0.0  # Zero allocation

    def test_create_plan_with_future_date(self, client, money_planner):
        """Test creating a plan with a future date."""
        user = self.get_test_user(client)

        future_date = (date.today() + timedelta(days=30)).isoformat()

        result = self.execute_query(
            client,
            """
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
            """,
            user=user,
            variables={"input": {"initialBalance": 1000.0, "notes": "Future plan", "planDate": future_date}},
        )

        assert "errors" not in result
        assert "data" in result["moneyPlan"]["startPlan"]
        assert result["moneyPlan"]["startPlan"]["data"]["plan_date"] == future_date
        assert result["moneyPlan"]["startPlan"]["data"]["created_at"] is not None

    def test_create_plan_with_account(self, client):
        """Test creating a plan with an account."""
        user = self.get_test_user(client)

        # Create a plan
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
        variables = {"input": {"initialBalance": 1000.0, "notes": "Test Plan"}}

        result = self.execute_query(client, create_plan_mutation, user=user, variables=variables)
        assert "errors" not in result
        plan_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Add an account
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
                "name": "Savings Account",
                "buckets": [{"name": "Savings", "category": "savings", "allocatedAmount": 1000.0}],
            }
        }

        result = self.execute_query(client, add_account_mutation, user=user, variables=account_variables)
        assert "errors" not in result
        assert "data" in result["moneyPlan"]["addAccount"]

        # Query the plan to verify the account was added
        query = """
        query GetMoneyPlan($id: GlobalID!) {
            moneyPlan(id: $id) {
                id
                initialBalance
                remainingBalance
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
        assert result["moneyPlan"]["initialBalance"] == 1000.0
        assert result["moneyPlan"]["remainingBalance"] == 0.0
        assert len(result["moneyPlan"]["accounts"]) == 1
        assert result["moneyPlan"]["accounts"][0]["name"] == "Savings Account"
        assert result["moneyPlan"]["accounts"][0]["buckets"][0]["name"] == "Savings"
        assert result["moneyPlan"]["accounts"][0]["buckets"][0]["allocatedAmount"] == 1000.0

    def test_create_plan_with_multiple_accounts(self, client):
        """Test creating a plan with multiple accounts."""
        user = self.get_test_user(client)

        # Create a plan
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
        variables = {"input": {"initialBalance": 1000.0, "notes": "Test Plan"}}

        result = self.execute_query(client, create_plan_mutation, user=user, variables=variables)
        assert "errors" not in result
        plan_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Add first account
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
                "name": "Checking Account",
                "buckets": [
                    {"name": "Bills", "category": "expenses", "allocatedAmount": 600.0},
                    {"name": "Food", "category": "expenses", "allocatedAmount": 200.0},
                ],
            }
        }

        result = self.execute_query(client, add_account_mutation, user=user, variables=account_variables)
        assert "errors" not in result
        assert "data" in result["moneyPlan"]["addAccount"]

        # Add second account
        account_variables2 = {
            "input": {
                "planId": plan_id,
                "name": "Savings Account",
                "buckets": [
                    {"name": "Emergency Fund", "category": "savings", "allocatedAmount": 200.0},
                ],
            }
        }

        result = self.execute_query(client, add_account_mutation, user=user, variables=account_variables2)
        assert "errors" not in result
        assert "data" in result["moneyPlan"]["addAccount"]

        # Query the plan to verify both accounts were added
        query = """
        query GetMoneyPlan($id: GlobalID!) {
            moneyPlan(id: $id) {
                id
                initialBalance
                remainingBalance
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
        assert result["moneyPlan"]["initialBalance"] == 1000.0
        assert result["moneyPlan"]["remainingBalance"] == 0.0
        assert len(result["moneyPlan"]["accounts"]) == 2

        # Find the checking account
        checking = next(
            account for account in result["moneyPlan"]["accounts"] if account["name"] == "Checking Account"
        )
        buckets = {b["name"]: b for b in checking["buckets"]}
        assert len(buckets) == 2
        assert buckets["Bills"]["allocatedAmount"] == 600.0
        assert buckets["Food"]["allocatedAmount"] == 200.0

        # Find the savings account
        savings = next(
            account for account in result["moneyPlan"]["accounts"] if account["name"] == "Savings Account"
        )
        assert len(savings["buckets"]) == 1
        assert savings["buckets"][0]["name"] == "Emergency Fund"
        assert savings["buckets"][0]["allocatedAmount"] == 200.0
