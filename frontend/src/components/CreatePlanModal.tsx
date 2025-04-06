'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation } from '@apollo/client';
import { CREATE_PLAN } from '@/lib/graphql/operations';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';

const formSchema = z.object({
  initialBalance: z.string().transform((val) => parseFloat(val)),
  notes: z.string().optional(),
});

type FormData = z.infer<typeof formSchema>;

export function CreatePlanModal() {
  const [open, setOpen] = useState(false);
  const [createPlan] = useMutation(CREATE_PLAN);

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      initialBalance: '',
      notes: '',
    },
  });

  const onSubmit = async (data: FormData) => {
    try {
      await createPlan({
        variables: {
          input: {
            initialBalance: data.initialBalance,
            notes: data.notes || '',
          },
        },
      });
      setOpen(false);
      form.reset();
    } catch (error) {
      console.error('Error creating plan:', error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="default">Start a new money plan</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Start a new money plan</DialogTitle>
          <DialogDescription>
            Create a new money plan to manage your finances.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="initialBalance"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Initial Balance</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      className="text-foreground"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="notes"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Notes</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Add any notes about this plan"
                      className="text-foreground"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="flex justify-end space-x-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit">Create Plan</Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
} 