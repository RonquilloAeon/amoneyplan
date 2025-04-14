'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { useAccountsPaginated } from '@/lib/hooks/useAccounts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PlusIcon } from 'lucide-react';

export default function AccountsPage() {
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
    goToPreviousPage 
  } = useAccountsPaginated(10);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/login');
    }
  }, [status, router]);

  if (status === 'loading') {
    return <div className="flex justify-center py-8">Loading...</div>;
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
        <Card>
          <CardContent className="py-10 flex flex-col items-center">
            <p className="text-muted-foreground mb-4">You don't have any accounts yet</p>
            <Button onClick={() => router.push('/accounts/new')}>
              <PlusIcon className="h-4 w-4 mr-2" />
              Create Your First Account
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            {accounts.map((account) => (
              <Card key={account.id} className="cursor-pointer hover:shadow-md transition-shadow" 
                onClick={() => router.push(`/accounts/${account.id}`)}>
                <CardHeader className="py-4">
                  <CardTitle>{account.name}</CardTitle>
                </CardHeader>
              </Card>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex justify-between items-center pt-4">
              <Button 
                variant="outline" 
                onClick={goToPreviousPage} 
                disabled={currentPage === 1}
              >
                Previous
              </Button>
              <span>
                Page {currentPage} of {totalPages}
              </span>
              <Button 
                variant="outline" 
                onClick={goToNextPage} 
                disabled={currentPage === totalPages}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
} 