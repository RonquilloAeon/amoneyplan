'use client';

import { useState, useCallback } from 'react';
import { useMutation, useQuery } from '@apollo/client';
import { GET_ACCOUNTS, CREATE_ACCOUNT, UPDATE_ACCOUNT } from '../graphql/operations';

export interface Account {
  id: string;
  name: string;
}

export interface CreateAccountInput {
  name: string;
  notes?: string;
}

export interface UpdateAccountInput {
  accountId: string;
  name: string;
  notes?: string;
}

export function useAccounts() {
  const [error, setError] = useState<string | null>(null);

  // Query for accounts
  const { 
    data: accountsData, 
    loading, 
    refetch: refetchAccountsQuery
  } = useQuery(GET_ACCOUNTS, {
    onError: (error) => {
      setError(`Failed to load accounts: ${error.message}`);
    }
  });

  // Extract accounts from data
  const accounts = accountsData?.accounts || [];

  // Mutations
  const [createAccountMutation] = useMutation(CREATE_ACCOUNT);
  const [updateAccountMutation] = useMutation(UPDATE_ACCOUNT);

  // Helper functions to wrap mutations
  const createAccount = async (input: CreateAccountInput) => {
    try {
      const { data } = await createAccountMutation({
        variables: { input }
      });
      
      if (data?.account?.create.__typename === 'ApplicationError') {
        throw new Error(data.account.create.message);
      }
      
      await refetchAccountsQuery();
      
      return data?.account?.create.data;
    } catch (error) {
      if (error instanceof Error) {
        setError(`Failed to create account: ${error.message}`);
      }
      throw error;
    }
  };

  const updateAccount = async (input: UpdateAccountInput) => {
    try {
      const { data } = await updateAccountMutation({
        variables: { input }
      });
      
      if (data?.account?.update.__typename === 'ApplicationError') {
        throw new Error(data.account.update.message);
      }
      
      await refetchAccountsQuery();
      
      return data?.account?.update.data;
    } catch (error) {
      if (error instanceof Error) {
        setError(`Failed to update account: ${error.message}`);
      }
      throw error;
    }
  };

  const refetchAccounts = useCallback(async () => {
    try {
      await refetchAccountsQuery();
    } catch (error) {
      if (error instanceof Error) {
        setError(`Failed to refetch accounts: ${error.message}`);
      }
    }
  }, [refetchAccountsQuery]);

  return {
    accounts,
    loading,
    error,
    createAccount,
    updateAccount,
    refetchAccounts
  };
} 