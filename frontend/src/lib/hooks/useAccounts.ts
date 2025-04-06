import { useState } from 'react';
import { useMutation, useQuery } from '@apollo/client';
import {
  GET_ACCOUNTS,
  CREATE_ACCOUNT,
  UPDATE_ACCOUNT,
  DELETE_ACCOUNT,
} from '@/lib/graphql/operations';
import { Account, CreateAccountInput, UpdateAccountInput } from '@/lib/graphql/types';

export const useAccounts = () => {
  const [error, setError] = useState<string | null>(null);

  const { data, loading, refetch } = useQuery(GET_ACCOUNTS);

  const [createAccount] = useMutation(CREATE_ACCOUNT, {
    onCompleted: () => {
      refetch();
    },
    onError: (error) => {
      setError(error.message);
    },
  });

  const [updateAccount] = useMutation(UPDATE_ACCOUNT, {
    onCompleted: () => {
      refetch();
    },
    onError: (error) => {
      setError(error.message);
    },
  });

  const [deleteAccount] = useMutation(DELETE_ACCOUNT, {
    onCompleted: () => {
      refetch();
    },
    onError: (error) => {
      setError(error.message);
    },
  });

  const handleCreateAccount = async (input: CreateAccountInput) => {
    try {
      await createAccount({
        variables: { input },
      });
      setError(null);
    } catch (error) {
      // Error is handled by onError callback
    }
  };

  const handleUpdateAccount = async (id: string, input: UpdateAccountInput) => {
    try {
      await updateAccount({
        variables: { id, input },
      });
      setError(null);
    } catch (error) {
      // Error is handled by onError callback
    }
  };

  const handleDeleteAccount = async (id: string) => {
    try {
      await deleteAccount({
        variables: { id },
      });
      setError(null);
    } catch (error) {
      // Error is handled by onError callback
    }
  };

  return {
    accounts: data?.accounts || [],
    loading,
    error,
    createAccount: handleCreateAccount,
    updateAccount: handleUpdateAccount,
    deleteAccount: handleDeleteAccount,
    refetch,
  };
}; 