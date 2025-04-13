'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { usePlans } from '@/lib/hooks/usePlans';
import { useAccounts } from '@/lib/hooks/useAccounts';
import { formatCurrency, formatDate, calculateTotalBalance } from '@/lib/utils/format';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { 
  AlertCircle, 
  Archive, 
  Check, 
  Plus,
  Loader2,
  Trash2
} from 'lucide-react';
import { StartPlanModal } from '@/components/StartPlanModal';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue
} from '@/components/ui/select';

export default function PlansPage() {
  // Check authentication with NextAuth
  const { data: session, status } = useSession();
  const router = useRouter();
  
  // Redirect to login if not authenticated
  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin?callbackUrl=/plans');
    }
  }, [status, router]);
  
  const { 
    plans, 
    draftPlan, 
    loading, 
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
  } = usePlans();

  const { accounts, loading: accountsLoading } = useAccounts();

  const [expandedAccounts, setExpandedAccounts] = useState<Record<string, boolean>>({});
  const [isCommitting, setIsCommitting] = useState(false);
  const [isArchiving, setIsArchiving] = useState(false);
  const [selectedAccountId, setSelectedAccountId] = useState<string>('');
  const [isAddingAccount, setIsAddingAccount] = useState(false);
  const [showAddAccountDialog, setShowAddAccountDialog] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Filter out accounts that are already in the draft plan
  const availableAccounts = accounts?.filter(
    account => !draftPlan?.accounts.some(planAccount => planAccount.account.id === account.id)
  ) || [];

  const handleAddAccount = async () => {
    if (!draftPlan || !selectedAccountId) return;
    
    setActionError(null);
    setIsAddingAccount(true);
    
    try {
      await addAccountToPlan(draftPlan.id, selectedAccountId, []);
      setShowAddAccountDialog(false);
      setSelectedAccountId('');
    } catch (err) {
      if (err instanceof Error) {
        setActionError(`Failed to add account: ${err.message}`);
      } else {
        setActionError('An unexpected error occurred');
      }
    } finally {
      setIsAddingAccount(false);
    }
  };

  const handleUpdatePlanNotes = async (notes: string) => {
    if (!draftPlan) return;
    try {
      await updatePlanNotes(draftPlan.id, notes);
    } catch (err) {
      console.error('Failed to update plan notes:', err);
    }
  };

  const handleUpdatePlanAccountNotes = async (accountId: string, notes: string) => {
    if (!draftPlan) return;
    try {
      await updatePlanAccountNotes(draftPlan.id, accountId, notes);
    } catch (err) {
      console.error('Failed to update account notes:', err);
    }
  };

  const handleToggleAccountCheck = async (accountId: string) => {
    if (!draftPlan) return;
    try {
      await toggleAccountCheck(draftPlan.id, accountId);
    } catch (err) {
      console.error('Failed to toggle account check:', err);
    }
  };

  const handleRemoveAccount = async (accountId: string) => {
    if (!draftPlan) return;
    try {
      await removeAccountFromPlan(draftPlan.id, accountId);
    } catch (err) {
      console.error('Failed to remove account:', err);
    }
  };

  const handleCommitPlan = async () => {
    if (!draftPlan) return;
    
    setActionError(null);
    setIsCommitting(true);
    
    try {
      await commitPlan(draftPlan.id);
      await refetchPlans();
      await refetchDraft();
    } catch (err) {
      if (err instanceof Error) {
        setActionError(`Failed to commit plan: ${err.message}`);
      } else {
        setActionError('An unexpected error occurred');
      }
    } finally {
      setIsCommitting(false);
    }
  };

  const handleArchivePlan = async () => {
    if (!draftPlan) return;
    
    setActionError(null);
    setIsArchiving(true);
    
    try {
      await archivePlan(draftPlan.id);
      await refetchPlans();
      await refetchDraft();
    } catch (err) {
      if (err instanceof Error) {
        setActionError(`Failed to archive plan: ${err.message}`);
      } else {
        setActionError('An unexpected error occurred');
      }
    } finally {
      setIsArchiving(false);
    }
  };

  const toggleAccountExpansion = (accountId: string) => {
    setExpandedAccounts(prev => ({
      ...prev,
      [accountId]: !prev[accountId],
    }));
  };

  // Show loading when checking authentication
  if (status === 'loading') {
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

  if (loading || accountsLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
          <p className="text-lg font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!draftPlan) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold">No active money plan</h2>
          <p className="text-muted-foreground">Start a new plan to manage your finances.</p>
        </div>
        <StartPlanModal />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {actionError && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{actionError}</AlertDescription>
        </Alert>
      )}
      
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Current Plan</h1>
        <div className="space-x-2">
          <Button 
            variant="outline" 
            onClick={handleArchivePlan} 
            disabled={isArchiving || isCommitting}
          >
            {isArchiving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Archiving...
              </>
            ) : (
              <>
                <Archive className="mr-2 h-4 w-4" />
                Archive Plan
              </>
            )}
          </Button>
          <Button 
            onClick={handleCommitPlan} 
            disabled={isCommitting || isArchiving}
          >
            {isCommitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Committing...
              </>
            ) : (
              <>
                <Check className="mr-2 h-4 w-4" />
                Commit Plan
              </>
            )}
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Plan Overview</CardTitle>
          <CardDescription>
            Created on {formatDate(draftPlan.createdAt)}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <div className="flex justify-between mb-2">
              <span>Balance Allocation</span>
              <span>
                {formatCurrency(Number(calculateTotalBalance(draftPlan)))} / {formatCurrency(Number(draftPlan.initialBalance))}
              </span>
            </div>
            <Progress 
              value={(Number(calculateTotalBalance(draftPlan)) / Number(draftPlan.initialBalance)) * 100} 
              className="h-2"
            />
          </div>
          
          <div className="space-y-2">
            <h3 className="font-semibold">Notes</h3>
            <Textarea 
              value={draftPlan.notes || ''} 
              placeholder="Add notes to your plan"
              className="text-foreground"
              onChange={(e) => handleUpdatePlanNotes(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Accounts Section */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold">Accounts</h2>
          <Dialog open={showAddAccountDialog} onOpenChange={setShowAddAccountDialog}>
            <DialogTrigger asChild>
              <Button variant="outline" disabled={availableAccounts.length === 0}>
                <Plus className="mr-2 h-4 w-4" />
                Add Account
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Account to Plan</DialogTitle>
                <DialogDescription>
                  Select an account to add to your money plan.
                </DialogDescription>
              </DialogHeader>
              <div className="py-4">
                <Label htmlFor="account-select" className="mb-2 block">
                  Select Account
                </Label>
                <Select
                  value={selectedAccountId}
                  onValueChange={setSelectedAccountId}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select an account" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableAccounts.map((account) => (
                      <SelectItem key={account.id} value={account.id}>
                        {account.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <DialogFooter>
                <Button 
                  onClick={handleAddAccount} 
                  disabled={!selectedAccountId || isAddingAccount}
                >
                  {isAddingAccount ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Adding...
                    </>
                  ) : (
                    'Add Account'
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
        
        {draftPlan.accounts.length === 0 ? (
          <Card className="p-6 text-center">
            <p className="text-muted-foreground mb-4">No accounts added to this plan yet.</p>
            <Button 
              variant="outline" 
              onClick={() => setShowAddAccountDialog(true)}
              disabled={availableAccounts.length === 0}
            >
              <Plus className="mr-2 h-4 w-4" />
              Add Your First Account
            </Button>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {draftPlan.accounts.map((planAccount) => (
              <Card key={planAccount.id} className="relative">
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start">
                    <CardTitle>{planAccount.account.name}</CardTitle>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="h-8 w-8 p-0"
                      onClick={() => handleRemoveAccount(planAccount.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                      <span className="sr-only">Remove account</span>
                    </Button>
                  </div>
                  <CardDescription>
                    Total allocated: {formatCurrency(Number(planAccount.buckets.reduce((sum, bucket) => sum + bucket.allocatedAmount, 0)))}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pb-2">
                  <div className="space-y-2">
                    {planAccount.buckets.length > 0 ? (
                      planAccount.buckets.map((bucket) => (
                        <div key={bucket.id} className="flex justify-between">
                          <span>{bucket.name}</span>
                          <span>{formatCurrency(bucket.allocatedAmount)}</span>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-muted-foreground">No buckets configured</p>
                    )}
                  </div>
                </CardContent>
                <CardFooter>
                  <Textarea 
                    value={planAccount.notes || ''} 
                    placeholder="Add notes"
                    className="text-foreground text-sm"
                    rows={2}
                    onChange={(e) => handleUpdatePlanAccountNotes(planAccount.id, e.target.value)}
                  />
                </CardFooter>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
} 