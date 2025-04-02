import pytest
from django.test import Client

from .utils import TestGraphQLAPI


@pytest.mark.django_db(transaction=True)
class TestAuthenticationAndAuthorization(TestGraphQLAPI):
    def test_unauthenticated_user_cannot_fetch_money_plans(self, client: Client):
        """Test that unauthenticated users cannot fetch money plans."""
        # Query for money plans without authentication
        query = """
        query GetMoneyPlans {
            moneyPlans {
                edges {
                    node {
                        id
                        initialBalance
                    }
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                }
            }
        }
        """
        result = self.execute_query(client, query, user=None)

        # Verify empty results for unauthenticated user
        assert "moneyPlans" in result
        assert len(result["moneyPlans"]["edges"]) == 0

    def test_unauthenticated_user_cannot_fetch_specific_money_plan(self, client: Client):
        """Test that unauthenticated users cannot fetch a specific money plan."""
        # First create a user and a plan
        user = self.get_test_user(client)

        # Create a plan as an authenticated user
        create_plan_mutation = """
        mutation StartPlan($input: PlanStartInput!) {
            moneyPlan {
                startPlan(input: $input) {
                    ... on Success {
                        data
                    }
                }
            }
        }
        """
        variables = {"input": {"initialBalance": 1000.0, "notes": "Test plan"}}
        result = self.execute_query(client, create_plan_mutation, user=user, variables=variables)
        plan_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Now try to fetch that plan without authentication
        query = """
        query GetMoneyPlan($planId: GlobalID!) {
            moneyPlan(planId: $planId) {
                id
                initialBalance
                accounts {
                    id
                    name
                }
            }
        }
        """
        result = self.execute_query(client, query, user=None, variables={"planId": plan_id})

        # Should return null for the moneyPlan field when unauthenticated
        assert result["moneyPlan"] is None

    def test_unauthenticated_user_cannot_create_plan(self, client: Client):
        """Test that unauthenticated users cannot create a money plan."""
        # Try to create a plan without authentication
        create_plan_mutation = """
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
        """
        variables = {"input": {"initialBalance": 1000.0, "notes": "Test plan without auth"}}
        result = self.execute_query(client, create_plan_mutation, user=None, variables=variables)

        assert result is None

    def test_user_cannot_see_another_users_money_plans(self, client: Client):
        """Test that one user cannot see another user's money plans."""
        # Create first user and their plan
        user1 = self.get_test_user(client, email="user1@example.com")

        # Create a plan for user1
        create_plan_mutation = """
        mutation StartPlan($input: PlanStartInput!) {
            moneyPlan {
                startPlan(input: $input) {
                    ... on Success {
                        data
                    }
                }
            }
        }
        """
        variables = {"input": {"initialBalance": 1000.0, "notes": "User 1's plan"}}
        result = self.execute_query(client, create_plan_mutation, user=user1, variables=variables)
        plan_id_user1 = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Add an account to this plan
        add_account_mutation = """
        mutation AddAccount($input: AddAccountInput!) {
            moneyPlan {
                addAccount(input: $input) {
                    ... on Success {
                        data {
                            id
                            name
                        }
                    }
                    ... on ApplicationError {
                        message
                    }
                }
            }
        }
        """
        account_variables = {
            "input": {
                "planId": plan_id_user1,
                "name": "User 1 Account",
                "buckets": [{"bucketName": "Default", "category": "default", "allocatedAmount": 1000.0}],
            }
        }
        self.execute_query(client, add_account_mutation, user=user1, variables=account_variables)

        # Create second user
        user2 = self.get_test_user(client, email="user2@example.com")

        # User2 tries to access User1's specific plan
        query = """
        query GetMoneyPlan($planId: GlobalID!) {
            moneyPlan(planId: $planId) {
                id
                initialBalance
                accounts {
                    id
                    name
                }
            }
        }
        """
        result = self.execute_query(client, query, user=user2, variables={"planId": plan_id_user1})

        # User2 should not be able to see User1's plan
        assert result["moneyPlan"] is None

        # Now check that User2 doesn't see User1's plans in the list
        list_query = """
        query GetMoneyPlans {
            moneyPlans {
                edges {
                    node {
                        id
                        notes
                    }
                }
            }
        }
        """
        result = self.execute_query(client, list_query, user=user2)

        # User2 should not see any plans from User1
        # (the edges array should be empty or not contain User1's plan)
        assert len(result["moneyPlans"]["edges"]) == 0

        # Create a plan for User2 to verify they can see their own plans
        variables = {"input": {"initialBalance": 2000.0, "notes": "User 2's plan"}}
        self.execute_query(client, create_plan_mutation, user=user2, variables=variables)

        # Now User2 should see exactly one plan (their own)
        result = self.execute_query(client, list_query, user=user2)
        assert len(result["moneyPlans"]["edges"]) == 1
        assert result["moneyPlans"]["edges"][0]["node"]["notes"] == "User 2's plan"

    def test_user_cannot_see_another_users_accounts(self, client: Client):
        """Test that one user cannot see another user's accounts."""
        # Create first user and set up account
        user1 = self.get_test_user(client, email="user1_accounts@example.com")

        # Create a plan and account for first user
        create_plan_mutation = """
        mutation StartPlan($input: PlanStartInput!) {
            moneyPlan {
                startPlan(input: $input) {
                    ... on Success {
                        data
                    }
                }
            }
        }
        """
        variables = {"input": {"initialBalance": 1000.0, "notes": "User 1's plan"}}
        result = self.execute_query(client, create_plan_mutation, user=user1, variables=variables)
        plan_id = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Add an account to this plan
        add_account_mutation = """
        mutation AddAccount($input: AddAccountInput!) {
            moneyPlan {
                addAccount(input: $input) {
                    ... on Success {
                        data
                    }
                }
            }
        }
        """
        account_variables = {
            "input": {
                "planId": plan_id,
                "name": "User 1 Special Account",
                "buckets": [{"bucketName": "Default", "category": "default", "allocatedAmount": 1000.0}],
            }
        }
        self.execute_query(client, add_account_mutation, user=user1, variables=account_variables)

        # Create second user
        user2 = self.get_test_user(client, email="user2_accounts@example.com")

        # User2 queries the accounts list
        accounts_query = """
        query GetAccounts {
            accounts {
                id
                name
            }
        }
        """
        result = self.execute_query(client, accounts_query, user=user2)

        # User2 should not see User1's account
        account_names = [account["name"] for account in result["accounts"]]
        assert "User 1 Special Account" not in account_names

    def test_user_cannot_modify_another_users_plan(self, client: Client):
        """Test that one user cannot modify another user's money plan."""
        # Create first user and their plan
        user1 = self.get_test_user(client, email="user1_modify@example.com")

        # Create a plan for user1
        create_plan_mutation = """
        mutation StartPlan($input: PlanStartInput!) {
            moneyPlan {
                startPlan(input: $input) {
                    ... on Success {
                        data
                    }
                }
            }
        }
        """
        variables = {"input": {"initialBalance": 1000.0, "notes": "User 1's plan to be protected"}}
        result = self.execute_query(client, create_plan_mutation, user=user1, variables=variables)
        plan_id_user1 = result["moneyPlan"]["startPlan"]["data"]["id"]

        # Add an account to this plan
        add_account_mutation = """
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
        """
        account_variables = {
            "input": {
                "planId": plan_id_user1,
                "name": "User 1 Protected Account",
                "buckets": [{"bucketName": "Default", "category": "default", "allocatedAmount": 1000.0}],
            }
        }
        account_result = self.execute_query(
            client, add_account_mutation, user=user1, variables=account_variables
        )
        account_id_user1 = account_result["moneyPlan"]["addAccount"]["data"]["id"]

        # Create second user
        user2 = self.get_test_user(client, email="user2_modify@example.com")

        # User2 tries to edit User1's plan notes
        edit_notes_mutation = """
        mutation EditPlanNotes($input: EditPlanNotesInput!) {
            moneyPlan {
                editPlanNotes(input: $input) {
                    ... on Success {
                        data
                    }
                    ... on ApplicationError {
                        message
                    }
                }
            }
        }
        """
        edit_variables = {
            "input": {
                "planId": plan_id_user1,
                "notes": "User 2 trying to modify User 1's plan",
            }
        }
        result = self.execute_query(client, edit_notes_mutation, user=user2, variables=edit_variables)

        # User2's attempt to edit User1's plan should fail
        assert "data" not in result["moneyPlan"]["editPlanNotes"]
        assert "message" in result["moneyPlan"]["editPlanNotes"]

        # User2 tries to add an account to User1's plan
        account_variables = {
            "input": {
                "planId": plan_id_user1,
                "name": "User 2's Intrusion Account",
                "buckets": [{"bucketName": "Intrusion", "category": "intrusion", "allocatedAmount": 500.0}],
            }
        }
        result = self.execute_query(client, add_account_mutation, user=user2, variables=account_variables)

        # User2's attempt to add an account to User1's plan should fail
        assert "data" not in result["moneyPlan"]["addAccount"]
        assert "message" in result["moneyPlan"]["addAccount"]

        # User2 tries to edit User1's account notes
        edit_account_notes_mutation = """
        mutation EditAccountNotes($input: EditAccountNotesInput!) {
            moneyPlan {
                editAccountNotes(input: $input) {
                    ... on Success {
                        data
                    }
                    ... on ApplicationError {
                        message
                    }
                }
            }
        }
        """
        edit_account_variables = {
            "input": {
                "planId": plan_id_user1,
                "accountId": account_id_user1,
                "notes": "User 2 trying to modify User 1's account",
            }
        }
        result = self.execute_query(
            client, edit_account_notes_mutation, user=user2, variables=edit_account_variables
        )

        # User2's attempt to edit User1's account notes should fail
        assert "data" not in result["moneyPlan"]["editAccountNotes"]
        assert "message" in result["moneyPlan"]["editAccountNotes"]

    def test_duplicate_username_registration_fails(self, client: Client):
        """Test that registration with duplicate username fails."""
        # Register first user
        username = self.fake.user_name()
        email1 = self.fake.email()

        register_mutation = """
        mutation($username: String!, $email: String!, $password: String!) {
            auth {
                register(username: $username, email: $email, password: $password) {
                    success
                    error
                    token
                }
            }
        }
        """
        variables = {
            "username": username,
            "email": email1,
            "password": "SecurePassword123!",
        }

        result = self.execute_query(client, register_mutation, variables=variables)
        assert result["auth"]["register"]["success"] is True

        # Try to register a second user with the same username
        email2 = self.fake.email()
        variables = {
            "username": username,  # Same username
            "email": email2,  # Different email
            "password": "AnotherSecurePassword456!",
        }

        result = self.execute_query(client, register_mutation, variables=variables)
        assert result["auth"]["register"]["success"] is False
        # The error message should indicate the username is already taken
        assert "username" in result["auth"]["register"]["error"].lower()

    def test_duplicate_email_registration_fails(self, client: Client):
        """Test that registration with duplicate email fails."""
        # Register first user
        username1 = self.fake.user_name()
        email = self.fake.email()

        register_mutation = """
        mutation($username: String!, $email: String!, $password: String!) {
            auth {
                register(username: $username, email: $email, password: $password) {
                    success
                    error
                    token
                }
            }
        }
        """
        variables = {
            "username": username1,
            "email": email,
            "password": "SecurePassword123!",
        }

        result = self.execute_query(client, register_mutation, variables=variables)
        assert result["auth"]["register"]["success"] is True

        # Try to register a second user with the same email
        username2 = self.fake.user_name()
        variables = {
            "username": username2,  # Different username
            "email": email,  # Same email
            "password": "AnotherSecurePassword456!",
        }

        result = self.execute_query(client, register_mutation, variables=variables)
        assert result["auth"]["register"]["success"] is False
        # The error message should indicate the email is already taken
        assert "email" in result["auth"]["register"]["error"].lower()
