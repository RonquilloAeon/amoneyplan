'use client';

import * as React from 'react';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X, Plus, Trash2, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useAccounts } from '@/lib/hooks/useAccounts';
import { usePlans } from '@/lib/hooks/usePlans';
import { BucketConfigInput, Plan } from '@/lib/hooks/usePlans';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { formatCurrency } from '@/lib/utils/format';
import { cn } from '@/lib/utils';
import { useToast } from '@/lib/hooks/useToast';

interface BucketFormState {
  name: string;
  category: string;
  allocatedAmount: string;
}

interface ScrollableAddAccountModalProps {
  planId: string;
  availableAccounts: Array<{ id: string; name: string }>;
  onSuccess?: () => void;
}

export function ScrollableAddAccountModal({ planId, availableAccounts, onSuccess }: ScrollableAddAccountModalProps) {
  const [open, setOpen] = useState(false);
  const [selectedAccountId, setSelectedAccountId] = useState<string>('');
  const [notes, setNotes] = useState('');
  const [buckets, setBuckets] = useState<BucketFormState[]>([
    { name: 'Default', category: '', allocatedAmount: '' }
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();
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
        toast({
          variant: "destructive",
          title: "Validation Error",
          description: "Please select an account"
        });
        return false;
      }
    } else {
      // Check if new account name is provided
      if (!newAccountName.trim()) {
        toast({
          variant: "destructive",
          title: "Validation Error",
          description: "Please enter a name for the new account"
        });
        return false;
      }
      
      // Check for duplicate account name
      const nameExists = accounts?.some(account => 
        account.name.toLowerCase() === newAccountName.trim().toLowerCase()
      );
      
      if (nameExists) {
        toast({
          variant: "destructive",
          title: "Validation Error",
          description: `An account named "${newAccountName.trim()}" already exists`
        });
        return false;
      }
    }

    // Check if all buckets have names and categories
    for (let i = 0; i < buckets.length; i++) {
      if (!buckets[i].name.trim()) {
        toast({
          variant: "destructive",
          title: "Validation Error",
          description: `Bucket #${i + 1} needs a name`
        });
        return false;
      }
      
      if (!buckets[i].category) {
        toast({
          variant: "destructive",
          title: "Validation Error",
          description: `Bucket #${i + 1} needs a category`
        });
        return false;
      }
      
      if (!buckets[i].allocatedAmount) {
        toast({
          variant: "destructive",
          title: "Validation Error",
          description: `Bucket #${i + 1} needs an amount`
        });
        return false;
      }
    }

    // Check for duplicate bucket names
    const bucketNames = buckets.map(bucket => bucket.name.trim());
    const hasDuplicates = bucketNames.some(
      (name, index) => bucketNames.indexOf(name) !== index
    );
    
    if (hasDuplicates) {
      toast({
        variant: "destructive",
        title: "Validation Error",
        description: "Bucket names must be unique"
      });
      return false;
    }

    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

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
      
      // Show success toast
      toast({
        title: "Success",
        description: "Account successfully added to plan"
      });
      
      if (onSuccess) {
        onSuccess();
      }
    } catch (err) {
      if (err instanceof Error) {
        toast({
          variant: "destructive",
          title: "Error",
          description: err.message
        });
      } else {
        toast({
          variant: "destructive",
          title: "Error",
          description: "An error occurred while adding the account"
        });
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
    setActiveTab(availableAccounts.length > 0 ? 'existing' : 'new');
  };

  // Find the current plan and get remaining balance
  const currentPlan = draftPlan?.id === planId ? draftPlan : null;

  return (
    <DialogPrimitive.Root open={open} onOpenChange={(newOpen) => {
      setOpen(newOpen);
      if (newOpen) {
        // When opening the modal, refetch accounts
        refetchAccounts();
      } else {
        // When closing the modal, reset the form
        resetForm();
      }
    }}>
      <DialogPrimitive.Trigger asChild>
        <Button className="bg-primary hover:bg-primary/90 ml-auto">
          <Plus className="mr-2 h-4 w-4" /> Add Account
        </Button>
      </DialogPrimitive.Trigger>
      
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <DialogPrimitive.Content 
          className={cn(
            "fixed z-50 top-[50%] left-[50%] translate-x-[-50%] translate-y-[-50%]",
            "w-[calc(100%-32px)] sm:w-full sm:max-w-xl lg:max-w-2xl max-h-[85vh] rounded-md bg-white border p-0",
            "shadow-lg focus:outline-none flex flex-col overflow-hidden",
            "data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%]"
          )}
        >
          {/* Header - Fixed at top */}
          <div className="border-b p-4 sm:p-6 bg-white sticky top-0 z-10">
            <DialogPrimitive.Title className="text-xl text-primary font-bold">
              Add Account to Plan
            </DialogPrimitive.Title>
            <DialogPrimitive.Description className="text-sm text-muted-foreground">
              Select an existing account or create a new one to add to your money plan.
            </DialogPrimitive.Description>
          </div>
          
          {/* Content - Scrollable */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 pt-2 max-h-[calc(85vh-140px)]">
            {/* Remaining Balance Display */}
            {currentPlan && (
              <div className="bg-blue-50 border border-blue-100 p-4 rounded-md mb-4 text-center">
                <p className="text-sm font-medium text-blue-700">Remaining Plan Balance</p>
                <p className="text-2xl font-bold text-blue-800">{formatCurrency(currentPlan.remainingBalance)}</p>
              </div>
            )}
            
            <div className="space-y-6">
              {/* Account Selection Tabs */}
              <div className="space-y-6">
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                  <TabsList className="grid grid-cols-2 w-full">
                    <TabsTrigger 
                      value="existing" 
                      disabled={availableAccounts.length === 0 || isSubmitting}
                      className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary data-[state=active]:shadow-sm"
                    >
                      Use Existing Account
                    </TabsTrigger>
                    <TabsTrigger 
                      value="new"
                      disabled={isSubmitting}
                      className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary data-[state=active]:shadow-sm"
                    >
                      Create New Account
                    </TabsTrigger>
                  </TabsList>
                </Tabs>

                {activeTab === 'existing' ? (
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="account-select" className="text-right font-medium">
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
                          className="col-span-3 w-full focus:ring-primary focus:border-primary"
                        >
                          <SelectValue placeholder="Select an account" />
                        </SelectTrigger>
                        <SelectContent>
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
                    <Label htmlFor="new-account-name" className="text-right font-medium">
                      Account Name
                    </Label>
                    <Input
                      id="new-account-name"
                      className="col-span-3 focus:ring-primary focus:border-primary"
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
                <Label htmlFor="notes" className="text-right font-medium">
                  Notes
                </Label>
                <Textarea
                  id="notes"
                  className="col-span-3 focus:ring-primary focus:border-primary"
                  placeholder="Optional notes for this account allocation"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  disabled={isSubmitting}
                />
              </div>
              
              {/* Buckets Section */}
              <div className="mt-4">
                <h3 className="text-lg font-medium mb-2 flex items-center text-primary">
                  <span className="bg-primary/10 p-1 rounded-md mr-2">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-package"><path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>
                  </span>
                  Buckets
                </h3>
                <div className="space-y-4">
                  {buckets.map((bucket, index) => (
                    <div key={index} className="grid grid-cols-12 gap-2 items-center border p-3 rounded-md hover:border-primary/30 hover:bg-primary/5 transition-colors">
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
                          className="focus:ring-primary focus:border-primary"
                        />
                      </div>
                      <div className="col-span-5">
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
                            className="focus:ring-primary focus:border-primary"
                          >
                            <SelectValue placeholder="Select a category" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="need" className="text-blue-700">Need</SelectItem>
                            <SelectItem value="want" className="text-purple-700">Want</SelectItem>
                            <SelectItem value="savings/investing" className="text-green-700">Savings/Investing</SelectItem>
                            <SelectItem value="other" className="text-gray-700">Other</SelectItem>
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
                          className="focus:ring-primary focus:border-primary"
                        />
                      </div>
                      <div className="col-span-2 flex items-end justify-end">
                        {buckets.length > 1 && (
                          <Button
                            variant="outline"
                            size="icon"
                            onClick={() => handleRemoveBucket(index)}
                            disabled={isSubmitting}
                            className="hover:bg-red-50 hover:text-red-600 hover:border-red-200"
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
                    className="w-full border-dashed border-primary/50 text-primary hover:bg-primary/5"
                    onClick={handleAddBucket}
                    disabled={isSubmitting}
                  >
                    <Plus className="mr-2 h-4 w-4" /> Add Bucket
                  </Button>
                </div>
              </div>
            </div>
          </div>
          
          {/* Footer - Fixed at bottom */}
          <div className="border-t p-4 sm:p-6 bg-white sticky bottom-0 z-10 flex justify-end mt-auto">
            <Button 
              type="submit" 
              onClick={handleSubmit} 
              disabled={isSubmitting}
              className="bg-primary hover:bg-primary/90"
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
          </div>

          {/* Close button */}
          <DialogPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none">
            <X className="h-4 w-4" />
            <span className="sr-only">Close</span>
          </DialogPrimitive.Close>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
} 