from datetime import date, timedelta

import pytest
from utils import TestGraphQLAPI


@pytest.mark.django_db(transaction=True)
class TestSchema(TestGraphQLAPI):
    """Tests for GraphQL API."""

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

    def test_money_plans_query(self, client, money_planner):
        """Test querying all money plans with pagination."""
        # Create and commit first plan
        plan1_id = self.create_money_plan(client, 1000.0, "Plan 1")
        self.add_account_with_full_balance(client, plan1_id, 1000.0, "Account 1")
        assert self.commit_plan(client, plan1_id)

        # Create and commit second plan
        plan2_id = self.create_money_plan(client, 2000.0, "Plan 2")
        self.add_account_with_full_balance(client, plan2_id, 2000.0, "Account 2")
        assert self.commit_plan(client, plan2_id)

        # Query all plans
        query = """
        query GetMoneyPlans {
            moneyPlans {
                edges {
                    node {
                        id
                        initialBalance
                        notes
                        isCommitted
                    }
                    cursor
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                }
            }
        }
        """

        result = self.execute_query(client, query)

        # Verify the connection structure
        assert "edges" in result["moneyPlans"]
        assert "pageInfo" in result["moneyPlans"]

        # Verify we have both plans
        edges = result["moneyPlans"]["edges"]
        assert len(edges) == 2

        # Plans should be ordered by notification position (most recent first)
        assert edges[0]["node"]["initialBalance"] == 2000.0
        assert edges[0]["node"]["notes"] == "Plan 2"
        assert edges[0]["node"]["isCommitted"] is True
        assert edges[1]["node"]["initialBalance"] == 1000.0
        assert edges[1]["node"]["notes"] == "Plan 1"
        assert edges[1]["node"]["isCommitted"] is True

        # Each edge should have a cursor
        assert edges[0]["cursor"] is not None
        assert edges[1]["cursor"] is not None

        # Test forward pagination
        query_with_first = """
        query GetMoneyPlans($first: Int, $after: String) {
            moneyPlans(first: $first, after: $after) {
                edges {
                    node {
                        id
                        initialBalance
                        notes
                        isCommitted
                    }
                    cursor
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                }
            }
        }
        """

        # Get only the first plan
        result = self.execute_query(client, query_with_first, {"first": 1})
        edges = result["moneyPlans"]["edges"]
        page_info = result["moneyPlans"]["pageInfo"]

        assert len(edges) == 1
        assert edges[0]["node"]["initialBalance"] == 2000.0
        assert edges[0]["node"]["notes"] == "Plan 2"
        assert edges[0]["node"]["isCommitted"] is True
        assert page_info["hasNextPage"] is True
        assert page_info["hasPreviousPage"] is False

        # Get the next plan using the cursor
        first_cursor = edges[0]["cursor"]
        result = self.execute_query(client, query_with_first, {"first": 1, "after": first_cursor})
        edges = result["moneyPlans"]["edges"]
        page_info = result["moneyPlans"]["pageInfo"]

        assert len(edges) == 1
        assert edges[0]["node"]["initialBalance"] == 1000.0
        assert edges[0]["node"]["notes"] == "Plan 1"
        assert edges[0]["node"]["isCommitted"] is True
        assert page_info["hasNextPage"] is False
        assert page_info["hasPreviousPage"] is True

    def test_cannot_create_multiple_uncommitted_plans(self, client, money_planner):
        """Test that we cannot create multiple uncommitted plans."""
        # Create first plan
        create_mutation = """
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
                        remainingBalance
                    }
                }
            }
        }
        """

        # Create first plan
        result1 = self.execute_query(
            client,
            create_mutation,
            {"input": {"initialBalance": 1000.0, "notes": "First plan"}},
        )
        assert "errors" not in result1
        assert result1["moneyPlan"]["startPlan"]["success"]

        # Try to create second plan without committing first one
        result2 = self.execute_query(
            client,
            create_mutation,
            {"input": {"initialBalance": 2000.0, "notes": "Second plan"}},
        )
        assert "errors" not in result2
        assert not result2["moneyPlan"]["startPlan"]["success"]
        assert "uncommitted plan" in result2["moneyPlan"]["startPlan"]["error"]["message"].lower()

        # Commit first plan
        commit_mutation = """
        mutation CommitPlan($input: CommitPlanInput!) {
            moneyPlan {
                commitPlan(input: $input) {
                    success
                }
            }
        }
        """

        # Add account with full balance to satisfy commit invariants
        plan1_id = result1["moneyPlan"]["startPlan"]["moneyPlan"]["id"]
        self.add_account_with_full_balance(client, plan1_id, 1000.0, "Account 1")

        # Now commit the plan
        commit_result = self.execute_query(
            client,
            commit_mutation,
            {"input": {"planId": plan1_id}},
        )
        assert commit_result["moneyPlan"]["commitPlan"]["success"]

        # Now we should be able to create another plan
        result3 = self.execute_query(
            client,
            create_mutation,
            {"input": {"initialBalance": 2000.0, "notes": "Second plan after commit"}},
        )
        assert "errors" not in result3
        assert result3["moneyPlan"]["startPlan"]["success"]

    def test_money_plans_with_archived(self, client, money_planner):
        """Test that archived plans are filtered out by default but can be included."""
        # Create and commit two plans
        plan1_id = self.create_money_plan(client, 1000.0, "Plan 1")
        self.add_account_with_full_balance(client, plan1_id, 1000.0, "Account 1")
        assert self.commit_plan(client, plan1_id)

        plan2_id = self.create_money_plan(client, 2000.0, "Plan 2")
        self.add_account_with_full_balance(client, plan2_id, 2000.0, "Account 2")
        assert self.commit_plan(client, plan2_id)

        # Archive plan 1
        archive_mutation = """
        mutation ArchivePlan($input: ArchivePlanInput!) {
            moneyPlan {
                archivePlan(input: $input) {
                    success
                }
            }
        }
        """
        archive_result = self.execute_query(client, archive_mutation, {"input": {"planId": plan1_id}})
        assert archive_result["moneyPlan"]["archivePlan"]["success"]

        # Query plans - should only get plan 2 by default
        query = """
        query GetMoneyPlans($filter: MoneyPlanFilter) {
            moneyPlans(filter: $filter) {
                edges {
                    node {
                        id
                        initialBalance
                        notes
                        isCommitted
                        isArchived
                    }
                }
            }
        }
        """

        # Without any filter (defaults to not including archived)
        result = self.execute_query(client, query)
        edges = result["moneyPlans"]["edges"]
        assert len(edges) == 1
        assert edges[0]["node"]["initialBalance"] == 2000.0
        assert edges[0]["node"]["notes"] == "Plan 2"
        assert not edges[0]["node"]["isArchived"]

        # With is_archived = true - should only return archived plans
        result = self.execute_query(client, query, {"filter": {"isArchived": True}})
        edges = result["moneyPlans"]["edges"]
        assert len(edges) == 1  # Only plan 1 is archived
        assert edges[0]["node"]["initialBalance"] == 1000.0
        assert edges[0]["node"]["isArchived"]  # Plan 1 is archived

    def test_money_plans_with_filters(self, client, money_planner):
        """Test filtering money plans by status and archived state."""
        # Create and commit two plans
        plan1_id = self.create_money_plan(client, 1000.0, "Plan 1")
        self.add_account_with_full_balance(client, plan1_id, 1000.0, "Account 1")
        assert self.commit_plan(client, plan1_id)

        plan2_id = self.create_money_plan(client, 2000.0, "Plan 2")
        self.add_account_with_full_balance(client, plan2_id, 2000.0, "Account 2")
        # Query to test draft filter before committing plan 2
        query = """
        query GetMoneyPlans($filter: MoneyPlanFilter) {
            moneyPlans(filter: $filter) {
                edges {
                    node {
                        id
                        initialBalance
                        notes
                        isCommitted
                        isArchived
                    }
                }
            }
        }
        """

        # Test status=draft filter
        result = self.execute_query(client, query, {"filter": {"status": "draft"}})
        edges = result["moneyPlans"]["edges"]
        assert len(edges) == 1
        assert edges[0]["node"]["initialBalance"] == 2000.0
        assert edges[0]["node"]["notes"] == "Plan 2"
        assert not edges[0]["node"]["isCommitted"]

        # Now commit plan 2 before creating plan 3
        assert self.commit_plan(client, plan2_id)

        # Create a third plan and commit it
        plan3_id = self.create_money_plan(client, 3000.0, "Plan 3")
        self.add_account_with_full_balance(client, plan3_id, 3000.0, "Account 3")
        assert self.commit_plan(client, plan3_id)

        # Archive plan 3
        archive_mutation = """
        mutation ArchivePlan($input: ArchivePlanInput!) {
            moneyPlan {
                archivePlan(input: $input) {
                    success
                }
            }
        }
        """
        archive_result = self.execute_query(client, archive_mutation, {"input": {"planId": plan3_id}})
        assert archive_result["moneyPlan"]["archivePlan"]["success"]

        # Test status=committed filter
        result = self.execute_query(client, query, {"filter": {"status": "committed"}})
        edges = result["moneyPlans"]["edges"]
        assert len(edges) == 2  # Plans 1 and 2 (Plan 3 is archived)
        assert edges[0]["node"]["initialBalance"] == 2000.0  # Most recent first
        assert edges[1]["node"]["initialBalance"] == 1000.0
        assert all(edge["node"]["isCommitted"] for edge in edges)

        # Test is_archived=true (should only return archived plan 3)
        result = self.execute_query(client, query, {"filter": {"isArchived": True}})
        edges = result["moneyPlans"]["edges"]
        assert len(edges) == 1  # Only plan 3 is archived
        assert edges[0]["node"]["initialBalance"] == 3000.0  # Plan 3
        assert edges[0]["node"]["isArchived"]  # Plan 3 is archived

        # Test both filters together - should return only archived AND committed plans
        result = self.execute_query(client, query, {"filter": {"status": "committed", "isArchived": True}})
        edges = result["moneyPlans"]["edges"]
        assert len(edges) == 1  # Only plan 3 is both archived and committed
        assert edges[0]["node"]["initialBalance"] == 3000.0  # Most recent first
        assert edges[0]["node"]["isArchived"]
        assert edges[0]["node"]["isCommitted"]

    def test_can_create_plan_after_archiving_uncommitted(self, client, money_planner):
        """Test that we can create a new plan after archiving an uncommitted one."""
        # Create first plan (will be uncommitted)
        plan1_id = self.create_money_plan(client, 1000.0, "Plan 1")

        # Archive the uncommitted plan
        archive_mutation = """
        mutation ArchivePlan($input: ArchivePlanInput!) {
            moneyPlan {
                archivePlan(input: $input) {
                    success
                    error {
                        message
                    }
                }
            }
        }
        """
        archive_result = self.execute_query(client, archive_mutation, {"input": {"planId": plan1_id}})
        assert archive_result["moneyPlan"]["archivePlan"]["success"]

        # Try to create a new plan - should succeed now
        create_mutation = """
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
                        remainingBalance
                        isArchived
                        isCommitted
                    }
                }
            }
        }
        """
        result = self.execute_query(
            client,
            create_mutation,
            {"input": {"initialBalance": 2000.0, "notes": "Plan 2"}},
        )
        assert "errors" not in result
        assert result["moneyPlan"]["startPlan"]["success"]
        assert result["moneyPlan"]["startPlan"]["moneyPlan"]["initialBalance"] == 2000.0
        assert not result["moneyPlan"]["startPlan"]["moneyPlan"]["isArchived"]
        assert not result["moneyPlan"]["startPlan"]["moneyPlan"]["isCommitted"]

    def test_start_plan_with_copied_structure(self, client, money_planner):
        """Test starting a plan with structure copied from a specific plan."""
        # Create first plan with accounts and buckets
        plan1_id = self.create_money_plan(client, 1000.0, "Plan 1")

        # Add an account with specific buckets
        add_account_mutation = """
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
        """

        # Add first account with two buckets
        account_variables = {
            "input": {
                "planId": plan1_id,
                "name": "Checking Account",
                "buckets": [
                    {"bucketName": "Bills", "category": "expenses", "allocatedAmount": 600.0},
                    {"bucketName": "Food", "category": "expenses", "allocatedAmount": 200.0},
                ],
            }
        }
        result = self.execute_query(client, add_account_mutation, account_variables)
        assert result["moneyPlan"]["addAccount"]["success"]

        # Add second account with one bucket
        account_variables = {
            "input": {
                "planId": plan1_id,
                "name": "Savings Account",
                "buckets": [
                    {"bucketName": "Emergency Fund", "category": "savings", "allocatedAmount": 200.0},
                ],
            }
        }
        result = self.execute_query(client, add_account_mutation, account_variables)
        assert result["moneyPlan"]["addAccount"]["success"]

        # Commit the plan
        assert self.commit_plan(client, plan1_id)

        # Now create a second plan with copied structure
        create_plan_mutation = """
        mutation StartPlan($input: PlanStartInput!) {
            moneyPlan {
                startPlan(input: $input) {
                    success
                    error {
                        message
                    }
                    moneyPlan {
                        id
                        initialBalance
                        remainingBalance
                        accounts {
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
        """

        # Create new plan with the copy_from parameter set to the first plan's ID
        variables = {
            "input": {"initialBalance": 2000.0, "notes": "Plan with copied structure", "copyFrom": plan1_id}
        }

        result = self.execute_query(client, create_plan_mutation, variables)
        assert "errors" not in result
        assert result["moneyPlan"]["startPlan"]["success"]

        # Verify the new plan has the same account structure but with zero allocations
        new_plan = result["moneyPlan"]["startPlan"]["moneyPlan"]
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
        buckets = {b["bucketName"]: b for b in checking["buckets"]}
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
        assert savings["buckets"][0]["bucketName"] == "Emergency Fund"
        assert savings["buckets"][0]["category"] == "savings"
        assert savings["buckets"][0]["allocatedAmount"] == 0.0  # Zero allocation

    def test_create_plan_with_future_date(self, client, money_planner):
        """Test creating a plan with a future date."""
        future_date = (date.today() + timedelta(days=30)).isoformat()

        mutation = """
        mutation StartPlan($input: PlanStartInput!) {
            moneyPlan {
                startPlan(input: $input) {
                    success
                    moneyPlan {
                        id
                        planDate
                        createdAt
                    }
                }
            }
        }
        """
        variables = {"input": {"initialBalance": 1000.0, "notes": "Future plan", "planDate": future_date}}

        result = self.execute_query(client, mutation, variables)
        assert "errors" not in result
        assert result["moneyPlan"]["startPlan"]["success"]
        assert result["moneyPlan"]["startPlan"]["moneyPlan"]["planDate"] == future_date
        assert result["moneyPlan"]["startPlan"]["moneyPlan"]["createdAt"] is not None
