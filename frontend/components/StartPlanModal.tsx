'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { usePlans } from '@/lib/hooks/usePlans';
import { Textarea } from '@/components/ui/textarea';
import { Loader2 } from 'lucide-react';
import { useToast } from '@/lib/hooks/useToast';

export function StartPlanModal() {
  const { data: session } = useSession();
  const [open, setOpen] = useState(false);
  const [initialBalance, setInitialBalance] = useState('');
  const [notes, setNotes] = useState('');
  const [date, setDate] = useState<Date>(new Date());
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const { createPlan, refetchDraft } = usePlans();

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
      const result = await createPlan({
        initialBalance: parseFloat(initialBalance),
        notes: notes.trim() || undefined,
        planDate: date.toISOString().split('T')[0]
      });

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
      }
    } catch (err) {
      // Error is handled in the usePlans hook with toast
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
            Start a fresh plan to allocate your finances.
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
                  setDate(new Date(e.target.value));
                }
              }}
              disabled={isSubmitting}
            />
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
          <Button type="submit" onClick={handleSubmit} disabled={isSubmitting}>
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