import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const accountSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  balance: z.number().min(0, 'Balance must be positive'),
  accountType: z.enum(['CHECKING', 'SAVINGS', 'CREDIT', 'INVESTMENT']),
  currency: z.string().default('USD'),
});

type AccountFormData = z.infer<typeof accountSchema>;

interface AccountFormProps {
  initialData?: AccountFormData;
  onSubmit: (data: AccountFormData) => void;
  onCancel: () => void;
}

export const AccountForm = ({ initialData, onSubmit, onCancel }: AccountFormProps) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AccountFormData>({
    resolver: zodResolver(accountSchema),
    defaultValues: initialData,
  });

  const onSubmitForm = async (data: AccountFormData) => {
    try {
      setIsSubmitting(true);
      await onSubmit(data);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmitForm)} className="space-y-4">
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700">
          Account Name
        </label>
        <input
          type="text"
          id="name"
          {...register('name')}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="balance" className="block text-sm font-medium text-gray-700">
          Balance
        </label>
        <input
          type="number"
          id="balance"
          step="0.01"
          {...register('balance', { valueAsNumber: true })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
        {errors.balance && (
          <p className="mt-1 text-sm text-red-600">{errors.balance.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="accountType" className="block text-sm font-medium text-gray-700">
          Account Type
        </label>
        <select
          id="accountType"
          {...register('accountType')}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        >
          <option value="CHECKING">Checking</option>
          <option value="SAVINGS">Savings</option>
          <option value="CREDIT">Credit</option>
          <option value="INVESTMENT">Investment</option>
        </select>
        {errors.accountType && (
          <p className="mt-1 text-sm text-red-600">{errors.accountType.message}</p>
        )}
      </div>

      <div className="flex justify-end space-x-3">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          {isSubmitting ? 'Saving...' : 'Save'}
        </button>
      </div>
    </form>
  );
}; 