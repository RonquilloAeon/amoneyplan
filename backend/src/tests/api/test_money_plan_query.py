import pytest

from .utils import TestGraphQLAPI


@pytest.mark.django_db(transaction=True)
class TestMoneyPlan(TestGraphQLAPI):
    def test_money_plan_query(self, client):
        """Test querying a money plan."""
        # Get a test user
        user = self.get_test_user(client)

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

        # Add an account with a bucket to satisfy invariants
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
                "buckets": [{"bucketName": "Default", "category": "default", "allocatedAmount": 1000.0}],
            }
        }

        result = self.execute_query(client, add_account_mutation, user=user, variables=account_variables)
        assert "data" in result["moneyPlan"]["addAccount"]

        # Now query the created plan
        result = self.execute_query(client, query, user=user, variables={"planId": plan_id})
        assert "errors" not in result
        assert result["moneyPlan"]["initialBalance"] == 1000.0
        assert result["moneyPlan"]["isCommitted"] is False
        assert len(result["moneyPlan"]["accounts"]) == 1
        assert result["moneyPlan"]["accounts"][0]["name"] == "Test Account"

    def test_money_plans_query(self, client, money_planner):
        """Test querying all money plans with pagination."""
        user = self.get_test_user(client)

        # Create and commit first plan
        result = self.execute_query(
            client,
            """
            mutation StartPlan($input: PlanStartInput!) {
                moneyPlan {
                    startPlan(input: $input) {
                        ... on Success {
                            data
                            message
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
            variables={"input": {"initialBalance": 1000.0, "notes": "Plan 1"}},
        )
        assert "errors" not in result
        plan1_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Add account with full balance to first plan
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
                    "planId": plan1_id,
                    "name": "Account 1",
                    "buckets": [{"bucketName": "Default", "category": "default", "allocatedAmount": 1000.0}],
                }
            },
        )
        assert "errors" not in result

        # Commit first plan
        commit_result = self.execute_query(
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
            variables={"input": {"planId": plan1_id}},
        )
        assert "errors" not in commit_result
        assert "data" in commit_result["moneyPlan"]["commitPlan"]

        # Create and commit second plan
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
            variables={"input": {"initialBalance": 2000.0, "notes": "Plan 2"}},
        )
        assert "errors" not in result
        plan2_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Add account with full balance to second plan
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
                    "planId": plan2_id,
                    "name": "Account 2",
                    "buckets": [{"bucketName": "Default", "category": "default", "allocatedAmount": 2000.0}],
                }
            },
        )
        assert "errors" not in result

        # Commit second plan
        commit_result = self.execute_query(
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
            variables={"input": {"planId": plan2_id}},
        )
        assert "errors" not in commit_result
        assert "data" in commit_result["moneyPlan"]["commitPlan"]

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
        result = self.execute_query(client, query, user=user)

        # Verify the connection structure
        assert "edges" in result["moneyPlans"]
        assert "pageInfo" in result["moneyPlans"]

        # Verify we have both plans
        edges = result["moneyPlans"]["edges"]
        assert len(edges) == 2

        # Find plans by their initial balance (since order might not be guaranteed)
        plans = {edge["node"]["initialBalance"]: edge["node"] for edge in edges}

        # Verify plan details
        assert 1000.0 in plans
        assert 2000.0 in plans
        assert plans[1000.0]["notes"] == "Plan 1"
        assert plans[1000.0]["isCommitted"] is True
        assert plans[2000.0]["notes"] == "Plan 2"
        assert plans[2000.0]["isCommitted"] is True

        # Each edge should have a cursor
        assert all(edge["cursor"] is not None for edge in edges)

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
        result = self.execute_query(client, query_with_first, user=user, variables={"first": 1})
        edges = result["moneyPlans"]["edges"]
        page_info = result["moneyPlans"]["pageInfo"]
        assert len(edges) == 1

        # There should be a next page since we have 2 plans total
        assert page_info["hasNextPage"] is True
        assert page_info["hasPreviousPage"] is False

        # Get the next plan using the cursor
        first_cursor = edges[0]["cursor"]
        result = self.execute_query(
            client, query_with_first, user=user, variables={"first": 1, "after": first_cursor}
        )
        edges = result["moneyPlans"]["edges"]
        page_info = result["moneyPlans"]["pageInfo"]
        assert len(edges) == 1

        # We should have reached the end now
        assert page_info["hasNextPage"] is False
        assert page_info["hasPreviousPage"] is True

    def test_money_plans_with_filters(self, client, money_planner):
        """Test filtering money plans by status and archived state."""
        user = self.get_test_user(client)

        # Create first plan
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

        # Add account with full balance
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
                    "name": "Account 1",
                    "buckets": [{"bucketName": "Default", "category": "default", "allocatedAmount": 1000.0}],
                }
            },
        )
        assert "errors" not in result

        # Commit plan 1
        commit_result = self.execute_query(
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
        assert "errors" not in commit_result
        assert "data" in commit_result["moneyPlan"]["commitPlan"]

        # Create second plan but don't commit it yet
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
            variables={"input": {"initialBalance": 2000.0, "notes": "Plan 2"}},
        )
        assert "errors" not in result
        plan2_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Add account with full balance
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
                    "planId": plan2_id,
                    "name": "Account 2",
                    "buckets": [{"bucketName": "Default", "category": "default", "allocatedAmount": 2000.0}],
                }
            },
        )
        assert "errors" not in result

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
        result = self.execute_query(client, query, user=user, variables={"filter": {"status": "draft"}})
        edges = result["moneyPlans"]["edges"]
        assert len(edges) == 1
        assert edges[0]["node"]["initialBalance"] == 2000.0
        assert edges[0]["node"]["notes"] == "Plan 2"
        assert not edges[0]["node"]["isCommitted"]

        # Now commit plan 2
        commit_result = self.execute_query(
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
            variables={"input": {"planId": plan2_id}},
        )
        assert "errors" not in commit_result
        assert "data" in commit_result["moneyPlan"]["commitPlan"]

        # Create a third plan and commit it
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
            variables={"input": {"initialBalance": 3000.0, "notes": "Plan 3"}},
        )
        assert "errors" not in result
        plan3_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Add account with full balance
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
                    "planId": plan3_id,
                    "name": "Account 3",
                    "buckets": [{"bucketName": "Default", "category": "default", "allocatedAmount": 3000.0}],
                }
            },
        )
        assert "errors" not in result

        # Commit plan 3
        commit_result = self.execute_query(
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
            variables={"input": {"planId": plan3_id}},
        )
        assert "errors" not in commit_result
        assert "data" in commit_result["moneyPlan"]["commitPlan"]

        # Archive plan 3
        archive_mutation = """
        mutation ArchivePlan($input: ArchivePlanInput!) {
            moneyPlan {
                archivePlan(input: $input) {
                    ...on Success {
                        data
                        message
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
        archive_result = self.execute_query(
            client, archive_mutation, user=user, variables={"input": {"planId": plan3_id}}
        )
        assert "errors" not in archive_result
        assert "data" in archive_result["moneyPlan"]["archivePlan"]

        # Test status=committed filter
        result = self.execute_query(client, query, user=user, variables={"filter": {"status": "committed"}})
        edges = result["moneyPlans"]["edges"]
        assert len(edges) == 2  # Plans 1 and 2 (Plan 3 is archived)
        assert edges[0]["node"]["initialBalance"] == 2000.0  # Most recent first
        assert edges[1]["node"]["initialBalance"] == 1000.0
        assert all(edge["node"]["isCommitted"] for edge in edges)

        # Test is_archived=true (should only return archived plan 3)
        result = self.execute_query(client, query, user=user, variables={"filter": {"isArchived": True}})
        edges = result["moneyPlans"]["edges"]
        assert len(edges) == 1  # Only plan 3 is archived
        assert edges[0]["node"]["initialBalance"] == 3000.0  # Plan 3
        assert edges[0]["node"]["isArchived"]  # Plan 3 is archived

        # Test both filters together - should return only archived AND committed plans
        result = self.execute_query(
            client, query, user=user, variables={"filter": {"status": "committed", "isArchived": True}}
        )
        edges = result["moneyPlans"]["edges"]
        assert len(edges) == 1  # Only plan 3 is both archived and committed
        assert edges[0]["node"]["initialBalance"] == 3000.0  # Plan 3
        assert edges[0]["node"]["isArchived"]
        assert edges[0]["node"]["isCommitted"]
