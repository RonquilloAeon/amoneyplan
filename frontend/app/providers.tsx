'use client';

import { ReactNode, useState, useEffect } from 'react';
import { SessionProvider } from 'next-auth/react';
import { ApolloClient, ApolloProvider, InMemoryCache, createHttpLink } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { useSession } from 'next-auth/react';

// Function to create Apollo Client with NextAuth authentication
function createApolloClient() {
  // Create the http link
  const httpLink = createHttpLink({
    uri: process.env.NEXT_PUBLIC_GRAPHQL_URL || 'http://localhost:8001/graphql/',
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
    link: authLink.concat(httpLink),
    cache: new InMemoryCache(),
    defaultOptions: {
      watchQuery: {
        fetchPolicy: 'cache-and-network',
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