/**
 * Formats a number or string to a currency string
 */
export function formatCurrency(value: number | string): string {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(num);
}

/**
 * Formats a date string to a readable format
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(date);
}

/**
 * Calculates the total balance of a plan or plan account
 */
export function calculateTotalBalance(item: any): number {
  // For a plan, sum up all accounts
  if (item.accounts) {
    return item.accounts.reduce((total: number, account: any) => {
      return total + calculateTotalBalance(account);
    }, 0);
  }
  
  // For a plan account, sum up all buckets
  if (item.buckets) {
    return item.buckets.reduce((total: number, bucket: any) => {
      return total + bucket.allocatedAmount;
    }, 0);
  }
  
  return 0;
} 