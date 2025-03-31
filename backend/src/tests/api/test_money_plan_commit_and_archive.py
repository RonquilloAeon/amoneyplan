import pytest

from .utils import TestGraphQLAPI


@pytest.mark.django_db(transaction=True)
class TestMoneyPlan(TestGraphQLAPI):
    def test_create_and_commit_plan(self, client, money_planner):
        """Test creating a plan, adding accounts/buckets, and committing it."""
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
        variables = {"input": {"initialBalance": 1000.0, "notes": "Test plan with accounts"}}

        result = self.execute_query(client, create_plan_mutation, user=user, variables=variables)
        assert "errors" not in result
        plan_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Add an account with buckets that sum to initial balance
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
        assert "errors" not in result
        assert "data" in result["moneyPlan"]["addAccount"]

        # Commit the plan
        commit_plan_mutation = """
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
        result = self.execute_query(client, commit_plan_mutation, user=user, variables=commit_variables)
        assert "errors" not in result
        assert "data" in result["moneyPlan"]["commitPlan"]

    def test_money_plans_with_archived(self, client, money_planner):
        """Test that archived plans are filtered out by default but can be included."""
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

        # Add account with full balance
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

        # Add account with full balance
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

        # Archive plan 1
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
            client, archive_mutation, user=user, variables={"input": {"planId": plan1_id}}
        )
        assert "data" in archive_result["moneyPlan"]["archivePlan"]

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
        result = self.execute_query(client, query, user=user)
        edges = result["moneyPlans"]["edges"]
        assert len(edges) == 1
        assert edges[0]["node"]["initialBalance"] == 2000.0
        assert edges[0]["node"]["notes"] == "Plan 2"
        assert not edges[0]["node"]["isArchived"]

        # With is_archived = true - should only return archived plans
        result = self.execute_query(client, query, user=user, variables={"filter": {"isArchived": True}})
        edges = result["moneyPlans"]["edges"]
        assert len(edges) == 1  # Only plan 1 is archived
        assert edges[0]["node"]["initialBalance"] == 1000.0
        assert edges[0]["node"]["isArchived"]  # Plan 1 is archived

    def test_can_create_plan_after_archiving_uncommitted(self, client, money_planner):
        """Test that we can create a new plan after archiving an uncommitted one."""
        user = self.get_test_user(client)

        # Create first plan (will be uncommitted)
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

        # Archive the uncommitted plan
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
            client, archive_mutation, user=user, variables={"input": {"planId": plan1_id}}
        )
        assert "errors" not in archive_result
        assert "data" in archive_result["moneyPlan"]["archivePlan"]

        # Try to create a new plan - should succeed now
        create_mutation = """
        mutation StartPlan($input: PlanStartInput!) {
            moneyPlan {
                startPlan(input: $input) {
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
        result = self.execute_query(
            client,
            create_mutation,
            user=user,
            variables={"input": {"initialBalance": 2000.0, "notes": "Plan 2"}},
        )
        assert "errors" not in result
        assert "data" in result["moneyPlan"]["startPlan"]

        # Get the plan to verify its properties
        plan2_id = result["moneyPlan"]["startPlan"]["data"]["id"]
        query = """
        query GetMoneyPlan($planId: GlobalID!) {
            moneyPlan(planId: $planId) {
                id
                initialBalance
                remainingBalance
                isArchived
                isCommitted
            }
        }
        """
        plan_result = self.execute_query(client, query, user=user, variables={"planId": plan2_id})
        assert plan_result["moneyPlan"]["initialBalance"] == 2000.0
        assert not plan_result["moneyPlan"]["isArchived"]
        assert not plan_result["moneyPlan"]["isCommitted"]
