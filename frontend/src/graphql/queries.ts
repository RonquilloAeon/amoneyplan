import gql from 'graphql-tag';

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
