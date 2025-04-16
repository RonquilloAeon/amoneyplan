import { gql } from '@apollo/client';

// Account Operations
export const GET_ACCOUNTS = gql`
  query GetAccounts {
    accounts {
      id
      name
      notes
    }
  }
`;

export const CREATE_ACCOUNT = gql`
  mutation CreateAccount($input: CreateAccountInput!) {
    account {
      create(input: $input) {
        ... on Success {
          data
          message
        }
        ... on ApplicationError {
          message
        }
      }
    }
  }
`;

export const UPDATE_ACCOUNT = gql`
  mutation UpdateAccount($input: UpdateAccountInput!) {
    account {
      update(input: $input) {
        ... on Success {
          data
          message
        }
        ... on ApplicationError {
          message
        }
      }
    }
  }
`;

// Plan Operations
export const GET_PLANS = gql`
  query GetPlans($filter: MoneyPlanFilter) {
    moneyPlans(filter: $filter) {
      edges {
        node {
          id
          initialBalance
          remainingBalance
          notes
          isCommitted
          isArchived
          createdAt
          planDate
          archivedAt
          accounts {
            id
            isChecked
            notes
            account {
              id
              name
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
      pageInfo {
        hasNextPage
        hasPreviousPage
        startCursor
        endCursor
      }
    }
  }
`;

export const GET_DRAFT_PLAN = gql`
  query GetDraftPlan {
    draftMoneyPlan {
      id
      initialBalance
      remainingBalance
      notes
      isCommitted
      isArchived
      createdAt
      planDate
      archivedAt
      accounts {
        id
        isChecked
        notes
        account {
          id
          name
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

export const CREATE_PLAN = gql`
  mutation CreatePlan($input: PlanStartInput!) {
    moneyPlan {
      startPlan(input: $input) {
        ... on Success {
          data
          message
        }
        ... on ApplicationError {
          message
        }
      }
    }
  }
`;

export const UPDATE_PLAN = gql`
  mutation UpdatePlan($id: GlobalID!, $input: PlanBalanceAdjustInput!) {
    moneyPlan {
      adjustPlanBalance(input: $input) {
        ... on Success {
          data
          message
        }
        ... on ApplicationError {
          message
        }
      }
    }
  }
`;

export const COMMIT_PLAN = gql`
  mutation CommitPlan($id: GlobalID!) {
    moneyPlan {
      commitPlan(input: { planId: $id }) {
        ... on Success {
          data
          message
        }
        ... on ApplicationError {
          message
        }
      }
    }
  }
`;

export const ARCHIVE_PLAN = gql`
  mutation ArchivePlan($id: GlobalID!) {
    moneyPlan {
      archivePlan(input: { planId: $id }) {
        ... on Success {
          data
          message
        }
        ... on ApplicationError {
          message
        }
      }
    }
  }
`;

// Plan Account Operations
export const ADD_ACCOUNT_TO_PLAN = gql`
  mutation AddAccountToPlan($planId: GlobalID!, $accountId: GlobalID!, $buckets: [BucketConfigInput!]!) {
    moneyPlan {
      addAccount(input: { planId: $planId, accountId: $accountId, buckets: $buckets, notes: "" }) {
        ... on Success {
          data
          message
        }
        ... on ApplicationError {
          message
        }
      }
    }
  }
`;

export const UPDATE_PLAN_ACCOUNT = gql`
  mutation UpdatePlanAccount($planId: GlobalID!, $accountId: GlobalID!, $buckets: [BucketConfigInput!]!) {
    moneyPlan {
      changeAccountConfiguration(input: { planId: $planId, accountId: $accountId, newBucketConfig: $buckets }) {
        ... on Success {
          data
          message
        }
        ... on ApplicationError {
          message
        }
      }
    }
  }
`;

export const REMOVE_ACCOUNT_FROM_PLAN = gql`
  mutation RemoveAccountFromPlan($planId: GlobalID!, $accountId: GlobalID!) {
    moneyPlan {
      removeAccount(input: { planId: $planId, accountId: $accountId }) {
        ... on Success {
          data
          message
        }
        ... on ApplicationError {
          message
        }
      }
    }
  }
`;

export const UPDATE_PLAN_ACCOUNT_NOTES = gql`
  mutation UpdatePlanAccountNotes($planId: GlobalID!, $accountId: GlobalID!, $notes: String!) {
    moneyPlan {
      editAccountNotes(input: { planId: $planId, accountId: $accountId, notes: $notes }) {
        ... on Success {
          data
          message
        }
        ... on ApplicationError {
          message
        }
      }
    }
  }
`;

export const UPDATE_PLAN_NOTES = gql`
  mutation UpdatePlanNotes($planId: GlobalID!, $notes: String!) {
    moneyPlan {
      editPlanNotes(input: { planId: $planId, notes: $notes }) {
        ... on Success {
          data
          message
        }
        ... on ApplicationError {
          message
        }
      }
    }
  }
`;

export const GET_PLAN = gql`
  query GetPlan($id: GlobalID!) {
    moneyPlan(id: $id) {
      id
      initialBalance
      remainingBalance
      notes
      isCommitted
      isArchived
      createdAt
      planDate
      archivedAt
      accounts {
        id
        isChecked
        notes
        account {
          id
          name
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

export const SET_ACCOUNT_CHECKED_STATE = gql`
  mutation SetAccountCheckedState($planId: GlobalID!, $accountId: GlobalID!, $isChecked: Boolean!) {
    moneyPlan {
      setAccountCheckedState(input: { planId: $planId, accountId: $accountId, isChecked: $isChecked }) {
        ... on EmptySuccess {
          message
        }
        ... on ApplicationError {
          message
        }
      }
    }
  }
`; 