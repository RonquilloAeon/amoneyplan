from uuid import uuid4

import pytest
from strawberry.relay import to_base64
from utils import TestGraphQLAPI


@pytest.mark.django_db(transaction=True)
class TestNotesSchema(TestGraphQLAPI):
    def test_edit_plan_notes(self, client, money_planner):
        """Test editing the notes of a plan."""
        # Create a plan
        plan_id = self.create_money_plan(client, 1000.0, "Initial notes")

        # Edit the plan notes
        result = self.execute_query(
            client,
            """
            mutation EditPlanNotes($input: EditPlanNotesInput!) {
                moneyPlan {
                    editPlanNotes(input: $input) {
                        error {
                            message
                        }
                        success
                        moneyPlan {
                            id
                            notes
                        }
                    }
                }
            }
            """,
            {"input": {"planId": plan_id, "notes": "Updated notes"}},
        )

        # Check the result
        assert "errors" not in result
        assert result["moneyPlan"]["editPlanNotes"]["success"]
        assert result["moneyPlan"]["editPlanNotes"]["moneyPlan"]["notes"] == "Updated notes"

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
            {"planId": plan_id},
        )
        assert result["moneyPlan"]["notes"] == "Updated notes"

    def test_edit_account_notes(self, client, money_planner):
        """Test editing the notes of an account."""
        # Create a plan with an account
        plan_id = self.create_money_plan(client, 1000.0, "Plan 1")
        account_id = self.add_account_with_full_balance(client, plan_id, 1000.0, "Account 1")

        # Edit the account notes
        result = self.execute_query(
            client,
            """
            mutation EditAccountNotes($input: EditAccountNotesInput!) {
                moneyPlan {
                    editAccountNotes(input: $input) {
                        error {
                            message
                        }
                        success
                        moneyPlan {
                            id
                            accounts {
                                id
                                name
                                notes
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
                    "notes": "Account notes",
                }
            },
        )

        # Check the result
        assert "errors" not in result
        assert result["moneyPlan"]["editAccountNotes"]["success"]

        # Find the account in the result and check its notes
        account = next(
            (
                a
                for a in result["moneyPlan"]["editAccountNotes"]["moneyPlan"]["accounts"]
                if a["id"] == account_id
            ),
            None,
        )
        assert account is not None
        assert account["notes"] == "Account notes"

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
            {"planId": plan_id},
        )
        assert result["moneyPlan"]["accounts"][0]["notes"] == "Account notes"

    def test_edit_plan_notes_archived_plan(self, client, money_planner):
        """Test that editing notes of an archived plan fails."""
        # Create a plan and archive it
        plan_id = self.create_money_plan(client, 1000.0, "Plan 1")

        archive_mutation = """
        mutation ArchivePlan($input: ArchivePlanInput!) {
            moneyPlan {
                archivePlan(input: $input) {
                    success
                }
            }
        }
        """
        archive_result = self.execute_query(client, archive_mutation, {"input": {"planId": plan_id}})
        assert archive_result["moneyPlan"]["archivePlan"]["success"]

        # Try to edit the plan notes
        result = self.execute_query(
            client,
            """
            mutation EditPlanNotes($input: EditPlanNotesInput!) {
                moneyPlan {
                    editPlanNotes(input: $input) {
                        error {
                            message
                        }
                        success
                    }
                }
            }
            """,
            {"input": {"planId": plan_id, "notes": "New notes"}},
        )

        # Check the result
        assert "errors" not in result
        assert not result["moneyPlan"]["editPlanNotes"]["success"]
        assert "Cannot modify an archived plan" in result["moneyPlan"]["editPlanNotes"]["error"]["message"]

    def test_edit_account_notes_archived_plan(self, client, money_planner):
        """Test that editing account notes of an archived plan fails."""
        # Create a plan with an account and archive it
        plan_id = self.create_money_plan(client, 1000.0, "Plan 1")
        account_id = self.add_account_with_full_balance(client, plan_id, 1000.0, "Account 1")

        archive_mutation = """
        mutation ArchivePlan($input: ArchivePlanInput!) {
            moneyPlan {
                archivePlan(input: $input) {
                    success
                }
            }
        }
        """
        archive_result = self.execute_query(client, archive_mutation, {"input": {"planId": plan_id}})
        assert archive_result["moneyPlan"]["archivePlan"]["success"]

        # Try to edit the account notes
        result = self.execute_query(
            client,
            """
            mutation EditAccountNotes($input: EditAccountNotesInput!) {
                moneyPlan {
                    editAccountNotes(input: $input) {
                        error {
                            message
                        }
                        success
                    }
                }
            }
            """,
            {
                "input": {
                    "planId": plan_id,
                    "accountId": account_id,
                    "notes": "Account notes",
                }
            },
        )

        # Check the result
        assert "errors" not in result
        assert not result["moneyPlan"]["editAccountNotes"]["success"]
        assert "Cannot modify an archived plan" in result["moneyPlan"]["editAccountNotes"]["error"]["message"]

    def test_edit_nonexistent_account_notes(self, client, money_planner):
        """Test that editing notes of a non-existent account fails."""
        # Create a plan
        plan_id = self.create_money_plan(client, 1000.0, "Test Plan")

        # Try to edit the notes of a non-existent account
        nonexistent_account_id = uuid4()

        result = self.execute_query(
            client,
            """
            mutation EditAccountNotes($input: EditAccountNotesInput!) {
                moneyPlan {
                    editAccountNotes(input: $input) {
                        error {
                            message
                        }
                        success
                    }
                }
            }
            """,
            {
                "input": {
                    "planId": plan_id,
                    "accountId": to_base64("Account", nonexistent_account_id),
                    "notes": "Account notes",
                }
            },
        )

        # Check the result
        assert "errors" not in result
        assert not result["moneyPlan"]["editAccountNotes"]["success"]
        assert (
            f"Account with ID {nonexistent_account_id}"
            in result["moneyPlan"]["editAccountNotes"]["error"]["message"]
        )
