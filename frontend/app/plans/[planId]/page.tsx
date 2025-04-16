'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@apollo/client';
import { GET_PLAN, ARCHIVE_PLAN, SET_ACCOUNT_CHECKED_STATE } from '@/lib/graphql/operations';
import { formatCurrency, formatDate } from '@/lib/utils/format';
import { useToast } from '@/lib/hooks/useToast';
import { Plan } from '@/lib/hooks/usePlans';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, Archive, ArrowLeft, Loader2 } from 'lucide-react';
import { Checkbox } from '@/components/ui/checkbox';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

export default function PlanDetailsPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const params = useParams();
  const { toast } = useToast();
  const encodedPlanId = params.planId as string;
  const planId = decodeURIComponent(encodedPlanId);
  const [isArchiving, setIsArchiving] = useState(false);
  const [checkingAccount, setCheckingAccount] = useState<string | null>(null);
  
  // For debugging
  useEffect(() => {
    console.log('Encoded ID:', encodedPlanId);
    console.log('Decoded ID:', planId);
  }, [encodedPlanId, planId]);
  
  // Redirect to login if not authenticated
  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin?callbackUrl=' + encodeURIComponent(`/plans/${encodedPlanId}`));
    }
  }, [status, router, encodedPlanId]);
  
  const { data, loading, error, refetch } = useQuery(GET_PLAN, {
    variables: { id: planId },
    skip: !session || !planId,
  });
  
  const plan: Plan = data?.moneyPlan;
  
  const [archivePlanMutation] = useMutation(ARCHIVE_PLAN);
  
  const [setAccountCheckedState] = useMutation(SET_ACCOUNT_CHECKED_STATE, {
    onCompleted: (data) => {
      console.log("Detail page mutation completed:", data);
      const result = data?.moneyPlan?.setAccountCheckedState;

      if (result?.__typename?.includes('Success')) {
        const message = result.message;
        console.log("Success response message:", message);
        
        toast({
          title: 'Success',
          description: message || 'Account state updated.',
          variant: 'success',
        });
        refetch();
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
      toast({
        variant: 'destructive',
        title: 'Error',
        description: `Failed to update account: ${error.message}`,
      });
      setCheckingAccount(null);
    },
  });
  
  const handleToggleChecked = async (planAccountId: string, underlyingAccountId: string, currentCheckedState: boolean) => {
    if (!planId) return;
    
    console.log("Toggle checked for PlanAccount ID:", planAccountId);
    console.log("Toggle checked for Underlying Account ID:", underlyingAccountId);
    console.log("Current checked state:", currentCheckedState);
    
    setCheckingAccount(planAccountId);
    
    const newState = !currentCheckedState;
    
    const optimisticAccounts = plan?.accounts.map(acc => {
        if (acc.id === planAccountId) {
            return {
                ...acc,
                isChecked: newState, 
                __typename: "PlanAccount"
            };
        }
        return { ...acc, __typename: "PlanAccount"};
    }) || [];
    
    optimisticAccounts.forEach(acc => {
      acc.buckets = acc.buckets.map(b => ({ ...b, __typename: "Bucket" }));
    });

    try {
      await setAccountCheckedState({
        variables: {
          planId,
          accountId: underlyingAccountId,
          isChecked: newState
        },
        optimisticResponse: {
          moneyPlan: {
            __typename: "MoneyPlanMutations", 
            setAccountCheckedState: {
              __typename: "EmptySuccess",
              message: `Account ${newState ? 'checked' : 'unchecked'} optimistically.`,
            }
          }
        }
      });
    } catch (error) {
      // Error is handled in the onError callback
    }
  };
  
  const handleArchivePlan = async () => {
    if (!planId) return;
    
    setIsArchiving(true);
    try {
      const response = await archivePlanMutation({
        variables: { id: planId }
      });
      
      if (response.data?.moneyPlan?.archivePlan.__typename === 'ApplicationError') {
        throw new Error(response.data.moneyPlan.archivePlan.message);
      }
      
      toast({
        title: "Success",
        description: "Plan successfully archived",
      });
      
      // Redirect back to plans list
      router.push('/plans');
    } catch (error) {
      let errorMessage = "Failed to archive plan";
      if (error instanceof Error) {
        errorMessage = `${errorMessage}: ${error.message}`;
      }
      
      toast({
        variant: "destructive",
        title: "Error",
        description: errorMessage,
      });
    } finally {
      setIsArchiving(false);
    }
  };
  
  // Show loading when checking authentication or fetching data
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
      <div className="space-y-6">
        <div className="flex items-center">
          <Button variant="ghost" size="sm" onClick={() => router.push('/plans')} className="mr-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Plans
          </Button>
        </div>
        
        <div className="flex flex-col items-center justify-center min-h-[40vh] space-y-4">
          <AlertCircle className="h-12 w-12 text-red-500" />
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-bold text-red-500">Error</h2>
            <p className="text-muted-foreground">{error.message}</p>
          </div>
        </div>
      </div>
    );
  }
  
  if (!plan) {
    return (
      <div className="space-y-6">
        <div className="flex items-center">
          <Button variant="ghost" size="sm" onClick={() => router.push('/plans')} className="mr-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Plans
          </Button>
        </div>
        
        <div className="flex flex-col items-center justify-center min-h-[40vh] space-y-4">
          <AlertCircle className="h-12 w-12 text-yellow-500" />
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-bold">Plan Not Found</h2>
            <p className="text-muted-foreground">The requested plan could not be found.</p>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Button variant="ghost" size="sm" onClick={() => router.push('/plans')} className="mr-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Plans
        </Button>
        
        {!plan.isArchived && (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" className="bg-white">
                <Archive className="h-4 w-4 mr-2" />
                Archive Plan
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Archive Money Plan</AlertDialogTitle>
                <AlertDialogDescription>
                  Are you sure you want to archive this plan? This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction 
                  onClick={handleArchivePlan}
                  disabled={isArchiving}
                  className={isArchiving ? "opacity-70 cursor-not-allowed" : ""}
                >
                  {isArchiving ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Archiving...
                    </>
                  ) : (
                    "Archive"
                  )}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}
      </div>
      
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Plan Details</h1>
          <div className="flex items-center space-x-2">
            <Badge variant={plan.isCommitted ? "default" : "outline"} className={plan.isCommitted ? "bg-green-500 hover:bg-green-600" : ""}>
              {plan.isCommitted ? 'Committed' : 'Draft'}
            </Badge>
            {plan.isArchived && (
              <Badge variant="secondary">Archived</Badge>
            )}
          </div>
        </div>
        
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle>Summary</CardTitle>
            <CardDescription>
              Created on {formatDate(plan.createdAt)}
              {plan.planDate && ` • Planned for ${formatDate(plan.planDate)}`}
              {plan.archivedAt && ` • Archived on ${formatDate(plan.archivedAt)}`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-1">Initial Balance</h3>
                <p className="text-3xl font-bold">{formatCurrency(plan.initialBalance)}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-1">Remaining Balance</h3>
                <p className="text-3xl font-bold">{formatCurrency(plan.remainingBalance)}</p>
              </div>
            </div>
            
            {plan.notes && (
              <div className="mt-6">
                <h3 className="text-sm font-medium text-muted-foreground mb-2">Notes</h3>
                <div className="bg-gray-50 p-4 rounded-md whitespace-pre-wrap">
                  {plan.notes}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
        
        <div>
          <h2 className="text-2xl font-bold mb-4">Accounts</h2>
          
          {plan.accounts.length === 0 ? (
            <div className="text-center py-12 border rounded-lg bg-gray-50">
              <h3 className="text-lg font-medium mb-2">No accounts added</h3>
              <p className="text-muted-foreground">This plan doesn't have any accounts configured.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {plan.accounts.map((account) => (
                <Card key={account.id} className="shadow-sm">
                  <CardHeader className="py-4">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-2">
                        <div className="flex items-center h-5">
                          <Checkbox
                            id={`account-${planId}-${account.id}`}
                            checked={account.isChecked}
                            disabled={plan.isArchived || checkingAccount === account.id}
                            onCheckedChange={() => {
                              console.log(`Detail page: Checkbox clicked for PlanAccount [${account.id}]`);
                              console.log(`Current isChecked state: ${account.isChecked}`);
                              console.log(`Plan ID: ${planId}`);
                              handleToggleChecked(account.id, account.account.id, account.isChecked);
                            }}
                            className="data-[state=checked]:bg-green-500 data-[state=checked]:text-white"
                          />
                        </div>
                        <CardTitle 
                          className={`text-lg ${account.isChecked ? 'line-through text-muted-foreground' : ''}`}
                        >
                          {account.account.name}
                        </CardTitle>
                        {checkingAccount === account.id && (
                          <Loader2 className="h-4 w-4 animate-spin ml-2" />
                        )}
                      </div>
                      <p className="text-xl font-bold">
                        {formatCurrency(account.buckets.reduce((sum, bucket) => sum + bucket.allocatedAmount, 0))}
                      </p>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {account.notes && (
                      <div className="mb-4">
                        <h4 className="text-sm font-medium text-muted-foreground mb-1">Notes</h4>
                        <div className="bg-gray-50 p-3 rounded-md text-sm">
                          {account.notes}
                        </div>
                      </div>
                    )}
                    
                    {account.buckets.length > 0 ? (
                      <div>
                        <h4 className="text-sm font-medium text-muted-foreground mb-2">Allocations</h4>
                        <div className="space-y-2">
                          {account.buckets.map((bucket) => (
                            <div key={bucket.id} className="flex justify-between items-center p-2 border-b last:border-b-0">
                              <div>
                                <p className={`font-medium ${account.isChecked ? 'line-through text-muted-foreground' : ''}`}>
                                  {bucket.name}
                                </p>
                                <p className="text-xs text-muted-foreground">{bucket.category}</p>
                              </div>
                              <p className={`font-semibold ${account.isChecked ? 'text-muted-foreground' : ''}`}>
                                {formatCurrency(bucket.allocatedAmount)}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">No allocations for this account</p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 