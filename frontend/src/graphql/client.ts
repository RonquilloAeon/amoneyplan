import { createClient, cacheExchange, fetchExchange } from '@urql/vue';

export const client = createClient({
  url: 'http://localhost:8000/graphql/',  // TODO abstract this to an environment variable
  fetchOptions: {
    credentials: 'include', // This enables sending cookies with requests
  },
  exchanges: [cacheExchange, fetchExchange],
});