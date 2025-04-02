import gql from 'graphql-tag';

export const LOGIN_MUTATION = gql`
  mutation Login($username: String!, $password: String!) {
    auth {
      login(username: $username, password: $password) {
        success
        error
        token
      }
    }
  }
`;

export const REGISTER_MUTATION = gql`
  mutation Register($username: String!, $email: String!, $password: String!, $firstName: String!, $lastName: String!) {
    auth {
      register(username: $username, email: $email, password: $password, firstName: $firstName, lastName: $lastName) {
        success
        error
      }
    }
  }
`;

export const LOGOUT_MUTATION = gql`
  mutation Logout {
    auth {
      logout {
        success
        error
      }
    }
  }
`;

export const GOOGLE_AUTH_URL = gql`
  mutation GoogleAuthUrl {
    auth {
      googleAuthUrl {
        authUrl
      }
    }
  }
`;

export const GOOGLE_AUTH_CALLBACK = gql`
  mutation GoogleAuthCallback($code: String!) {
    auth {
      googleCallback(code: $code) {
        success
        error
      }
    }
  }
`;

export const ME_QUERY = gql`
  query Me {
    me {
      id
      username
      email
      firstName
      lastName
    }
  }
`;