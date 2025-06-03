'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery } from '@apollo/client';
import { GET_SHARED_PLAN } from '@/lib/graphql/operations';
import { formatCurrency, formatDate } from '@/lib/utils/format';
import { Plan } from '@/lib/hooks/usePlans';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, ArrowLeft, Loader2 } from 'lucide-react';

export default function SharedPlanPage() {
  const router = useRouter();
  const params = useParams();
  const token = params.token as string;
  
  const { data, loading, error } = useQuery(GET_SHARED_PLAN, {
    variables: { token },
  });
  
  const plan: Plan = data?.sharedPlan;
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
          <p className="text-lg font-medium">Loading shared plan...</p>
        </div>
      </div>
    );
  }
  
  if (error || !plan) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col items-center justify-center min-h-[40vh] space-y-4">
          <AlertCircle className="h-12 w-12 text-red-500" />
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-bold text-red-500">
              {error ? 'Error' : 'Shared Plan Not Found'}
            </h2>
            <p className="text-muted-foreground">
              {error ? error.message : 'This shared plan link may be invalid or expired.'}
            </p>
            <Button 
              variant="outline" 
              className="mt-4"
              onClick={() => router.push('/')}
            >
              Go to Homepage
            </Button>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Shared Money Plan</h1>
        <Badge variant="outline" className="text-blue-600 border-blue-600">
          Shared Plan
        </Badge>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Plan from {formatDate(plan.planDate || plan.createdAt)}</CardTitle>
          <CardDescription>
            {plan.isCommitted ? 'Committed' : 'Draft'} 
            {plan.isArchived && ' • Archived'}
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {plan.notes && (
            <div className="bg-muted p-4 rounded-md">
              <h3 className="font-medium mb-2">Notes</h3>
              <p className="whitespace-pre-line">{plan.notes}</p>
            </div>
          )}
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-medium text-muted-foreground">Initial Balance</h3>
              <p className="text-2xl font-bold">{formatCurrency(plan.initialBalance)}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-muted-foreground">Remaining Balance</h3>
              <p className="text-2xl font-bold">{formatCurrency(plan.remainingBalance)}</p>
            </div>
          </div>
          
          <div>
            <h3 className="font-medium mb-4">Accounts</h3>
            {plan.accounts.length === 0 ? (
              <p className="text-muted-foreground">No accounts have been added to this plan.</p>
            ) : (
              <div className="space-y-4">
                {plan.accounts.map((planAccount) => (
                  <Card key={planAccount.id} className="shadow-sm">
                    <CardHeader className="py-3">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">
                          {planAccount.account.name}
                        </CardTitle>
                        {planAccount.isChecked && (
                          <Badge variant="default" className="ml-2">
                            Checked
                          </Badge>
                        )}
                      </div>
                    </CardHeader>
                    
                    <CardContent className="py-3 space-y-4">
                      {planAccount.notes && (
                        <div className="bg-muted p-3 rounded-md text-sm">
                          <p className="whitespace-pre-line">{planAccount.notes}</p>
                        </div>
                      )}
                      
                      <div>
                        <h4 className="text-sm font-medium mb-2">Buckets</h4>
                        {planAccount.buckets.length === 0 ? (
                          <p className="text-sm text-muted-foreground">No buckets allocated</p>
                        ) : (
                          <div className="space-y-2">
                            {planAccount.buckets.map((bucket) => (
                              <div key={bucket.id} className="flex justify-between text-sm py-1 border-b border-gray-100">
                                <span>{bucket.name}</span>
                                <span className="font-medium">{formatCurrency(bucket.allocatedAmount)}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </CardContent>
        
        <CardFooter className="flex justify-between pt-4">
          <p className="text-sm text-muted-foreground">
            This is a shared view. Sign in to create your own plans.
          </p>
          <Button 
            variant="outline" 
            onClick={() => router.push('/auth/signin')}
          >
            Sign In
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
} 