'use client';

import { useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@apollo/client';
import { GET_PLANS } from '@/lib/graphql/operations';
import { usePagination } from '@/lib/hooks/usePagination';
import { formatCurrency, formatDate } from '@/lib/utils/format';
import Link from 'next/link';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PlusCircle, Loader2, ChevronLeft, ChevronRight } from 'lucide-react';
import { Plan } from '@/lib/hooks/usePlans';

export default function PlansListPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const pagination = usePagination<Plan>(5); // Show 5 plans per page

  // Redirect to login if not authenticated
  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin?callbackUrl=/plans');
    }
  }, [status, router]);

  const { data, loading, error } = useQuery(GET_PLANS, {
    variables: pagination.variables,
    skip: !session,
    onCompleted: (data) => {
      if (data?.moneyPlans?.pageInfo) {
        pagination.updatePageInfo(data.moneyPlans.pageInfo);
      }
    },
  });

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
                              <p className="font-medium">{account.account.name}</p>
                              <p className="text-sm font-bold">
                                {formatCurrency(account.buckets.reduce((sum, bucket) => sum + bucket.allocatedAmount, 0))}
                              </p>
                            </div>
                            {account.buckets.length > 0 && (
                              <div className="mt-1 pl-4 space-y-1">
                                {account.buckets.map((bucket) => (
                                  <div key={bucket.id} className="flex justify-between items-center text-sm">
                                    <p className="text-muted-foreground">{bucket.name}</p>
                                    <p>{formatCurrency(bucket.allocatedAmount)}</p>
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