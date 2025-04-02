import gql from 'graphql-tag';
import { createClient, cacheExchange, fetchExchange } from '@urql/core';
import type { Exchange, Operation, OperationResult } from '@urql/core';
import { pipe, tap } from 'wonka';
import logger from '../utils/logger';

// Create a debug exchange to log all operations
const debugExchange: Exchange = ({ forward }) => ops$ => {
  return pipe(
    ops$,
    tap((operation: Operation) => {
      logger.debug('GraphQL:Request', `Operation: ${operation.kind} - ${operation.query.definitions[0].kind === 'OperationDefinition' ? operation.query.definitions[0].operation : 'unknown'}`, {
        name: operation.query.definitions[0].kind === 'OperationDefinition' ? 
          operation.query.definitions[0].name?.value : 'unnamed',
        variables: operation.variables
      });
    }),
    forward,
    tap((result: OperationResult) => {
      if (result.error) {
        logger.error('GraphQL:Response', 'Error in operation', result.error);
      } else {
        logger.debug('GraphQL:Response', 'Operation result', {
          data: result.data,
          stale: result.stale,
          hasNext: result.hasNext
        });
      }
    })
  );
};

// Create a function to get a fresh client instance with the latest token
export const getClient = () => {
  const token = localStorage.getItem('token');
  logger.debug('GraphQL', 'Getting client with token', token ? `${token.substring(0, 10)}...` : 'No token');
  
  // Debug info about local storage
  logger.debug('GraphQL', 'LocalStorage keys', Object.keys(localStorage));
  
  const client = createClient({
    url: import.meta.env.VITE_GRAPHQL_URL,
    exchanges: [debugExchange, cacheExchange, fetchExchange],
    fetchOptions: () => {
      logger.debug('GraphQL', 'Preparing request with token', token ? `${token.substring(0, 10)}...` : 'No token');
      return {
        headers: {
          Authorization: token ? `Bearer ${token}` : '',
        },
      };
    },
  });
  
  logger.debug('GraphQL', 'Client created with URL', import.meta.env.VITE_GRAPHQL_URL);
  return client;
};

export const CREATE_MONEY_PLAN = gql`
  mutation StartPlan($input: PlanStartInput!) {
    moneyPlan {
      startPlan(input: $input) {
        ... on Success {
          message
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
`;

export const UPDATE_MONEY_PLAN = gql`
  mutation UpdateMoneyPlan($id: ID!, $input: UpdateMoneyPlanInput!) {
    moneyPlan {
      update(input: $input) {
        ... on Success {
          message
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
`;

export const DELETE_MONEY_PLAN = gql`
  mutation DeleteMoneyPlan($id: ID!) {
    moneyPlan {
      delete(id: $id) {
        ... on Success {
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
`;

export const COMMIT_PLAN_MUTATION = gql`
  mutation CommitPlan($input: CommitPlanInput!) {
    moneyPlan {
      commitPlan(input: $input) {
        ... on Success {
          message
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
`;

export const ARCHIVE_PLAN_MUTATION = gql`
  mutation ArchivePlan($input: ArchivePlanInput!) {
    moneyPlan {
      archivePlan(input: $input) {
        ... on Success {
          message
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
`;

export const REMOVE_ACCOUNT_MUTATION = gql`
  mutation RemoveAccount($input: RemoveAccountInput!) {
    moneyPlan {
      removeAccount(input: $input) {
        ... on Success {
          message
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
`;

export const SET_ACCOUNT_CHECKED_MUTATION = gql`
  mutation SetAccountCheckedState($input: SetAccountCheckedStateInput!) {
    moneyPlan {
      setAccountCheckedState(input: $input) {
        ... on Success {
          message
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
`;

export const MONEY_PLANS_QUERY = gql`
  query MoneyPlans($filter: MoneyPlanFilter) {
    moneyPlans(filter: $filter) {
      edges {
        node {
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
            isChecked
            notes
          }
          notes
          isCommitted
          isArchived
          createdAt
          planDate
          archivedAt
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
`;

export const MONEY_PLAN_QUERY = gql`
  query MoneyPlan($id: GlobalID!) {
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
        isChecked
        notes
      }
      notes
      isCommitted
      isArchived
      createdAt
      planDate
      archivedAt
    }
  }
`;

export const DRAFT_MONEY_PLAN_QUERY = gql`
  query DraftMoneyPlan {
    draftMoneyPlan {
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
        isChecked
        notes
      }
      notes
      isCommitted
      isArchived
      createdAt
      planDate
      archivedAt
    }
  }
`; 