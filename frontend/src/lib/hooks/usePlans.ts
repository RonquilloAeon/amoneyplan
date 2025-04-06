import { useState } from 'react';
import { useMutation, useQuery } from '@apollo/client';
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
  TOGGLE_ACCOUNT_CHECK,
} from '@/lib/graphql/operations';
import { Plan, CreatePlanInput, UpdatePlanInput, CreateBucketInput, UpdateBucketInput, PlanAccount } from '@/lib/graphql/types';

export const usePlans = () => {
  const [error, setError] = useState<string | null>(null);

  // Query for all plans
  const { data: plansData, loading: plansLoading, refetch: refetchPlans } = useQuery(GET_PLANS);
  
  // Query for draft plan
  const { data: draftData, loading: draftLoading, refetch: refetchDraft } = useQuery(GET_DRAFT_PLAN);

  // Mutations
  const [createPlan] = useMutation(CREATE_PLAN, {
    onCompleted: () => {
      refetchDraft();
      refetchPlans();
    },
    onError: (error) => {
      setError(error.message);
    },
  });

  const [updatePlan] = useMutation(UPDATE_PLAN, {
    onCompleted: () => {
      refetchDraft();
      refetchPlans();
    },
    onError: (error) => {
      setError(error.message);
    },
  });

  const [commitPlan] = useMutation(COMMIT_PLAN, {
    onCompleted: () => {
      refetchDraft();
      refetchPlans();
    },
    onError: (error) => {
      setError(error.message);
    },
  });

  const [archivePlan] = useMutation(ARCHIVE_PLAN, {
    onCompleted: () => {
      refetchDraft();
      refetchPlans();
    },
    onError: (error) => {
      setError(error.message);
    },
  });

  const [addAccountToPlan] = useMutation(ADD_ACCOUNT_TO_PLAN, {
    onCompleted: () => {
      refetchDraft();
    },
    onError: (error) => {
      setError(error.message);
    },
  });

  const [updatePlanAccount] = useMutation(UPDATE_PLAN_ACCOUNT, {
    onCompleted: () => {
      refetchDraft();
    },
    onError: (error) => {
      setError(error.message);
    },
  });

  const [removeAccountFromPlan] = useMutation(REMOVE_ACCOUNT_FROM_PLAN, {
    onCompleted: () => {
      refetchDraft();
    },
    onError: (error) => {
      setError(error.message);
    },
  });

  const [updatePlanAccountNotes] = useMutation(UPDATE_PLAN_ACCOUNT_NOTES, {
    onCompleted: () => {
      refetchDraft();
    },
    onError: (error) => {
      setError(error.message);
    },
  });

  const [updatePlanNotes] = useMutation(UPDATE_PLAN_NOTES, {
    onCompleted: () => {
      refetchDraft();
    },
    onError: (error) => {
      setError(error.message);
    },
  });

  const [toggleAccountCheck] = useMutation(TOGGLE_ACCOUNT_CHECK, {
    onCompleted: () => {
      refetchDraft();
    },
    onError: (error) => {
      setError(error.message);
    },
  });

  // Handler functions
  const handleCreatePlan = async (input: CreatePlanInput) => {
    try {
      await createPlan({
        variables: { input },
      });
      setError(null);
    } catch (error) {
      // Error is handled by onError callback
    }
  };

  const handleUpdatePlan = async (id: string, input: UpdatePlanInput) => {
    try {
      await updatePlan({
        variables: { id, input },
      });
      setError(null);
    } catch (error) {
      // Error is handled by onError callback
    }
  };

  const handleCommitPlan = async (id: string) => {
    try {
      await commitPlan({
        variables: { id },
      });
      setError(null);
    } catch (error) {
      // Error is handled by onError callback
    }
  };

  const handleArchivePlan = async (id: string) => {
    try {
      await archivePlan({
        variables: { id },
      });
      setError(null);
    } catch (error) {
      // Error is handled by onError callback
    }
  };

  const handleAddAccountToPlan = async (planId: string, accountId: string, buckets: CreateBucketInput[]) => {
    try {
      await addAccountToPlan({
        variables: { planId, accountId, buckets },
      });
      setError(null);
    } catch (error) {
      // Error is handled by onError callback
    }
  };

  const handleUpdatePlanAccount = async (planId: string, planAccountId: string, buckets: UpdateBucketInput[]) => {
    try {
      await updatePlanAccount({
        variables: { planId, planAccountId, buckets },
      });
      setError(null);
    } catch (error) {
      // Error is handled by onError callback
    }
  };

  const handleRemoveAccountFromPlan = async (planId: string, planAccountId: string) => {
    try {
      await removeAccountFromPlan({
        variables: { planId, planAccountId },
      });
      setError(null);
    } catch (error) {
      // Error is handled by onError callback
    }
  };

  const handleUpdatePlanAccountNotes = async (planId: string, planAccountId: string, notes: string) => {
    try {
      await updatePlanAccountNotes({
        variables: { planId, planAccountId, notes },
      });
      setError(null);
    } catch (error) {
      // Error is handled by onError callback
    }
  };

  const handleUpdatePlanNotes = async (planId: string, notes: string) => {
    try {
      await updatePlanNotes({
        variables: { planId, notes },
      });
      setError(null);
    } catch (error) {
      // Error is handled by onError callback
    }
  };

  const handleToggleAccountCheck = async (planId: string, planAccountId: string) => {
    try {
      await toggleAccountCheck({
        variables: { planId, planAccountId },
      });
      setError(null);
    } catch (error) {
      // Error is handled by onError callback
    }
  };

  return {
    plans: plansData?.plans || [],
    draftPlan: draftData?.draftPlan || null,
    loading: plansLoading || draftLoading,
    error,
    createPlan: handleCreatePlan,
    updatePlan: handleUpdatePlan,
    commitPlan: handleCommitPlan,
    archivePlan: handleArchivePlan,
    addAccountToPlan: handleAddAccountToPlan,
    updatePlanAccount: handleUpdatePlanAccount,
    removeAccountFromPlan: handleRemoveAccountFromPlan,
    updatePlanAccountNotes: handleUpdatePlanAccountNotes,
    updatePlanNotes: handleUpdatePlanNotes,
    toggleAccountCheck: handleToggleAccountCheck,
    refetchPlans,
    refetchDraft,
  };
}; 