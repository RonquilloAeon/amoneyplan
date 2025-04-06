'use client';

import { ApolloClient, ApolloProvider, InMemoryCache, createHttpLink } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { useSession } from 'next-auth/react';

const httpLink = createHttpLink({
  uri: process.env.NEXT_PUBLIC_GRAPHQL_URL || 'http://localhost:8001/graphql/',
});

export function ApolloWrapper({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession();

  const authLink = setContext((_, { headers }) => {
    // Get the authentication token from the session if it exists
    const token = session?.accessToken;
    
    // Return the headers to the context so httpLink can read them
    return {
      headers: {
        ...headers,
        authorization: token ? `Bearer ${token}` : '',
      },
    };
  });

  const client = new ApolloClient({
    link: authLink.concat(httpLink),
    cache: new InMemoryCache(),
    defaultOptions: {
      watchQuery: {
        fetchPolicy: 'cache-and-network',
      },
    },
  });

  return <ApolloProvider client={client}>{children}</ApolloProvider>;
} 