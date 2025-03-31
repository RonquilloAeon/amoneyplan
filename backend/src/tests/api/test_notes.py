from uuid import uuid4

import pytest
from strawberry.relay import to_base64

from .utils import TestGraphQLAPI


@pytest.mark.django_db(transaction=True)
class TestNotesSchema(TestGraphQLAPI):
    def test_edit_plan_notes(self, client, money_planner):
        """Test editing the notes of a plan."""
        user = self.get_test_user(client)

        # Create a plan
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
            variables={"input": {"initialBalance": 1000.0, "notes": "Original notes"}},
        )
        assert "errors" not in result
        plan_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Edit the plan notes
        result = self.execute_query(
            client,
            """
            mutation EditPlanNotes($input: EditPlanNotesInput!) {
                moneyPlan {
                    editPlanNotes(input: $input) {
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
            variables={"input": {"planId": plan_id, "notes": "Updated notes"}},
        )

        # Check the result
        assert "errors" not in result
        assert "data" in result["moneyPlan"]["editPlanNotes"]

        # Verify that the plan notes were updated in the domain model
        result = self.execute_query(
            client,
            """
            query GetMoneyPlan($planId: GlobalID!) {
                moneyPlan(planId: $planId) {
                    notes
                }
            }
            """,
            user=user,
            variables={"planId": plan_id},
        )
        assert "errors" not in result
        assert result["moneyPlan"]["notes"] == "Updated notes"

    def test_edit_account_notes(self, client, money_planner):
        """Test editing the notes of an account."""
        user = self.get_test_user(client)

        # Create a plan with an account
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
                    "name": "Account 1",
                    "buckets": [{"bucketName": "Default", "category": "default", "allocatedAmount": 1000.0}],
                }
            },
        )
        assert "errors" not in result
        account_id = result["moneyPlan"]["addAccount"]["data"]["id"]

        # Edit the account notes
        result = self.execute_query(
            client,
            """
            mutation EditAccountNotes($input: EditAccountNotesInput!) {
                moneyPlan {
                    editAccountNotes(input: $input) {
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
                    "notes": "Account notes",
                }
            },
        )

        # Check the result
        assert "errors" not in result
        assert "data" in result["moneyPlan"]["editAccountNotes"]

        # Verify that the account notes were saved
        result = self.execute_query(
            client,
            """
            query GetMoneyPlan($planId: GlobalID!) {
                moneyPlan(planId: $planId) {
                    accounts {
                        id
                        notes
                    }
                }
            }
            """,
            user=user,
            variables={"planId": plan_id},
        )

        # Find the account in the result and check its notes
        account = next(
            (a for a in result["moneyPlan"]["accounts"] if a["id"] == account_id),
            None,
        )
        assert account is not None
        assert account["notes"] == "Account notes"

    def test_edit_plan_notes_archived_plan(self, client, money_planner):
        """Test that editing notes of an archived plan fails."""
        user = self.get_test_user(client)

        # Create a plan and archive it
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
        plan_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Archive the plan
        archive_mutation = """
        mutation ArchivePlan($input: ArchivePlanInput!) {
            moneyPlan {
                archivePlan(input: $input) {
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
        archive_result = self.execute_query(
            client, archive_mutation, user=user, variables={"input": {"planId": plan_id}}
        )
        assert "data" in archive_result["moneyPlan"]["archivePlan"]

        # Try to edit the plan notes
        result = self.execute_query(
            client,
            """
            mutation EditPlanNotes($input: EditPlanNotesInput!) {
                moneyPlan {
                    editPlanNotes(input: $input) {
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
            variables={"input": {"planId": plan_id, "notes": "New notes"}},
        )

        # Check the result
        assert "errors" not in result
        assert "message" in result["moneyPlan"]["editPlanNotes"]
        assert "Cannot modify an archived plan" in result["moneyPlan"]["editPlanNotes"]["message"]

    def test_edit_account_notes_archived_plan(self, client, money_planner):
        """Test that editing account notes of an archived plan fails."""
        user = self.get_test_user(client)

        # Create a plan with an account
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
        plan_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Add account
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
                    "name": "Account 1",
                    "buckets": [{"bucketName": "Default", "category": "default", "allocatedAmount": 1000.0}],
                }
            },
        )
        assert "errors" not in result
        account_id = result["moneyPlan"]["addAccount"]["data"]["id"]

        # Archive the plan
        archive_mutation = """
        mutation ArchivePlan($input: ArchivePlanInput!) {
            moneyPlan {
                archivePlan(input: $input) {
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
        archive_result = self.execute_query(
            client, archive_mutation, user=user, variables={"input": {"planId": plan_id}}
        )
        assert "data" in archive_result["moneyPlan"]["archivePlan"]

        # Try to edit the account notes
        result = self.execute_query(
            client,
            """
            mutation EditAccountNotes($input: EditAccountNotesInput!) {
                moneyPlan {
                    editAccountNotes(input: $input) {
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
                    "planId": plan_id,
                    "accountId": account_id,
                    "notes": "Account notes",
                }
            },
        )

        # Check the result
        assert "errors" not in result
        assert "message" in result["moneyPlan"]["editAccountNotes"]
        assert "Cannot modify an archived plan" in result["moneyPlan"]["editAccountNotes"]["message"]

    def test_edit_nonexistent_account_notes(self, client, money_planner):
        """Test that editing notes of a non-existent account fails."""
        user = self.get_test_user(client)

        # Create a plan
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

        # Try to edit the notes of a non-existent account
        nonexistent_account_id = str(uuid4())
        relay_account_id = to_base64("Account", nonexistent_account_id)

        result = self.execute_query(
            client,
            """
            mutation EditAccountNotes($input: EditAccountNotesInput!) {
                moneyPlan {
                    editAccountNotes(input: $input) {
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
                    "accountId": relay_account_id,
                    "notes": "Account notes",
                }
            },
        )

        # Check the result
        assert "errors" not in result
        assert "message" in result["moneyPlan"]["editAccountNotes"]
        assert "Account with ID" in result["moneyPlan"]["editAccountNotes"]["message"]
