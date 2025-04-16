'use client';

import { ReactNode } from 'react';
import { SessionProvider } from 'next-auth/react';
import { ApolloProvider } from '@apollo/client';
import client from '../lib/apollo-client';
import { Toaster } from '@/components/ui/toaster';
import { AuthProvider } from '@/lib/auth/AuthContext';

// Combine all providers
export function Providers({ children }: { children: ReactNode }) {
  return (
    <SessionProvider>
      <ApolloProvider client={client}>
        <AuthProvider>
          {children}
          <Toaster />
        </AuthProvider>
      </ApolloProvider>
    </SessionProvider>
  );
}