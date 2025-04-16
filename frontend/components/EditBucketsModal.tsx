'use client';

import * as React from 'react';
import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X, Plus, Trash2, Loader2, Edit } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { usePlans } from '@/lib/hooks/usePlans';
import { BucketConfigInput, PlanAccount } from '@/lib/hooks/usePlans';
import { formatCurrency } from '@/lib/utils/format';
import { cn } from '@/lib/utils';
import { useToast } from '@/lib/hooks/useToast';
import { BUCKET_CATEGORIES } from '@/lib/constants/bucketCategories';
import { PlanRemainingBalance } from '@/components/PlanRemainingBalance';

interface BucketFormState {
  name: string;
  category: string;
  allocatedAmount: string;
}

interface EditBucketsModalProps {
  planId: string;
  planAccount: PlanAccount;
  onSuccess?: () => void;
}

export function EditBucketsModal({ planId, planAccount, onSuccess }: EditBucketsModalProps) {
  const [open, setOpen] = useState(false);
  const [buckets, setBuckets] = useState<BucketFormState[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();
  const { updatePlanAccount, draftPlan } = usePlans();
  const [accountToEdit, setAccountToEdit] = useState<PlanAccount>(planAccount);
  const [pendingAllocation, setPendingAllocation] = useState<number>(0);
  const [originalAllocation, setOriginalAllocation] = useState<number>(0);

  // Update local account data when prop changes
  useEffect(() => {
    setAccountToEdit(planAccount);
  }, [planAccount]);

  // Initialize buckets from the accountToEdit when opening the modal
  useEffect(() => {
    if (open && accountToEdit) {
      const initialBuckets = accountToEdit.buckets.map(bucket => ({
        name: bucket.name,
        category: bucket.category,
        allocatedAmount: bucket.allocatedAmount.toString()
      }));
      
      // Calculate the original total allocation
      const initialTotal = accountToEdit.buckets.reduce((sum, bucket) => {
        return sum + (bucket.allocatedAmount || 0);
      }, 0);
      setOriginalAllocation(initialTotal);
      
      setBuckets(initialBuckets.length > 0 ? initialBuckets : [
        { name: 'Default', category: '', allocatedAmount: '' }
      ]);
    }
  }, [open, accountToEdit]);

  // Calculate pending allocation changes
  useEffect(() => {
    const currentTotal = buckets.reduce((sum, bucket) => {
      return sum + (parseFloat(bucket.allocatedAmount) || 0);
    }, 0);
    
    // The pending allocation is the difference between current and original
    setPendingAllocation(currentTotal - originalAllocation);
  }, [buckets, originalAllocation]);

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
    
    // Immediately recalculate pending allocation when an amount changes
    if (field === 'allocatedAmount') {
      const currentTotal = newBuckets.reduce((sum, bucket) => {
        return sum + (parseFloat(bucket.allocatedAmount) || 0);
      }, 0);
      
      // The pending allocation is the difference between current and original
      setPendingAllocation(currentTotal - originalAllocation);
    }
  };

  const validateForm = (): boolean => {
    // Check if all buckets have names, categories, and amounts
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
      
      // Check if allocatedAmount is explicitly set (can be 0)
      if (buckets[i].allocatedAmount === '' || buckets[i].allocatedAmount === null || buckets[i].allocatedAmount === undefined) {
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

      // Update bucket configuration for the account
      await updatePlanAccount(planId, accountToEdit.id, bucketConfigs);
      
      // Reset form and close modal
      setOpen(false);
      
      // Show success toast
      toast({
        title: "Success",
        description: "Bucket configuration successfully updated"
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
          description: "An error occurred while updating the buckets"
        });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Find the current plan and get remaining balance
  const currentPlan = draftPlan?.id === planId ? draftPlan : null;

  return (
    <DialogPrimitive.Root open={open} onOpenChange={(newOpen) => {
      setOpen(newOpen);
      if (!newOpen) {
        // Reset buckets when closing the modal without saving
        setBuckets([]);
        setPendingAllocation(0);
        setOriginalAllocation(0);
        if (onSuccess) {
          onSuccess(); // Notify parent that the modal was closed
        }
      }
    }}>
      <DialogPrimitive.Trigger asChild>
        <Button 
          variant="ghost" 
          size="sm" 
          className="h-8 w-8 p-0 hover:bg-primary/10 hover:text-primary"
        >
          <Edit className="h-4 w-4" />
          <span className="sr-only">Edit buckets</span>
        </Button>
      </DialogPrimitive.Trigger>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <DialogPrimitive.Content className="fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-white p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg">
          <div className="flex flex-col h-[80vh] max-h-[600px]">
            <div className="flex items-center justify-between">
              <DialogPrimitive.Title className="text-xl font-bold">
                Edit Buckets for {accountToEdit.account.name}
              </DialogPrimitive.Title>
              <DialogPrimitive.Close asChild>
                <Button variant="ghost" className="h-8 w-8 p-0 rounded-full" aria-label="Close">
                  <X className="h-4 w-4" />
                </Button>
              </DialogPrimitive.Close>
            </div>
            
            <div className="mt-4 overflow-y-auto flex-grow pr-2">
              {/* Add the PlanRemainingBalance component at the top */}
              <PlanRemainingBalance 
                plan={currentPlan} 
                pendingAllocation={pendingAllocation}
                className="mb-6"
              />
                
              {/* Buckets */}
              <div className="space-y-4 mb-8">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium">Bucket Configuration</h3>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleAddBucket} 
                    className="px-3"
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Add Bucket
                  </Button>
                </div>

                <div className="space-y-3">
                  {buckets.map((bucket, index) => (
                    <div 
                      key={index} 
                      className={cn(
                        "flex flex-col space-y-3 p-3 rounded-md",
                        "border-2 border-gray-200",
                        "hover:border-primary/50 focus-within:border-primary/50 transition-colors"
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium">Bucket #{index + 1}</h4>
                        {buckets.length > 1 && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveBucket(index)}
                            className="h-8 w-8 p-0 text-destructive hover:bg-destructive/10 hover:text-destructive"
                          >
                            <Trash2 className="h-4 w-4" />
                            <span className="sr-only">Remove bucket</span>
                          </Button>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-1 gap-3">
                        <div className="space-y-1">
                          <Label htmlFor={`bucket-name-${index}`}>Name</Label>
                          <Input
                            id={`bucket-name-${index}`}
                            value={bucket.name}
                            onChange={(e) => handleBucketChange(index, 'name', e.target.value)}
                            placeholder="e.g., Groceries, Rent, Savings"
                          />
                        </div>
                        
                        <div className="space-y-1">
                          <Label htmlFor={`bucket-category-${index}`}>Category</Label>
                          <Select
                            value={bucket.category}
                            onValueChange={(value) => handleBucketChange(index, 'category', value)}
                          >
                            <SelectTrigger id={`bucket-category-${index}`}>
                              <SelectValue placeholder="Select a category" />
                            </SelectTrigger>
                            <SelectContent>
                              {BUCKET_CATEGORIES.map((category) => (
                                <SelectItem 
                                  key={category.value} 
                                  value={category.value}
                                  className={`text-${category.color}`}
                                >
                                  {category.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        
                        <div className="space-y-1">
                          <Label htmlFor={`bucket-amount-${index}`}>Amount</Label>
                          <div className="relative">
                            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                            <Input
                              id={`bucket-amount-${index}`}
                              type="number"
                              step="0.01"
                              min="0"
                              value={bucket.allocatedAmount}
                              onChange={(e) => handleBucketChange(index, 'allocatedAmount', e.target.value)}
                              className="pl-7"
                              placeholder="0.00"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="flex justify-end space-x-2 pt-4 mt-auto border-t">
              <DialogPrimitive.Close asChild>
                <Button variant="outline">Cancel</Button>
              </DialogPrimitive.Close>
              <Button 
                onClick={handleSubmit} 
                disabled={isSubmitting}
                className="bg-primary hover:bg-primary/90"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Updating...
                  </>
                ) : (
                  'Save Changes'
                )}
              </Button>
            </div>
          </div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
} 