import gql from 'graphql-tag';

export const ACCOUNTS_QUERY = gql`
  query Accounts {
    accounts {
      id
      name
      type
      notes
    }
  }
`;

export const PLANS_FOR_COPY = gql`
  query PlansForCopy($first: Int, $after: String) {
    moneyPlans(first: $first, after: $after) {
      edges {
        node {
          id
          planDate
          notes
          isCommitted
        }
        cursor
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
`;

export const PLAN_ACCOUNTS_QUERY = gql`
  query PlanAccounts($planId: ID!) {
    moneyPlan(id: $planId) {
      planAccounts {
        id
        account {
          id
          name
          type
          notes
        }
        buckets {
          id
          name
          category
          allocatedAmount
        }
      }
    }
  }
`;
