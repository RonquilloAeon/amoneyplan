from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from amoneyplan.domain.money import Money

from .utils import TestGraphQLAPI


@pytest.mark.django_db(transaction=True)
class TestShareLink(TestGraphQLAPI):
    @patch("amoneyplan.money_plans.use_cases.MoneyPlanUseCases.create_share_link")
    def test_create_share_link(self, mock_create_share_link, client):
        """Test creating a share link for a plan."""
        # Get a test user
        user = self.get_test_user(client)

        # Mock the share link response
        token = "test_token_12345"
        expires_at = timezone.now() + timedelta(days=14)
        mock_link = MagicMock()
        mock_link.token = token
        mock_link.expires_at = expires_at

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = mock_link

        mock_create_share_link.return_value = mock_result

        # Create a share link for the plan
        create_link_mutation = """
        mutation CreateShareLink($planId: GlobalID!, $expiryDays: Int) {
            moneyPlan {
                createShareLink(input: { planId: $planId, expiryDays: $expiryDays }) {
                    ... on ShareLinkResponse {
                        token
                        expiresAt
                        url
                    }
                    ... on ApplicationError {
                        message
                    }
                }
            }
        }
        """
        variables = {
            "planId": "UGxhbjoxMjM0NQ==",  # Mocked plan ID in Base64
            "expiryDays": 7,
        }

        result = self.execute_query(client, create_link_mutation, user=user, variables=variables)

        # Verify the response
        assert "errors" not in result
        share_link_response = result["moneyPlan"]["createShareLink"]
        assert "token" in share_link_response
        assert "expiresAt" in share_link_response
        assert "url" in share_link_response

        # Verify the token is in the URL
        assert token in share_link_response["url"]

        # Verify create_share_link was called with the right parameters
        mock_create_share_link.assert_called_once()

    @patch("amoneyplan.money_plans.use_cases.MoneyPlanUseCases.get_shared_plan")
    def test_access_shared_plan(self, mock_get_shared_plan, client):
        """Test accessing a plan with a share link."""
        # Get a test user
        self.get_test_user(client)

        # Mock the plan response
        mock_plan = MagicMock()
        mock_plan.id = "plan_123"
        mock_plan.initial_balance = Money(1000)
        mock_plan.remaining_balance = Money(0)
        mock_plan.notes = "Test shared plan"

        # Mock account and buckets
        mock_account = MagicMock()
        mock_account.account_id = "account_123"
        mock_account.name = "Test Account"
        mock_account.is_checked = False
        mock_account.notes = ""

        mock_bucket = MagicMock()
        mock_bucket.name = "Default"
        mock_bucket.category = "default"
        mock_bucket.allocated_amount = Money(1000)

        # Add bucket to account's buckets
        mock_account.buckets = {"default": mock_bucket}

        # Set up the account allocations
        mock_allocation = MagicMock()
        mock_allocation.account = mock_account
        mock_allocation.name = "Test Account"
        mock_allocation.account.account_id = "account_123"

        # Link accounts to plan
        mock_plan.accounts = {"test_account": mock_allocation}

        # Set up the mock result
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.has_data = lambda: True
        mock_result.data = mock_plan

        # Configure mock
        mock_get_shared_plan.return_value = mock_result

        # Create a token to use
        token = "test_token_12345"

        # Query for the shared plan
        get_shared_plan_query = """
        query GetSharedPlan($token: String!) {
            sharedPlan(token: $token) {
                id
                initialBalance
                remainingBalance
                notes
                accounts {
                    id
                    account {
                        name
                    }
                    buckets {
                        name
                        category
                        allocatedAmount
                    }
                }
            }
        }
        """
        variables = {"token": token}

        # Execute as unauthenticated user
        result = self.execute_query(client, get_shared_plan_query, user=None, variables=variables)

        # Verify the plan data is accessible
        assert "errors" not in result
        shared_plan = result["sharedPlan"]
        assert shared_plan is not None
        assert shared_plan["initialBalance"] == 1000.0
        assert shared_plan["remainingBalance"] == 0.0
        assert shared_plan["notes"] == "Test shared plan"

        # Verify mock was called with the token
        mock_get_shared_plan.assert_called_once_with(token)

    @patch("amoneyplan.money_plans.use_cases.MoneyPlanUseCases.get_shared_plan")
    def test_expired_share_link(self, mock_get_shared_plan, client):
        """Test that expired share links don't work."""
        # Get a test user
        self.get_test_user(client)

        # Create an error response
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error = MagicMock()
        mock_result.error.message = "The share link has expired or does not exist"

        # Configure mock
        mock_get_shared_plan.return_value = mock_result

        # Create a token to use
        token = "expired_token_12345"

        # Query for the shared plan
        get_shared_plan_query = """
        query GetSharedPlan($token: String!) {
            sharedPlan(token: $token) {
                id
                initialBalance
                remainingBalance
            }
        }
        """
        variables = {"token": token}

        # Execute as unauthenticated user
        result = self.execute_query(client, get_shared_plan_query, user=None, variables=variables)

        assert result["sharedPlan"] is None

    def test_invalid_share_link(self, client):
        """Test that invalid share links don't work."""
        # Try to access a plan with an invalid token
        get_shared_plan_query = """
        query GetSharedPlan($token: String!) {
            sharedPlan(token: $token) {
                id
            }
        }
        """
        variables = {"token": "invalid_token"}

        # Execute as unauthenticated user
        result = self.execute_query(client, get_shared_plan_query, user=None, variables=variables)

        # Verify the plan is not accessible
        assert "errors" not in result
        assert result["sharedPlan"] is None

    def test_unauthenticated_cannot_create_share_link(self, client):
        """Test that unauthenticated users cannot create share links."""
        # Get a test user to create a plan
        user = self.get_test_user(client)

        # Create a test plan with an account
        plan_id, account_id = self.create_test_plan(client, user)

        # Try to create a share link without authentication
        create_link_mutation = """
        mutation CreateShareLink($planId: GlobalID!) {
            moneyPlan {
                createShareLink(input: { planId: $planId }) {
                    ... on ShareLinkResponse {
                        token
                    }
                    ... on ApplicationError {
                        message
                    }
                }
            }
        }
        """
        variables = {"planId": plan_id}

        # This should fail with an authentication error
        result = self.execute_query(
            client, create_link_mutation, user=None, variables=variables, fail_on_error=False
        )

        # Query should fail and return no data
        assert result is None

    def test_other_user_cannot_access_private_plan(self, client):
        """Test that a user cannot access another user's plan without share link."""
        # Create two users
        user1 = self.get_test_user(client, email="user1@example.com")
        user2 = self.get_test_user(client, email="user2@example.com")

        # User 1 creates a plan
        plan_id, _ = self.create_test_plan(client, user1)

        # User 2 tries to access User 1's plan directly
        get_plan_query = """
        query GetMoneyPlan($id: GlobalID!) {
            moneyPlan(id: $id) {
                id
                initialBalance
            }
        }
        """
        variables = {"id": plan_id}

        result = self.execute_query(client, get_plan_query, user=user2, variables=variables)

        # Plan should not be accessible to user2
        assert "errors" not in result
        assert result["moneyPlan"] is None

        # But User 2 can access the plan via a share link
        create_link_mutation = """
        mutation CreateShareLink($planId: GlobalID!) {
            moneyPlan {
                createShareLink(input: { planId: $planId }) {
                    ... on ShareLinkResponse {
                        token
                    }
                }
            }
        }
        """

        result = self.execute_query(client, create_link_mutation, user=user1, variables={"planId": plan_id})
        token = result["moneyPlan"]["createShareLink"]["token"]

        get_shared_plan_query = """
        query GetSharedPlan($token: String!) {
            sharedPlan(token: $token) {
                id
                initialBalance
            }
        }
        """

        # User 2 can access the shared plan even when authenticated as a different user
        result = self.execute_query(client, get_shared_plan_query, user=user2, variables={"token": token})

        assert "errors" not in result
        assert result["sharedPlan"]["id"] == plan_id
        assert result["sharedPlan"]["initialBalance"] == 1000.0
