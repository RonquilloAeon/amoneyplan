'use client';

import { ReactNode } from 'react';
import { SessionProvider } from 'next-auth/react';
import { ApolloProvider } from '@apollo/client';
import client from '../lib/apollo-client';
import { CustomToaster } from '@/components/CustomToaster';

// Combine all providers
export function Providers({ children }: { children: ReactNode }) {
  return (
    <SessionProvider>
      <ApolloProvider client={client}>
        {children}
        <CustomToaster />
      </ApolloProvider>
    </SessionProvider>
  );
} 