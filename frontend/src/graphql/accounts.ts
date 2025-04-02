import gql from 'graphql-tag';

export const CREATE_ACCOUNT = gql`
  mutation CreateAccount($input: CreateAccountInput!) {
    accounts {
      create(input: $input) {
        ... on Success {
          message
          node {
            id
            name
            type
            balance
            currency
            createdAt
            updatedAt
          }
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

export const UPDATE_ACCOUNT = gql`
  mutation UpdateAccount($id: ID!, $input: UpdateAccountInput!) {
    accounts {
      update(id: $id, input: $input) {
        ... on Success {
          message
          node {
            id
            name
            type
            balance
            currency
            createdAt
            updatedAt
          }
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

export const DELETE_ACCOUNT = gql`
  mutation DeleteAccount($id: ID!) {
    accounts {
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

export const ACCOUNTS_QUERY = gql`
  query Accounts {
    accounts {
      list {
        id
        name
        type
        balance
        currency
        createdAt
        updatedAt
      }
    }
  }
`;

export const ACCOUNT_QUERY = gql`
  query Account($id: ID!) {
    accounts {
      get(id: $id) {
        id
        name
        type
        balance
        currency
        createdAt
        updatedAt
      }
    }
  }
`; 