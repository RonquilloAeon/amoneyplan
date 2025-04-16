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
      if (data?.moneyPlan?.setAccountCheckedState.__typename === 'Success') {
        const successData = data.moneyPlan.setAccountCheckedState.data;
        console.log("Success response data:", successData);
        console.log("Updated accounts:", successData.accounts.map(acc => ({
          planAccountId: acc.id,
          isChecked: acc.isChecked,
          name: acc.account.name
        })));
        
        toast({
          title: 'Success',
          description: data.moneyPlan.setAccountCheckedState.message,
        });
        console.log("Refetching plans data after successful update");
        refetch();
      } else if (data?.moneyPlan?.setAccountCheckedState.__typename === 'ApplicationError') {
        console.error("Mutation error:", data.moneyPlan.setAccountCheckedState.message);
        toast({
          variant: 'destructive',
          title: 'Error',
          description: data.moneyPlan.setAccountCheckedState.message,
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
    update: (cache, { data }) => {
      if (data?.moneyPlan?.setAccountCheckedState.__typename === 'Success') {
        // The backend returns the updated plan, but the cache holds multiple plans,
        // so we need to update the specific plan and account that was changed
        try {
          const updatedPlan = data.moneyPlan.setAccountCheckedState.data;
          const currentPlansData = cache.readQuery({
            query: GET_PLANS,
            variables: pagination.variables
          }) as any; // Use any temporarily to bypass TypeScript constraints
          
          if (currentPlansData?.moneyPlans) {
            console.log("Updating cache with new checked state");
            // Create a new copy of the plans data with the updated account
            const updatedEdges = currentPlansData.moneyPlans.edges.map(edge => {
              if (edge.node.id === updatedPlan.id) {
                // This is the plan that was updated
                console.log("Found plan to update in cache:", edge.node.id);
                return {
                  ...edge,
                  node: {
                    ...edge.node,
                    accounts: updatedPlan.accounts
                  }
                };
              }
              return edge;
            });
            
            // Write back the updated query result
            cache.writeQuery({
              query: GET_PLANS,
              variables: pagination.variables,
              data: {
                moneyPlans: {
                  ...currentPlansData.moneyPlans,
                  edges: updatedEdges
                }
              }
            });
          }
        } catch (err) {
          console.error("Error updating cache:", err);
        }
      }
    }
  });

  const handleToggleChecked = async (planId: string, accountId: string, currentCheckedState: boolean) => {
    console.log("Toggle checked for plan:", planId);
    console.log("Toggle checked for PlanAccount ID:", accountId);
    console.log("Current checked state:", currentCheckedState);
    
    setCheckingAccount({ planId, accountId });
    
    // Create optimistic response to provide immediate feedback
    const newState = !currentCheckedState;
    
    try {
      await setAccountCheckedState({
        variables: {
          planId,
          accountId,
          isChecked: newState
        },
        optimisticResponse: {
          moneyPlan: {
            setAccountCheckedState: {
              __typename: "Success",
              message: `Account ${newState ? 'checked' : 'unchecked'} successfully.`,
              data: {
                // We'll ignore this data since we're doing an immediate refetch anyway
                id: planId,
                accounts: []
              }
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
        <h1 className="text-3xl font-bold">Money Plans</h1>
        <Link href="/new">
          <Button>
            <PlusCircle className="mr-2 h-4 w-4" />
            New Plan
          </Button>
        </Link>
      </div>

      {plans.length === 0 ? (
        <div className="text-center py-12 border rounded-lg bg-gray-50">
          <h3 className="text-lg font-medium mb-2">No plans found</h3>
          <p className="text-muted-foreground mb-4">Start by creating your first money plan.</p>
          <Link href="/new">
            <Button>
              <PlusCircle className="mr-2 h-4 w-4" />
              Create Plan
            </Button>
          </Link>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-6">
            {plans.map((plan) => (
              <Card key={plan.id} className="shadow-sm hover:shadow-md transition-shadow">
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-xl">{formatDate(plan.createdAt)}</CardTitle>
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
                                      (checkingAccount?.planId === plan.id && checkingAccount?.accountId === account.id)
                                    }
                                    onCheckedChange={() => {
                                      console.log(`Checkbox clicked for PlanAccount [${account.id}]`);
                                      console.log(`Current isChecked state: ${account.isChecked}`);
                                      console.log(`Parent Plan ID: ${plan.id}`);
                                      handleToggleChecked(plan.id, account.id, account.isChecked);
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
                                    <p className={`text-muted-foreground ${account.isChecked ? 'line-through' : ''}`}>
                                      {bucket.name}
                                    </p>
                                    <p className={account.isChecked ? 'text-muted-foreground' : ''}>
                                      {formatCurrency(bucket.allocatedAmount)}
                                    </p>
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

          {/* Pagination */}
          <div className="flex justify-center space-x-2 mt-6">
            <Button 
              variant="outline" 
              size="sm"
              onClick={pagination.handlePreviousPage}
              disabled={!pagination.pageInfo.hasPreviousPage}
            >
              <ChevronLeft className="h-4 w-4 mr-2" />
              Previous
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={pagination.handleNextPage}
              disabled={!pagination.pageInfo.hasNextPage}
            >
              Next
              <ChevronRight className="h-4 w-4 ml-2" />
            </Button>
          </div>
        </>
      )}
    </div>
  );
} 