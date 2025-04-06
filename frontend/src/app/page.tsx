'use client';

import { useState } from 'react';
import { useMutation } from '@apollo/client';
import { CREATE_PLAN } from '@/lib/graphql/operations';
import Layout from '@/components/layout/Layout';
import { AccountForm } from '@/components/accounts/AccountForm';

export default function CreatePlanPage() {
  const [initialBalance, setInitialBalance] = useState<number>(0);
  const [planNotes, setPlanNotes] = useState('');
  const [planDate, setPlanDate] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [createPlan] = useMutation(CREATE_PLAN, {
    onCompleted: (data) => {
      // Handle success
      console.log('Plan created:', data);
    },
    onError: (error) => {
      console.error('Error creating plan:', error);
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await createPlan({
        variables: {
          input: {
            initialBalance: parseFloat(initialBalance.toString()),
            notes: planNotes,
            planDate: planDate || null,
          },
        },
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Create a New Plan</h1>
        
        <form onSubmit={handleSubmit} className="space-y-8">
          <div>
            <label htmlFor="initialBalance" className="block text-sm font-medium text-gray-700">
              Initial Balance
            </label>
            <input
              type="number"
              id="initialBalance"
              value={initialBalance}
              onChange={(e) => setInitialBalance(parseFloat(e.target.value))}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              required
              min="0"
              step="0.01"
            />
          </div>

          <div>
            <label htmlFor="planDate" className="block text-sm font-medium text-gray-700">
              Plan Date
            </label>
            <input
              type="date"
              id="planDate"
              value={planDate}
              onChange={(e) => setPlanDate(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label htmlFor="planNotes" className="block text-sm font-medium text-gray-700">
              Notes
            </label>
            <textarea
              id="planNotes"
              value={planNotes}
              onChange={(e) => setPlanNotes(e.target.value)}
              rows={3}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              {isSubmitting ? 'Creating Plan...' : 'Create Plan'}
            </button>
          </div>
        </form>
      </div>
    </Layout>
  );
} 