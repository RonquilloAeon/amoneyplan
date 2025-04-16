'use client';

import { useState, useCallback } from 'react';
import { useQuery } from '@apollo/client';
import { useSession } from 'next-auth/react';
import { GET_PLANS } from '../graphql/operations';
import { useToast } from '@/lib/hooks/useToast';
import { useUrlPagination } from './useUrlPagination';

export interface MoneyPlanFilter {
  isArchived?: boolean;
  status?: 'all' | 'draft' | 'committed';
}

export function usePlansUrlPaginated(pageSize = 10, filter?: MoneyPlanFilter, paramName = 'page') {
  const [error, setError] = useState<string | null>(null);
  const { data: session } = useSession();
  const { toast } = useToast();

  // Query for plans
  const {
    data: plansData,
    loading,
    refetch: refetchPlansQuery
  } = useQuery(GET_PLANS, {
    variables: { filter },
    onError: (error) => {
      const errorMessage = `Failed to load plans: ${error.message}`;
      setError(errorMessage);
      toast({
        variant: "destructive",
        title: "Error",
        description: errorMessage
      });
    },
    skip: !session // Skip if not authenticated
  });

  // Extract plans from data
  const plans = plansData?.moneyPlans?.edges?.map(edge => edge.node) || [];
  
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
    totalItems: plans.length, 
    pageSize, 
    paramName 
  });
  
  // Get current page data
  const currentPlans = plans.slice(indexOfFirstItem, indexOfLastItem);

  const refetchPlans = useCallback(async () => {
    try {
      await refetchPlansQuery();
    } catch (error) {
      if (error instanceof Error) {
        const errorMessage = `Failed to refetch plans: ${error.message}`;
        setError(errorMessage);
        toast({
          variant: "destructive",
          title: "Error",
          description: errorMessage
        });
      }
    }
  }, [refetchPlansQuery, toast]);

  return {
    plans: currentPlans,
    allPlans: plans,
    loading,
    error,
    currentPage,
    totalPages,
    goToNextPage,
    goToPreviousPage,
    goToPage,
    refetchPlans
  };
} 