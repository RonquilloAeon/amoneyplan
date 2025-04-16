/**
 * Format a number as currency
 */
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

/**
 * Format a date using specified options
 */
export function formatDate(dateString: string, options: Intl.DateTimeFormatOptions = {}): string {
  const date = new Date(dateString);
  
  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...options
  };
  
  return new Intl.DateTimeFormat('en-US', defaultOptions).format(date);
}

/**
 * Calculate total balance from a plan
 */
export function calculateTotalBalance(plan: any): number {
  if (!plan || !plan.accounts) return 0;
  
  return plan.accounts.reduce((total: number, account: any) => {
    const accountTotal = account.buckets.reduce(
      (sum: number, bucket: any) => sum + (Number(bucket.allocatedAmount) || 0), 
      0
    );
    return total + accountTotal;
  }, 0);
} 