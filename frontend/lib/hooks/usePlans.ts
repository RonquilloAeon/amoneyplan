'use client';

import { useCallback, useEffect, useState } from 'react';
import { useMutation, useQuery } from '@apollo/client';
import { useSession } from 'next-auth/react';
import {
  GET_PLANS,
  GET_DRAFT_PLAN,
  CREATE_PLAN,
  UPDATE_PLAN,
  COMMIT_PLAN,
  ARCHIVE_PLAN,
  ADD_ACCOUNT_TO_PLAN,
  UPDATE_PLAN_ACCOUNT,
  REMOVE_ACCOUNT_FROM_PLAN,
  UPDATE_PLAN_ACCOUNT_NOTES,
  UPDATE_PLAN_NOTES,
} from '../graphql/operations';
import { useToast } from '@/lib/hooks/useToast';

// Types based on the GraphQL schema
export interface Bucket {
  id: string;
  name: string;
  category: string;
  allocatedAmount: number;
}

export interface Account {
  id: string;
  name: string;
}

export interface PlanAccount {
  id: string;
  account: Account;
  buckets: Bucket[];
  isChecked: boolean;
  notes: string;
}

export interface Plan {
  id: string;
  initialBalance: number;
  remainingBalance: number;
  notes: string;
  isCommitted: boolean;
  isArchived: boolean;
  createdAt: string;
  planDate: string | null;
  archivedAt: string | null;
  accounts: PlanAccount[];
}

export interface PlanStartInput {
  initialBalance: number;
  notes?: string;
  planDate?: string;
  copyFrom?: string;
}

export interface BucketConfigInput {
  name: string;
  category: string;
  allocatedAmount: number;
}

export function usePlans() {
  const [error, setError] = useState<string | null>(null);
  const { data: session } = useSession();
  const { toast } = useToast();
  
  // Query for all plans
  const { 
    data: plansData, 
    loading: plansLoading, 
    refetch: refetchPlansQuery 
  } = useQuery(GET_PLANS, {
    variables: { filter: { isArchived: false } },
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
  
  // Query for draft plan
  const { 
    data: draftPlanData, 
    loading: draftPlanLoading, 
    refetch: refetchDraftQuery 
  } = useQuery(GET_DRAFT_PLAN, {
    onError: (error) => {
      const errorMessage = `Failed to load draft plan: ${error.message}`;
      setError(errorMessage);
      toast({
        variant: "destructive",
        title: "Error",
        description: errorMessage
      });
    },
    skip: !session // Skip if not authenticated
  });

  // Extract plans and draft plan from data
  const plans = plansData?.moneyPlans?.edges?.map(edge => edge.node) || [];
  const draftPlan = draftPlanData?.draftMoneyPlan || null;
  
  // Mutations
  const [createPlanMutation] = useMutation(CREATE_PLAN);
  const [updatePlanMutation] = useMutation(UPDATE_PLAN);
  const [commitPlanMutation] = useMutation(COMMIT_PLAN);
  const [archivePlanMutation] = useMutation(ARCHIVE_PLAN);
  const [addAccountToPlanMutation] = useMutation(ADD_ACCOUNT_TO_PLAN);
  const [updatePlanAccountMutation] = useMutation(UPDATE_PLAN_ACCOUNT);
  const [removeAccountFromPlanMutation] = useMutation(REMOVE_ACCOUNT_FROM_PLAN);
  const [updatePlanAccountNotesMutation] = useMutation(UPDATE_PLAN_ACCOUNT_NOTES);
  const [updatePlanNotesMutation] = useMutation(UPDATE_PLAN_NOTES);
  
  // Helper functions to wrap mutations
  const createPlan = async (input: PlanStartInput) => {
    try {
      const { data } = await createPlanMutation({
        variables: { input }
      });
      
      if (data?.moneyPlan?.startPlan.__typename === 'ApplicationError') {
        throw new Error(data.moneyPlan.startPlan.message);
      }
      
      await refetchDraftQuery();
      await refetchPlansQuery();
      
      return data?.moneyPlan?.startPlan.data;
    } catch (error) {
      if (error instanceof Error) {
        const errorMessage = `Failed to create plan: ${error.message}`;
        setError(errorMessage);
        toast({
          variant: "destructive",
          title: "Error",
          description: errorMessage
        });
      }
      throw error;
    }
  };

  const updatePlan = async (planId: string, adjustment: number, reason: string = '') => {
    try {
      const { data } = await updatePlanMutation({
        variables: {
          id: planId,
          input: {
            planId,
            adjustment,
            reason
          }
        }
      });
      
      if (data?.moneyPlan?.adjustPlanBalance.__typename === 'ApplicationError') {
        throw new Error(data.moneyPlan.adjustPlanBalance.message);
      }
      
      await refetchDraftQuery();
      return data?.moneyPlan?.adjustPlanBalance.data;
    } catch (error) {
      if (error instanceof Error) {
        const errorMessage = `Failed to update plan: ${error.message}`;
        setError(errorMessage);
        toast({
          variant: "destructive",
          title: "Error",
          description: errorMessage
        });
      }
      throw error;
    }
  };

  const commitPlan = async (planId: string) => {
    try {
      const { data } = await commitPlanMutation({
        variables: { id: planId }
      });
      
      if (data?.moneyPlan?.commitPlan.__typename === 'ApplicationError') {
        // Show error toast but don't throw to prevent UI disruption
        const errorMessage = data.moneyPlan.commitPlan.message;
        setError(errorMessage);
        toast({
          variant: "destructive", 
          title: "Cannot Commit Plan",
          description: errorMessage
        });
        return null;
      }
      
      await refetchDraftQuery();
      await refetchPlansQuery();
      
      toast({
        title: "Success",
        description: "Plan successfully committed"
      });
      
      return data?.moneyPlan?.commitPlan.data;
    } catch (error) {
      if (error instanceof Error) {
        const errorMessage = `Failed to commit plan: ${error.message}`;
        setError(errorMessage);
        toast({
          variant: "destructive",
          title: "Error",
          description: errorMessage
        });
        // Return null instead of throwing to prevent UI disruption
        return null;
      }
      throw error;
    }
  };

  const archivePlan = async (planId: string) => {
    try {
      const { data } = await archivePlanMutation({
        variables: { id: planId }
      });
      
      if (data?.moneyPlan?.archivePlan.__typename === 'ApplicationError') {
        throw new Error(data.moneyPlan.archivePlan.message);
      }
      
      await refetchPlansQuery();
      
      toast({
        title: "Success",
        description: "Plan successfully archived"
      });
      
      return data?.moneyPlan?.archivePlan.data;
    } catch (error) {
      if (error instanceof Error) {
        const errorMessage = `Failed to archive plan: ${error.message}`;
        setError(errorMessage);
        toast({
          variant: "destructive",
          title: "Error",
          description: errorMessage
        });
      }
      throw error;
    }
  };

  const addAccountToPlan = async (planId: string, accountId: string, buckets: BucketConfigInput[]) => {
    try {
      const { data } = await addAccountToPlanMutation({
        variables: { planId, accountId, buckets }
      });
      
      if (data?.moneyPlan?.addAccount.__typename === 'ApplicationError') {
        throw new Error(data.moneyPlan.addAccount.message);
      }
      
      await refetchDraftQuery();
      
      return data?.moneyPlan?.addAccount.data;
    } catch (error) {
      if (error instanceof Error) {
        const errorMessage = `Failed to add account to plan: ${error.message}`;
        setError(errorMessage);
        toast({
          variant: "destructive",
          title: "Error",
          description: errorMessage
        });
      }
      throw error;
    }
  };

  const updatePlanAccount = async (planId: string, accountId: string, buckets: BucketConfigInput[]) => {
    try {
      const { data } = await updatePlanAccountMutation({
        variables: { planId, accountId, buckets }
      });
      
      if (data?.moneyPlan?.changeAccountConfiguration.__typename === 'ApplicationError') {
        throw new Error(data.moneyPlan.changeAccountConfiguration.message);
      }
      
      await refetchDraftQuery();
      
      return data?.moneyPlan?.changeAccountConfiguration.data;
    } catch (error) {
      if (error instanceof Error) {
        const errorMessage = `Failed to update plan account: ${error.message}`;
        setError(errorMessage);
        toast({
          variant: "destructive",
          title: "Error",
          description: errorMessage
        });
      }
      throw error;
    }
  };

  const removeAccountFromPlan = async (planId: string, accountId: string) => {
    try {
      const { data } = await removeAccountFromPlanMutation({
        variables: { planId, accountId }
      });
      
      if (data?.moneyPlan?.removeAccount.__typename === 'ApplicationError') {
        throw new Error(data.moneyPlan.removeAccount.message);
      }
      
      await refetchDraftQuery();
      
      toast({
        title: "Success",
        description: "Account successfully removed from plan"
      });
      
      return data?.moneyPlan?.removeAccount.data;
    } catch (error) {
      if (error instanceof Error) {
        const errorMessage = `Failed to remove account from plan: ${error.message}`;
        setError(errorMessage);
        toast({
          variant: "destructive",
          title: "Error",
          description: errorMessage
        });
      }
      throw error;
    }
  };

  const updatePlanAccountNotes = async (planId: string, accountId: string, notes: string) => {
    try {
      const { data } = await updatePlanAccountNotesMutation({
        variables: { planId, accountId, notes }
      });
      
      if (data?.moneyPlan?.editAccountNotes.__typename === 'ApplicationError') {
        throw new Error(data.moneyPlan.editAccountNotes.message);
      }
      
      await refetchDraftQuery();
      
      toast({
        title: "Success",
        description: "Account notes updated successfully"
      });
      
      return data?.moneyPlan?.editAccountNotes.data;
    } catch (error) {
      if (error instanceof Error) {
        const errorMessage = `Failed to update plan account notes: ${error.message}`;
        setError(errorMessage);
        toast({
          variant: "destructive",
          title: "Error",
          description: errorMessage
        });
      }
      throw error;
    }
  };

  const updatePlanNotes = async (planId: string, notes: string) => {
    try {
      const { data } = await updatePlanNotesMutation({
        variables: { planId, notes }
      });
      
      if (data?.moneyPlan?.editPlanNotes.__typename === 'ApplicationError') {
        throw new Error(data.moneyPlan.editPlanNotes.message);
      }
      
      await refetchDraftQuery();
      
      toast({
        title: "Success",
        description: "Plan notes updated successfully"
      });
      
      return data?.moneyPlan?.editPlanNotes.data;
    } catch (error) {
      if (error instanceof Error) {
        const errorMessage = `Failed to update plan notes: ${error.message}`;
        setError(errorMessage);
        toast({
          variant: "destructive",
          title: "Error",
          description: errorMessage
        });
      }
      throw error;
    }
  };

  const toggleAccountCheck = async (planId: string, accountId: string) => {
    try {
      const account = draftPlan?.accounts?.find(acc => acc.id === accountId);
      if (!account) {
        throw new Error("Account not found");
      }
      
      // Implement toggle account checked state (add mutation if available)
      // For now, mock implementation
      console.log(`Toggling check for account ${accountId} in plan ${planId}`);
      
      await refetchDraftQuery();
    } catch (error) {
      if (error instanceof Error) {
        const errorMessage = `Failed to toggle account check: ${error.message}`;
        setError(errorMessage);
        toast({
          variant: "destructive",
          title: "Error",
          description: errorMessage
        });
      }
      throw error;
    }
  };

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
  
  const refetchDraft = useCallback(async () => {
    try {
      await refetchDraftQuery();
    } catch (error) {
      if (error instanceof Error) {
        const errorMessage = `Failed to refetch draft plan: ${error.message}`;
        setError(errorMessage);
        toast({
          variant: "destructive",
          title: "Error",
          description: errorMessage
        });
      }
    }
  }, [refetchDraftQuery, toast]);

  return {
    plans,
    draftPlan,
    loading: plansLoading || draftPlanLoading,
    error,
    createPlan,
    updatePlan,
    commitPlan,
    archivePlan,
    addAccountToPlan,
    updatePlanAccount,
    removeAccountFromPlan,
    updatePlanAccountNotes,
    updatePlanNotes,
    toggleAccountCheck,
    refetchPlans,
    refetchDraft,
  };
} 