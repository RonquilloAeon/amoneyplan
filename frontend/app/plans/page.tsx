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
  Trash2,
  LayoutGrid,
  List
} from 'lucide-react';
import { StartPlanModal } from '../../components/StartPlanModal';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue
} from '@/components/ui/select';
import { ScrollableAddAccountModal } from '../../components/ScrollableAddAccountModal';
import { PlanAccountCard } from '../../components/PlanAccountCard';
import { useToast } from '@/lib/hooks/useToast';

// We'll style a div element as our badge since there seems to be an issue with the badge component import
// This is a temporary solution until the badge component is fixed

export default function PlansPage() {
  // Check authentication with NextAuth
  const { data: session, status } = useSession();
  const router = useRouter();
  const { toast } = useToast();
  
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

  const { accounts, loading: accountsLoading, refetchAccounts } = useAccounts();

  const [expandedAccounts, setExpandedAccounts] = useState<Record<string, boolean>>({});
  const [isCommitting, setIsCommitting] = useState(false);
  const [isArchiving, setIsArchiving] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Display error in toast if it exists
  useEffect(() => {
    if (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: error
      });
    }
  }, [error, toast]);

  // Refetch accounts and plans when the component mounts
  useEffect(() => {
    if (session) {
      refetchAccounts();
      refetchDraft();
    }
  }, [session, refetchAccounts, refetchDraft]);

  // Filter out accounts that are already in the draft plan
  const availableAccounts = accounts?.filter(
    account => !draftPlan?.accounts.some(planAccount => planAccount.account.id === account.id)
  ) || [];

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
    setIsCommitting(true);
    try {
      await commitPlan(draftPlan.id);
      // No need to set action error as the toast will be shown from the hook
    } catch (err) {
      // The error is already handled in the hook with a toast
      console.error('Failed to commit plan:', err);
    } finally {
      setIsCommitting(false);
    }
  };

  const handleArchivePlan = async () => {
    if (!draftPlan) return;
    setIsArchiving(true);
    try {
      await archivePlan(draftPlan.id);
      // No need to set action error as the toast will be shown from the hook
    } catch (err) {
      // The error is already handled in the hook with a toast
      console.error('Failed to archive plan:', err);
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

  const allocatedAmount = calculateTotalBalance(draftPlan);
  const allocatedPercentage = (Number(allocatedAmount) / Number(draftPlan.initialBalance)) * 100;
  const remainingAmount = Number(draftPlan.initialBalance) - Number(allocatedAmount);

  // Determine progress color based on percentage
  const getProgressColor = () => {
    if (allocatedPercentage < 80) return 'bg-blue-500';
    if (allocatedPercentage < 100) return 'bg-amber-500';
    if (allocatedPercentage === 100) return 'bg-emerald-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Current Plan</h1>
        <div className="space-x-2">
          <Button 
            variant="outline" 
            onClick={handleArchivePlan} 
            disabled={isArchiving || isCommitting}
            className="border-amber-600 text-amber-600 hover:bg-amber-50 hover:text-amber-700"
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
            className="bg-emerald-600 hover:bg-emerald-700 text-white"
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

      <Card className="border-2 border-primary/20 shadow-md">
        <CardHeader className="bg-primary/5">
          <CardTitle>Plan Overview</CardTitle>
          <CardDescription>
            Created on {formatDate(draftPlan.createdAt)}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
              <h3 className="text-sm font-medium text-gray-500 mb-1">Initial Balance</h3>
              <p className="text-2xl font-bold text-primary">{formatCurrency(Number(draftPlan.initialBalance))}</p>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
              <h3 className="text-sm font-medium text-gray-500 mb-1">Allocated</h3>
              <p className="text-2xl font-bold text-emerald-600">{formatCurrency(Number(allocatedAmount))}</p>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
              <h3 className="text-sm font-medium text-gray-500 mb-1">Remaining</h3>
              <p className="text-2xl font-bold text-blue-600">{formatCurrency(remainingAmount)}</p>
            </div>
          </div>

          <div>
            <div className="flex justify-between mb-2">
              <span className="font-medium">Allocation Progress</span>
              <span className="font-medium">
                {allocatedPercentage.toFixed(0)}%
              </span>
            </div>
            <Progress 
              value={allocatedPercentage} 
              className="h-3"
              indicatorClassName={getProgressColor()}
            />
          </div>
          
          <div className="space-y-2 mt-6">
            <h3 className="font-semibold">Notes</h3>
            <Textarea 
              value={draftPlan.notes || ''} 
              placeholder="Add notes to your plan"
              className="text-foreground border-gray-300 focus:border-primary focus:ring-primary"
              onChange={(e) => handleUpdatePlanNotes(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Accounts Section */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center">
            <h2 className="text-2xl font-bold mr-3">Accounts</h2>
            {draftPlan.accounts.length > 0 && (
              <div className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold bg-primary text-white">
                {draftPlan.accounts.length}
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <div className="flex border rounded-md overflow-hidden">
              <Button
                variant={viewMode === 'grid' ? 'default' : 'outline'}
                size="sm"
                className="rounded-none border-0"
                onClick={() => setViewMode('grid')}
              >
                <LayoutGrid className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === 'list' ? 'default' : 'outline'}
                size="sm"
                className="rounded-none border-0"
                onClick={() => setViewMode('list')}
              >
                <List className="h-4 w-4" />
              </Button>
            </div>
            
            <ScrollableAddAccountModal 
              planId={draftPlan.id} 
              availableAccounts={availableAccounts}
              onSuccess={() => {
                refetchDraft();
                refetchAccounts();
              }}
            />
          </div>
        </div>
        
        {draftPlan.accounts.length === 0 ? (
          <Card className="p-6 text-center border-dashed border-2">
            <p className="text-muted-foreground mb-4">No accounts added to this plan yet.</p>
            <ScrollableAddAccountModal 
              planId={draftPlan.id} 
              availableAccounts={availableAccounts}
              onSuccess={() => {
                refetchDraft();
                refetchAccounts();
              }}
            />
          </Card>
        ) : (
          <div className={viewMode === 'grid' 
            ? "grid gap-4 md:grid-cols-2 lg:grid-cols-3" 
            : "space-y-4"
          }>
            {draftPlan.accounts.map((planAccount) => (
              <PlanAccountCard
                key={planAccount.id}
                planAccount={planAccount}
                initialBalance={Number(draftPlan.initialBalance)}
                onRemove={handleRemoveAccount}
                onUpdateNotes={handleUpdatePlanAccountNotes}
                viewMode={viewMode}
                planId={draftPlan.id}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
} 