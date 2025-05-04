'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useQuery } from '@apollo/client';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { usePlans, Plan } from '@/lib/hooks/usePlans';
import { Textarea } from '@/components/ui/textarea';
import { Loader2 } from 'lucide-react';
import { useToast } from '@/lib/hooks/useToast';
import { GET_PLANS } from '@/lib/graphql/operations';
import { formatDate } from '@/lib/utils/format';

export function StartPlanModal() {
  const { data: session } = useSession();
  const [open, setOpen] = useState(false);
  const [initialBalance, setInitialBalance] = useState('');
  const [notes, setNotes] = useState('');
  const [date, setDate] = useState<Date>(new Date());
  const [copyFromPlanId, setCopyFromPlanId] = useState<string | undefined>(undefined);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const { createPlan, refetchDraft } = usePlans();

  const { data: plansData, loading: plansLoading, error: plansError } = useQuery(GET_PLANS, {
    variables: {
      first: 10,
      filter: { isArchived: false, status: 'committed' },
    },
    skip: !session || !open,
    fetchPolicy: 'cache-and-network',
  });

  const recentPlans: Plan[] = plansData?.moneyPlans?.edges?.map((edge: { node: Plan }) => edge.node) || [];

  useEffect(() => {
    if (plansError) {
      toast({
        variant: "destructive",
        title: "Error loading plans",
        description: plansError.message,
      });
    }
  }, [plansError, toast]);

  const handleSubmit = async () => {
    if (!initialBalance || parseFloat(initialBalance) <= 0) {
      toast({
        variant: "destructive",
        title: "Validation Error",
        description: "Please enter a valid initial balance greater than zero"
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const input = {
        initialBalance: parseFloat(initialBalance),
        notes: notes.trim() || undefined,
        planDate: date.toISOString().split('T')[0],
        copyFrom: copyFromPlanId || undefined,
      };
      console.log("Creating plan with input:", input);
      
      const result = await createPlan(input);

      if (result) {
        toast({
          title: "Success",
          description: "New plan started",
          variant: "success",
        });
        setOpen(false);
        setInitialBalance('');
        setNotes('');
        setDate(new Date());
        setCopyFromPlanId(undefined);
      }
    } catch (err) {
      console.error('Failed to create plan:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Start New Plan</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px] bg-white dark:bg-gray-950">
        <DialogHeader>
          <DialogTitle>Start New Money Plan</DialogTitle>
          <DialogDescription>
            Start a fresh plan or copy the structure from a previous one.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="initial-balance" className="text-right">
              Initial Balance
            </Label>
            <Input
              id="initial-balance"
              type="number"
              className="col-span-3"
              placeholder="0.00"
              value={initialBalance}
              onChange={(e) => setInitialBalance(e.target.value)}
              disabled={isSubmitting}
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="plan-date" className="text-right">
              Plan Date
            </Label>
            <Input
              id="plan-date"
              type="date"
              className="col-span-3"
              value={date.toISOString().split('T')[0]}
              onChange={(e) => {
                if (e.target.value) {
                  const [year, month, day] = e.target.value.split('-').map(Number);
                  setDate(new Date(year, month - 1, day)); 
                }
              }}
              disabled={isSubmitting}
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="copy-from" className="text-right">
              Copy Structure
            </Label>
            <Select
              value={copyFromPlanId}
              onValueChange={(value) => setCopyFromPlanId(value === 'none' ? undefined : value)}
              disabled={isSubmitting || plansLoading}
            >
              <SelectTrigger id="copy-from" className="col-span-3">
                <SelectValue placeholder={plansLoading ? "Loading plans..." : "Start from scratch"} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Start from scratch</SelectItem>
                {recentPlans.map((plan) => (
                  <SelectItem key={plan.id} value={plan.id}>
                    Plan from {formatDate(plan.planDate || plan.createdAt)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="notes" className="text-right">
              Notes
            </Label>
            <Textarea
              id="notes"
              className="col-span-3"
              placeholder="Optional notes about this plan"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              disabled={isSubmitting}
            />
          </div>
        </div>
        <DialogFooter>
          <Button type="submit" onClick={handleSubmit} disabled={isSubmitting || plansLoading}>
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating...
              </>
            ) : (
              'Create Plan'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
} 