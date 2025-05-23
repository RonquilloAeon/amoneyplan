'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@apollo/client';
import { GET_PLANS, SET_ACCOUNT_CHECKED_STATE } from '@/lib/graphql/operations';
import { usePagination } from '@/lib/hooks/usePagination';
import { formatCurrency, formatDate } from '@/lib/utils/format';
import { useToast } from '@/lib/hooks/useToast';
import Link from 'next/link';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PlusCircle, Loader2, ChevronLeft, ChevronRight, Check, X } from 'lucide-react';
import { Checkbox } from '@/components/ui/checkbox';
import { Plan } from '@/lib/hooks/usePlans';
import { EmptyState } from '@/components/EmptyState';
import { MoneyPlanGraphic } from '@/components/EmptyStateGraphics';

export default function PlansListPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const pagination = usePagination<Plan>(5); // Show 5 plans per page
  const { toast } = useToast();
  const [checkingAccount, setCheckingAccount] = useState<{ planId: string, accountId: string } | null>(null);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin?callbackUrl=/plans');
    }
  }, [status, router]);

  const { data, loading, error, refetch } = useQuery(GET_PLANS, {
    variables: pagination.variables,
    skip: !session,
    onCompleted: (data) => {
      if (data?.moneyPlans?.pageInfo) {
        pagination.updatePageInfo(data.moneyPlans.pageInfo);
      }
      
      // Log all plans and their accounts for debugging
      if (data?.moneyPlans?.edges) {
        console.log("Plans loaded:", data.moneyPlans.edges.length);
        data.moneyPlans.edges.forEach((edge, i) => {
          const plan = edge.node;
          console.log(`Plan ${i + 1} (${plan.id}):`, {
            isCommitted: plan.isCommitted,
            accounts: plan.accounts.map(acc => ({
              planAccountId: acc.id,
              accountId: acc.account.id,
              name: acc.account.name,
              isChecked: acc.isChecked
            }))
          });
        });
      }
    },
  });

  // Debug effect to monitor plan accounts
  useEffect(() => {
    if (data?.moneyPlans?.edges) {
      const allPlans = data.moneyPlans.edges.map(edge => edge.node);
      const accountsInMultiplePlans: Record<string, Array<{planId: string, planAccountId: string, isChecked: boolean}>> = {};
      
      // Build a map of base account IDs to all plans they appear in
      allPlans.forEach(plan => {
        plan.accounts.forEach(planAccount => {
          const baseAccountId = planAccount.account.id;
          if (!accountsInMultiplePlans[baseAccountId]) {
            accountsInMultiplePlans[baseAccountId] = [];
          }
          accountsInMultiplePlans[baseAccountId].push({
            planId: plan.id,
            planAccountId: planAccount.id,
            isChecked: planAccount.isChecked
          });
        });
      });
      
      // Log accounts that appear in multiple plans
      Object.entries(accountsInMultiplePlans)
        .filter(([_, plans]) => plans.length > 1)
        .forEach(([baseAccountId, plans]) => {
          console.log(`Account ${baseAccountId} appears in ${plans.length} plans:`);
          plans.forEach(p => {
            console.log(`  Plan ${p.planId}: PlanAccount ${p.planAccountId}, isChecked: ${p.isChecked}`);
          });
        });
    }
  }, [data]);

  const [setAccountCheckedState] = useMutation(SET_ACCOUNT_CHECKED_STATE, {
    onCompleted: (data) => {
      console.log("Mutation completed:", data);
      // Check the actual typename returned by your backend mutation (e.g., 'Success', 'EmptySuccess')
      const result = data?.moneyPlan?.setAccountCheckedState;

      if (result?.__typename?.includes('Success')) { // Check if typename indicates success
        const message = result.message;
        console.log("Success response message:", message);

        toast({
          title: 'Success',
          description: message || 'Account state updated.', // Use message from response
          variant: 'success', // Add success variant
        });
        console.log("Refetching plans data after successful update");
        refetch(); // Refetch to get confirmed data
      } else if (result?.__typename === 'ApplicationError') {
        const errorMessage = result.message;
        console.error("Mutation error:", errorMessage);
        toast({
          variant: 'destructive',
          title: 'Error',
          description: errorMessage,
        });
      }
      setCheckingAccount(null);
    },
    onError: (error) => {
      console.error("Mutation error:", error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: `Failed to update account: ${error.message}`,
      });
      setCheckingAccount(null);
    },
  });

  const handleToggleChecked = async (planId: string, planAccountId: string, underlyingAccountId: string, currentCheckedState: boolean) => {
    console.log("Toggle checked for plan:", planId);
    console.log("Toggle checked for PlanAccount ID:", planAccountId);
    console.log("Toggle checked for Underlying Account ID:", underlyingAccountId);
    console.log("Current checked state:", currentCheckedState);
    
    // Use planAccountId for UI disabling state, but underlyingAccountId for the mutation
    setCheckingAccount({ planId, accountId: planAccountId });
    
    const newState = !currentCheckedState;
    
    // Find the current plan and account data for optimistic update
    const currentPlan = data?.moneyPlans?.edges.find(edge => edge.node.id === planId)?.node;
    const currentAccount = currentPlan?.accounts.find(a => a.id === planAccountId);
    
    // Prepare optimistic accounts data
    const optimisticAccounts = currentPlan?.accounts.map(acc => {
        if (acc.id === planAccountId) {
            return {
                ...acc,
                isChecked: newState, // Optimistically update the checked state
                __typename: "PlanAccount" // Ensure typename is provided
            };
        }
        return { ...acc, __typename: "PlanAccount"}; // Ensure typename for others
    }) || [];
    
    // Ensure nested account and buckets also have typenames if needed by cache
    optimisticAccounts.forEach(acc => {
      acc.account = { ...acc.account, __typename: "Account" };
      acc.buckets = acc.buckets.map(b => ({ ...b, __typename: "Bucket" }));
    });

    try {
      await setAccountCheckedState({
        variables: {
          planId,
          accountId: underlyingAccountId, // Pass underlying account ID
          isChecked: newState
        },
        // Optimistic response structure now reflects the simpler backend return
        optimisticResponse: {
          moneyPlan: {
            __typename: "MoneyPlanMutations",
            setAccountCheckedState: {
              // Adjust __typename if your backend uses 'Success' with only a message, etc.
              __typename: "EmptySuccess", // Assuming backend returns EmptySuccess type now
              message: `Account ${newState ? 'checked' : 'unchecked'} optimistically.`, // Optimistic message
              // No 'data' field if using EmptySuccess
            }
          }
        }
      });
    } catch (error) {
      // Error is handled in the onError callback
    }
  };

  const plans = data?.moneyPlans?.edges?.map(edge => edge.node) || [];

  // Show loading when checking authentication
  if (status === 'loading' || loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
          <p className="text-lg font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render anything until authentication is checked
  if (status !== 'authenticated') {
    return null;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold text-red-500">Error</h2>
          <p className="text-muted-foreground">{error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Your Money Plans</h1>
        <Link href="/new">
          <Button>
            <PlusCircle className="mr-2 h-4 w-4" />
            New Plan
          </Button>
        </Link>
      </div>

      {plans.length === 0 ? (
        <EmptyState 
          graphic={<MoneyPlanGraphic />}
          title="You don't have any plans yet"
          description={[
            "Money plans help you allocate funds across your accounts without rigid budgeting. Create a plan to distribute your money where you need it, track what's been handled, and see what's left to allocate.",
            "A great time to create a plan is when you have a large amount of money to allocate or after each pay period."
          ]}
          actionInstruction="Click the"
          actionInstructionHighlight='"New Plan"'
        />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-6">
            {plans.map((plan) => (
              <Card key={plan.id} className="shadow-sm hover:shadow-md transition-shadow">
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-xl">{formatDate(plan.planDate)}</CardTitle>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant={plan.isCommitted ? "default" : "outline"} className={plan.isCommitted ? "bg-green-500 hover:bg-green-600" : ""}>
                      {plan.isCommitted ? 'Committed' : 'Draft'}
                    </Badge>
                    {plan.isArchived && (
                      <Badge variant="secondary">Archived</Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Initial Balance</p>
                      <p className="text-2xl font-bold">{formatCurrency(plan.initialBalance)}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Remaining Balance</p>
                      <p className="text-2xl font-bold">{formatCurrency(plan.remainingBalance)}</p>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <h4 className="font-medium">Accounts</h4>
                    {plan.accounts.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No accounts added yet</p>
                    ) : (
                      <div className="divide-y">
                        {plan.accounts.map((account) => (
                          <div key={account.id} className="py-2">
                            <div className="flex justify-between items-center">
                              <div className="flex items-center gap-2">
                                <div className="flex items-center h-5">
                                  <Checkbox
                                    id={`account-${plan.id}-${account.id}`}
                                    checked={account.isChecked}
                                    disabled={
                                      plan.isArchived || 
                                      // Disable based on PlanAccount ID
                                      (checkingAccount?.planId === plan.id && checkingAccount?.accountId === account.id)
                                    }
                                    onCheckedChange={() => {
                                      console.log(`Checkbox clicked for PlanAccount [${account.id}]`);
                                      console.log(`Current isChecked state: ${account.isChecked}`);
                                      console.log(`Parent Plan ID: ${plan.id}`);
                                      // Pass PlanAccount ID, Underlying Account ID, and current state
                                      handleToggleChecked(plan.id, account.id, account.account.id, account.isChecked);
                                    }}
                                    className="data-[state=checked]:bg-green-500 data-[state=checked]:text-white"
                                  />
                                </div>
                                <label 
                                  htmlFor={`account-${plan.id}-${account.id}`}
                                  className={`font-medium ${account.isChecked ? 'line-through text-muted-foreground' : ''}`}
                                >
                                  {account.account.name}
                                </label>
                                {checkingAccount?.planId === plan.id && checkingAccount?.accountId === account.id && (
                                  <Loader2 className="h-4 w-4 animate-spin ml-2" />
                                )}
                              </div>
                              <p className="text-sm font-bold">
                                {formatCurrency(account.buckets.reduce((sum, bucket) => sum + bucket.allocatedAmount, 0))}
                              </p>
                            </div>
                            {account.buckets.length > 0 && (
                              <div className="mt-1 pl-10 space-y-1">
                                {account.buckets.map((bucket) => (
                                  <div key={bucket.id} className="flex justify-between items-center text-sm">
                                    <p className="text-muted-foreground">{bucket.name}</p>
                                    <p className="font-medium">{formatCurrency(bucket.allocatedAmount)}</p>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </CardContent>
                <CardFooter className="flex justify-end">
                  <Link href={plan.isCommitted ? `/plans/${plan.id}` : "/new"}>
                    <Button variant="outline">
                      {plan.isCommitted ? 'View Details' : 'Continue Editing'}
                    </Button>
                  </Link>
                </CardFooter>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
