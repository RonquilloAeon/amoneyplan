'use client';

import { useState, useCallback } from 'react';
import { useQuery } from '@apollo/client';
import { useSession } from 'next-auth/react';
import { GET_ACCOUNTS } from '../graphql/operations';
import { useToast } from '@/lib/hooks/useToast';
import { Account } from './useAccounts';
import { useUrlPagination } from './useUrlPagination';

export function useAccountsPaginated(pageSize = 10, paramName = 'page') {
  const [error, setError] = useState<string | null>(null);
  const { data: session } = useSession();
  const { toast } = useToast();

  // Query for accounts
  const {
    data: accountsData,
    loading,
    refetch: refetchAccountsQuery
  } = useQuery(GET_ACCOUNTS, {
    onError: (error) => {
      const errorMessage = `Failed to load accounts: ${error.message}`;
      setError(errorMessage);
      toast({
        variant: "destructive",
        title: "Error",
        description: errorMessage
      });
    },
    skip: !session // Skip if not authenticated
  });

  // Extract accounts from data
  const accounts = accountsData?.accounts || [];
  
  // Use URL-based pagination
  const { 
    currentPage, 
    totalPages, 
    indexOfFirstItem, 
    indexOfLastItem, 
    goToNextPage, 
    goToPreviousPage,
    goToPage
  } = useUrlPagination({ 
    totalItems: accounts.length, 
    pageSize, 
    paramName 
  });
  
  // Get current page data
  const currentAccounts = accounts.slice(indexOfFirstItem, indexOfLastItem);

  const refetchAccounts = useCallback(async () => {
    try {
      await refetchAccountsQuery();
    } catch (error) {
      if (error instanceof Error) {
        const errorMessage = `Failed to refetch accounts: ${error.message}`;
        setError(errorMessage);
        toast({
          variant: "destructive",
          title: "Error",
          description: errorMessage
        });
      }
    }
  }, [refetchAccountsQuery, toast]);

  return {
    accounts: currentAccounts,
    allAccounts: accounts,
    loading,
    error,
    currentPage,
    totalPages,
    goToNextPage,
    goToPreviousPage,
    goToPage,
    refetchAccounts
  };
} 