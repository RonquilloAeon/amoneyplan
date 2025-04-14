'use client';

import * as React from 'react';
import { formatCurrency } from '@/lib/utils/format';
import { Plan } from '@/lib/hooks/usePlans';
import { cn } from '@/lib/utils';

/**
 * Props for the PlanRemainingBalance component
 * @interface PlanRemainingBalanceProps
 * @property {Plan | null} plan - The current plan object containing remainingBalance
 * @property {number} [pendingAllocation=0] - The amount to subtract from the remainingBalance to show adjusted balance
 * @property {string} [className=''] - Additional CSS classes to apply to the component
 */
interface PlanRemainingBalanceProps {
  plan: Plan | null;
  pendingAllocation?: number;
  className?: string;
}

/**
 * Displays the remaining balance of a plan with adjustments for pending allocations
 * 
 * This component shows the remaining balance of a plan and adjusts it based on
 * pending allocations that haven't been saved yet. The balance will turn red
 * if it becomes negative due to pending allocations.
 * 
 * @param {PlanRemainingBalanceProps} props - Component props
 * @returns {JSX.Element | null} The rendered component or null if no plan is provided
 */
export function PlanRemainingBalance({ 
  plan, 
  pendingAllocation = 0,
  className = ''
}: PlanRemainingBalanceProps) {
  if (!plan) return null;
  
  const adjustedBalance = plan.remainingBalance - pendingAllocation;
  const isNegative = adjustedBalance < 0;
  
  return (
    <div className={cn(
      "bg-blue-50 border border-blue-100 p-3 sm:p-4 rounded-md text-center",
      "transition-all duration-200",
      className
    )}>
      <p className="text-xs sm:text-sm font-medium text-blue-700">Remaining Plan Balance</p>
      <p className={cn(
        "text-xl sm:text-2xl font-bold transition-colors",
        isNegative ? "text-red-600" : "text-blue-800"
      )}>
        {formatCurrency(adjustedBalance)}
      </p>
      {pendingAllocation > 0 && (
        <p className="text-xs text-blue-600 mt-1">
          *Includes pending allocation of {formatCurrency(pendingAllocation)}
        </p>
      )}
    </div>
  );
} 