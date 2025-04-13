'use client';

import { ReactNode, useState, useEffect } from 'react';
import { SessionProvider } from 'next-auth/react';
import { ApolloClient, ApolloProvider, InMemoryCache, createHttpLink, from, FetchPolicy } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { onError } from '@apollo/client/link/error';
import { useSession, signOut } from 'next-auth/react';

// Function to create Apollo Client with NextAuth authentication
function createApolloClient() {
  // Create the http link
  const httpLink = createHttpLink({
    uri: process.env.NEXT_PUBLIC_GRAPHQL_URL || 'http://localhost:8001/graphql/',
  });

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

  // Create the auth link
  const authLink = setContext((_, { headers }) => {
    // Get the token from localStorage (client-side only)
    let token = null;
    
    if (typeof window !== 'undefined') {
      const session = JSON.parse(localStorage.getItem('next-auth.session-token') || '{}');
      token = session?.authToken;
    }
    
    // Return the headers to the context so httpLink can read them
    return {
      headers: {
        ...headers,
        authorization: token ? `Bearer ${token}` : '',
      },
    };
  });
  
  return new ApolloClient({
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
}

// Apollo provider with session
function ApolloProviderWithAuth({ children }: { children: ReactNode }) {
  const { data: session } = useSession();
  const [client, setClient] = useState<ApolloClient<any> | null>(null);
  
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // Store the session in localStorage for Apollo Client to access
      if (session?.authToken) {
        localStorage.setItem('next-auth.session-token', JSON.stringify(session));
      }
      
      // Create client if it doesn't exist
      if (!client) {
        setClient(createApolloClient());
      }
    }
  }, [session, client]);
  
  if (!client) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }
  
  return (
    <ApolloProvider client={client}>
      {children}
    </ApolloProvider>
  );
}

// Combine all providers
export function Providers({ children }: { children: ReactNode }) {
  return (
    <SessionProvider>
      <ApolloProviderWithAuth>
        {children}
      </ApolloProviderWithAuth>
    </SessionProvider>
  );
} 