'use client';

import React, { useEffect, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { useAccountsPaginated } from '@/lib/hooks/useAccountsPaginated';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PlusIcon } from 'lucide-react';
import { PaginationControls } from '@/components/PaginationControls';
import { EmptyState } from '@/components/EmptyState';
import { AccountsGraphic } from '@/components/EmptyStateGraphics';

// Renamed original component to avoid naming conflict
function AccountsPageContent() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const { 
    accounts, 
    allAccounts,
    loading, 
    error, 
    currentPage, 
    totalPages, 
    goToNextPage, 
    goToPreviousPage,
    goToPage
  } = useAccountsPaginated(10);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin');
    }
  }, [status, router]);

  if (status === 'loading') {
    return <div className="flex justify-center py-8">Loading session...</div>;
  }

  if (error) {
    return <div className="text-red-500 py-4">{error}</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Your Accounts</h1>
        <Button onClick={() => router.push('/accounts/new')}>
          <PlusIcon className="h-4 w-4 mr-2" />
          New Account
        </Button>
      </div>

      {loading ? (
        <div className="py-8 text-center">Loading accounts...</div>
      ) : allAccounts.length === 0 ? (
        <EmptyState
          graphic={<AccountsGraphic />}
          title="You don't have any accounts yet"
          description={[
            "Accounts help you organize your finances by tracking where your money is located.",
            "Create accounts to track your checking, savings, credit cards, or any other place your money goes."
          ]}
          actionInstruction="Click the"
          actionInstructionHighlight='"New Account"'
        />
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            {accounts.map((account) => (
              <Card key={account.id}>
                <CardHeader className="py-4">
                  <CardTitle>{account.name}</CardTitle>
                </CardHeader>
                {account.notes && (
                  <CardContent className="pt-0">
                    <p className="text-muted-foreground text-sm">{account.notes}</p>
                  </CardContent>
                )}
              </Card>
            ))}
          </div>

          {/* PaginationControls might still need Suspense if it uses useSearchParams *directly* */}
          {/* but the main cause is useAccountsPaginated, which is now inside Suspense */}
          <PaginationControls
            currentPage={currentPage}
            totalPages={totalPages}
            goToNextPage={goToNextPage}
            goToPreviousPage={goToPreviousPage}
            goToPage={goToPage}
            className="mt-4"
          />
        </>
      )}
    </div>
  );
}

// Default export now wraps the main content component in Suspense
export default function AccountsPage() {
  return (
    <Suspense fallback={<div className="flex justify-center py-8">Loading accounts page...</div>}>
      <AccountsPageContent />
    </Suspense>
  );
} 