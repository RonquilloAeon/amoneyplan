'use client';

import { useState } from 'react';
import { usePlans } from '@/lib/hooks/usePlans';
import { useAccounts } from '@/lib/hooks/useAccounts';
import { formatCurrency, formatDate, calculateTotalBalance } from '@/lib/utils/format';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle, Archive, Check, ChevronDown, ChevronUp, Plus } from 'lucide-react';
import { CreatePlanModal } from '@/components/CreatePlanModal';

export default function PlansPage() {
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

  const [showNewPlanDialog, setShowNewPlanDialog] = useState(false);
  const [newPlanInput, setNewPlanInput] = useState({
    initialBalance: '',
    planDate: new Date().toISOString().split('T')[0],
    notes: '',
  });

  const [expandedAccounts, setExpandedAccounts] = useState<Record<string, boolean>>({});

  const handleCreatePlan = async () => {
    await createPlan({
      initialBalance: parseFloat(newPlanInput.initialBalance),
      planDate: newPlanInput.planDate,
      notes: newPlanInput.notes,
    });
    setShowNewPlanDialog(false);
    setNewPlanInput({
      initialBalance: '',
      planDate: new Date().toISOString().split('T')[0],
      notes: '',
    });
  };

  const handleAddAccount = async (accountId: string) => {
    if (!draftPlan) return;
    await addAccountToPlan(draftPlan.id, accountId, []);
  };

  const handleUpdatePlanNotes = async (notes: string) => {
    if (!draftPlan) return;
    await updatePlanNotes(draftPlan.id, notes);
  };

  const handleUpdatePlanAccountNotes = async (planAccountId: string, notes: string) => {
    if (!draftPlan) return;
    await updatePlanAccountNotes(draftPlan.id, planAccountId, notes);
  };

  const handleToggleAccountCheck = async (planAccountId: string) => {
    if (!draftPlan) return;
    await toggleAccountCheck(draftPlan.id, planAccountId);
  };

  const handleRemoveAccount = async (planAccountId: string) => {
    if (!draftPlan) return;
    await removeAccountFromPlan(draftPlan.id, planAccountId);
  };

  const toggleAccountExpansion = (planAccountId: string) => {
    setExpandedAccounts(prev => ({
      ...prev,
      [planAccountId]: !prev[planAccountId],
    }));
  };

  if (loading || accountsLoading) {
    return <div>Loading...</div>;
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
        <CreatePlanModal />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Current Plan</h1>
        <div className="space-x-2">
          <Button variant="outline">Archive Plan</Button>
          <Button>Commit Plan</Button>
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
              <span>{formatCurrency(calculateTotalBalance(draftPlan))} / {formatCurrency(draftPlan.initialBalance)}</span>
            </div>
            <Progress value={(calculateTotalBalance(draftPlan) / draftPlan.initialBalance) * 100} />
          </div>
          
          <div className="space-y-2">
            <h3 className="font-semibold">Notes</h3>
            <Input 
              value={draftPlan.notes} 
              placeholder="Add notes to your plan"
              className="text-foreground"
            />
          </div>
        </CardContent>
      </Card>

      {/* Accounts Section */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold">Accounts</h2>
          <Button variant="outline">Add Account</Button>
        </div>
        
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {draftPlan.accounts.map((planAccount) => (
            <Card key={planAccount.id}>
              <CardHeader>
                <CardTitle>{planAccount.account.name}</CardTitle>
                <CardDescription>
                  Total allocated: {formatCurrency(calculateTotalBalance(planAccount))}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {planAccount.buckets.map((bucket) => (
                    <div key={bucket.id} className="flex justify-between">
                      <span>{bucket.name}</span>
                      <span>{formatCurrency(bucket.allocatedAmount)}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
              <CardFooter>
                <Input 
                  value={planAccount.notes} 
                  placeholder="Add notes"
                  className="text-foreground"
                />
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
} 