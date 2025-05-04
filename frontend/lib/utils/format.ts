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
export function formatDate(dateString: string | Date, options: Intl.DateTimeFormatOptions = {}): string {
  let date: Date;

  if (dateString instanceof Date) {
    date = dateString;
  } else {
    // Check if the string is just a date (YYYY-MM-DD)
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
      // Parse as local date to avoid timezone shifts
      const [year, month, day] = dateString.split('-').map(Number);
      // Note: month is 0-indexed in Date constructor
      date = new Date(year, month - 1, day);
    } else {
      // Otherwise, parse as a full date-time string (assumes ISO 8601 or similar)
      date = new Date(dateString);
    }
  }

  // Check for invalid date
  if (isNaN(date.getTime())) {
    console.error("Invalid dateString passed to formatDate:", dateString);
    return "Invalid Date"; // Or handle appropriately
  }

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