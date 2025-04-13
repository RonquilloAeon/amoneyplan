'use client';

import { ApolloClient, ApolloProvider, InMemoryCache, createHttpLink, from, FetchPolicy } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { onError } from '@apollo/client/link/error';
import { useSession, signOut } from 'next-auth/react';

const httpLink = createHttpLink({
  uri: process.env.NEXT_PUBLIC_GRAPHQL_URL || 'http://localhost:8001/graphql/',
});

export function ApolloWrapper({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession();

  // Error handling link for authentication errors
  const errorLink = onError(({ graphQLErrors, networkError }) => {
    if (graphQLErrors) {
      graphQLErrors.forEach(({ message, locations, path }) => {
        console.error(
          `[GraphQL error]: Message: ${message}, Location: ${locations}, Path: ${path}`,
        );
        
        // Check for authentication related errors
        if (
          message.includes('not authenticated') || 
          message.includes('authentication') || 
          message.includes('is_authenticated') ||
          message.includes('token is invalid') ||
          message.includes('token expired') ||
          message.includes('token has expired') ||
          message.includes('NoneType') ||
          message.includes('permission') ||
          message.includes('unauthorized')
        ) {
          console.error('Authentication error detected, redirecting to login...');
          
          // Clear session storage and redirect
          if (typeof window !== 'undefined') {
            // Use NextAuth signOut to clear the session
            signOut({ redirect: true, callbackUrl: '/auth/signin' });
          }
        }
      });
    }
    
    if (networkError) {
      console.error(`[Network error]: ${networkError}`);
      
      // Check if network error is related to authentication
      if (
        // @ts-ignore - Check for 401 in error message
        networkError.message?.includes('401') || 
        // @ts-ignore - Some network errors might include statusCode
        networkError.statusCode === 401
      ) {
        console.error('Authentication network error detected, redirecting to login...');
        
        if (typeof window !== 'undefined') {
          signOut({ redirect: true, callbackUrl: '/auth/signin' });
        }
      }
    }
  });

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
    link: from([errorLink, authLink, httpLink]),
    cache: new InMemoryCache(),
    defaultOptions: {
      watchQuery: {
        fetchPolicy: 'cache-and-network' as FetchPolicy,
        errorPolicy: 'all',
      },
      query: {
        fetchPolicy: 'cache-and-network' as FetchPolicy,
        errorPolicy: 'all',
      },
      mutate: {
        errorPolicy: 'all',
      },
    },
  });

  return <ApolloProvider client={client}>{children}</ApolloProvider>;
} 