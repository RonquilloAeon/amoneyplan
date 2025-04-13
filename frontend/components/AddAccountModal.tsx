'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, Plus, Trash2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useAccounts } from '@/lib/hooks/useAccounts';
import { usePlans } from '@/lib/hooks/usePlans';
import { BucketConfigInput, Plan } from '@/lib/hooks/usePlans';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { formatCurrency } from '@/lib/utils/format';

interface BucketFormState {
  name: string;
  category: string;
  allocatedAmount: string;
}

interface AddAccountModalProps {
  planId: string;
  availableAccounts: Array<{ id: string; name: string }>;
  onSuccess?: () => void;
}

export function AddAccountModal({ planId, availableAccounts, onSuccess }: AddAccountModalProps) {
  const [open, setOpen] = useState(false);
  const [selectedAccountId, setSelectedAccountId] = useState<string>('');
  const [notes, setNotes] = useState('');
  const [buckets, setBuckets] = useState<BucketFormState[]>([
    { name: 'Default', category: '', allocatedAmount: '' }
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>(availableAccounts.length > 0 ? 'existing' : 'new');
  const [newAccountName, setNewAccountName] = useState<string>('');

  const { addAccountToPlan, draftPlan } = usePlans();
  const { createAccount, accounts, loading: accountsLoading, refetchAccounts } = useAccounts();

  // Update the active tab when availableAccounts changes
  useEffect(() => {
    setActiveTab(availableAccounts.length > 0 ? 'existing' : 'new');
  }, [availableAccounts.length]);

  // Auto-select the first account when available accounts change
  useEffect(() => {
    if (availableAccounts.length > 0 && !selectedAccountId) {
      setSelectedAccountId(availableAccounts[0].id);
    }
  }, [availableAccounts, selectedAccountId]);
  
  // Refetch accounts when the modal is opened
  useEffect(() => {
    if (open) {
      console.log('Refetching accounts...');
      refetchAccounts().then(() => {
        console.log('Accounts after refetch:', accounts);
      });
    }
  }, [open, refetchAccounts, accounts]);

  const handleAddBucket = () => {
    setBuckets([...buckets, { name: '', category: '', allocatedAmount: '' }]);
  };

  const handleRemoveBucket = (index: number) => {
    const newBuckets = [...buckets];
    newBuckets.splice(index, 1);
    setBuckets(newBuckets);
  };

  const handleBucketChange = (index: number, field: keyof BucketFormState, value: string) => {
    const newBuckets = [...buckets];
    newBuckets[index] = { ...newBuckets[index], [field]: value };
    setBuckets(newBuckets);
  };

  const validateForm = (): boolean => {
    if (activeTab === 'existing') {
      // Check if account is selected
      if (!selectedAccountId) {
        setError('Please select an account');
        return false;
      }
    } else {
      // Check if new account name is provided
      if (!newAccountName.trim()) {
        setError('Please enter a name for the new account');
        return false;
      }
      
      // Check for duplicate account name
      const nameExists = accounts?.some(account => 
        account.name.toLowerCase() === newAccountName.trim().toLowerCase()
      );
      
      if (nameExists) {
        setError(`An account named "${newAccountName.trim()}" already exists`);
        return false;
      }
    }

    // Check if all buckets have names and categories
    for (let i = 0; i < buckets.length; i++) {
      if (!buckets[i].name.trim()) {
        setError(`Bucket #${i + 1} needs a name`);
        return false;
      }
      
      if (!buckets[i].category) {
        setError(`Bucket #${i + 1} needs a category`);
        return false;
      }
      
      if (!buckets[i].allocatedAmount) {
        setError(`Bucket #${i + 1} needs an amount`);
        return false;
      }
    }

    // Check for duplicate bucket names
    const bucketNames = buckets.map(bucket => bucket.name.trim());
    const hasDuplicates = bucketNames.some(
      (name, index) => bucketNames.indexOf(name) !== index
    );
    
    if (hasDuplicates) {
      setError('Bucket names must be unique');
      return false;
    }

    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setError(null);
    setIsSubmitting(true);
    
    try {
      const bucketConfigs: BucketConfigInput[] = buckets.map(bucket => ({
        name: bucket.name.trim(),
        category: bucket.category,
        allocatedAmount: parseFloat(bucket.allocatedAmount) || 0
      }));

      let accountId = selectedAccountId;
      
      // If creating a new account, do that first
      if (activeTab === 'new') {
        const newAccount = await createAccount({
          name: newAccountName.trim(),
          notes: notes
        });
        
        if (!newAccount || !newAccount.id) {
          throw new Error('Failed to create the new account');
        }
        
        accountId = newAccount.id;
      }

      await addAccountToPlan(planId, accountId, bucketConfigs);
      
      // Reset form and close modal
      setSelectedAccountId('');
      setNewAccountName('');
      setNotes('');
      setBuckets([{ name: 'Default', category: '', allocatedAmount: '' }]);
      setOpen(false);
      
      // Refresh data and notify parent of success
      await refetchAccounts();
      if (onSuccess) {
        onSuccess();
      }
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An error occurred while adding the account');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setSelectedAccountId('');
    setNewAccountName('');
    setNotes('');
    setBuckets([{ name: 'Default', category: '', allocatedAmount: '' }]);
    setError(null);
    setActiveTab(availableAccounts.length > 0 ? 'existing' : 'new');
  };

  // Find the current plan and get remaining balance
  const currentPlan = draftPlan?.id === planId ? draftPlan : null;

  return (
    <Dialog open={open} onOpenChange={(newOpen) => {
      setOpen(newOpen);
      if (newOpen) {
        // When opening the modal, refetch accounts
        refetchAccounts();
      } else {
        // When closing the modal, reset the form
        resetForm();
      }
    }}>
      <DialogTrigger asChild>
        <Button>Add Account</Button>
      </DialogTrigger>
      <DialogContent 
        className="sm:max-w-[600px] bg-white dark:bg-gray-950"
        style={{ backgroundColor: 'white' }}
      >
        <DialogHeader>
          <DialogTitle>Add Account to Plan</DialogTitle>
          <DialogDescription>
            Select an existing account or create a new one to add to your money plan.
          </DialogDescription>
        </DialogHeader>
        
        {/* Remaining Balance Display */}
        {currentPlan && (
          <div className="bg-muted p-3 rounded-md mb-4 text-center">
            <p className="text-sm font-medium">Remaining Plan Balance</p>
            <p className="text-2xl font-bold">{formatCurrency(currentPlan.remainingBalance)}</p>
          </div>
        )}
        
        <div className="grid gap-4 py-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          {/* Account Selection Tabs */}
          <div className="space-y-6">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid grid-cols-2 w-full bg-white dark:bg-gray-800">
                <TabsTrigger 
                  value="existing" 
                  disabled={availableAccounts.length === 0 || isSubmitting}
                  className="data-[state=active]:bg-muted"
                >
                  Use Existing Account
                </TabsTrigger>
                <TabsTrigger 
                  value="new"
                  disabled={isSubmitting}
                  className="data-[state=active]:bg-muted"
                >
                  Create New Account
                </TabsTrigger>
              </TabsList>
            </Tabs>

            {activeTab === 'existing' ? (
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="account-select" className="text-right">
                  Account
                </Label>
                {accountsLoading ? (
                  <div className="col-span-3 flex items-center">
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    <span>Loading accounts...</span>
                  </div>
                ) : (
                  <Select
                    value={selectedAccountId}
                    onValueChange={setSelectedAccountId}
                    disabled={isSubmitting || availableAccounts.length === 0}
                  >
                    <SelectTrigger 
                      id="account-select" 
                      className="col-span-3 w-full bg-white dark:bg-gray-800"
                      style={{ backgroundColor: 'white' }}
                    >
                      <SelectValue placeholder="Select an account" />
                    </SelectTrigger>
                    <SelectContent 
                      className="bg-white dark:bg-gray-800"
                      style={{ backgroundColor: 'white' }}
                    >
                      {availableAccounts.length > 0 ? (
                        availableAccounts.map((account) => (
                          <SelectItem key={account.id} value={account.id}>
                            {account.name}
                          </SelectItem>
                        ))
                      ) : (
                        <SelectItem value="none" disabled>No available accounts</SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="new-account-name" className="text-right">
                  Account Name
                </Label>
                <Input
                  id="new-account-name"
                  className="col-span-3"
                  placeholder="Enter account name"
                  value={newAccountName}
                  onChange={(e) => setNewAccountName(e.target.value)}
                  disabled={isSubmitting}
                />
                <p className="col-span-4 col-start-2 text-xs text-muted-foreground mt-1">
                  Account names must be unique. Examples: "Chase Checking", "Wealthfront", "Savings Account"
                </p>
              </div>
            )}
          </div>
          
          {/* Notes Field */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="notes" className="text-right">
              Notes
            </Label>
            <Textarea
              id="notes"
              className="col-span-3"
              placeholder="Optional notes for this account allocation"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              disabled={isSubmitting}
            />
          </div>
          
          {/* Buckets Section */}
          <div className="mt-4">
            <h3 className="text-lg font-medium mb-2">Buckets</h3>
            <div className="space-y-4">
              {buckets.map((bucket, index) => (
                <div key={index} className="grid grid-cols-12 gap-2 items-center border p-3 rounded-md">
                  <div className="col-span-4">
                    <Label htmlFor={`bucket-name-${index}`} className="mb-1 block flex items-center">
                      Name <span className="text-red-500 ml-1">*</span>
                    </Label>
                    <Input
                      id={`bucket-name-${index}`}
                      value={bucket.name}
                      onChange={(e) => handleBucketChange(index, 'name', e.target.value)}
                      disabled={isSubmitting}
                      required
                      placeholder="Enter bucket name"
                    />
                  </div>
                  <div className="col-span-3">
                    <Label htmlFor={`bucket-category-${index}`} className="mb-1 block flex items-center">
                      Category <span className="text-red-500 ml-1">*</span>
                    </Label>
                    <Select
                      value={bucket.category}
                      onValueChange={(value) => handleBucketChange(index, 'category', value)}
                      disabled={isSubmitting}
                      required
                    >
                      <SelectTrigger 
                        id={`bucket-category-${index}`} 
                        className="bg-white dark:bg-gray-800"
                        style={{ backgroundColor: 'white' }}
                      >
                        <SelectValue placeholder="Select a category" />
                      </SelectTrigger>
                      <SelectContent 
                        className="bg-white dark:bg-gray-800"
                        style={{ backgroundColor: 'white' }}
                      >
                        <SelectItem value="need">Need</SelectItem>
                        <SelectItem value="want">Want</SelectItem>
                        <SelectItem value="savings">Savings/Investing</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="col-span-3">
                    <Label htmlFor={`bucket-amount-${index}`} className="mb-1 block flex items-center">
                      Amount <span className="text-red-500 ml-1">*</span>
                    </Label>
                    <Input
                      id={`bucket-amount-${index}`}
                      type="number"
                      placeholder="Enter amount"
                      value={bucket.allocatedAmount}
                      onChange={(e) => handleBucketChange(index, 'allocatedAmount', e.target.value)}
                      disabled={isSubmitting}
                      required
                    />
                  </div>
                  <div className="col-span-2 flex items-end justify-end">
                    {buckets.length > 1 && (
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => handleRemoveBucket(index)}
                        disabled={isSubmitting}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}

              <Button
                type="button"
                variant="outline"
                className="w-full"
                onClick={handleAddBucket}
                disabled={isSubmitting}
              >
                <Plus className="mr-2 h-4 w-4" /> Add Bucket
              </Button>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button 
            type="submit" 
            onClick={handleSubmit} 
            disabled={isSubmitting}
          >
            {isSubmitting ? (
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
  );
} 