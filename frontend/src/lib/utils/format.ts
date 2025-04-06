export const formatCurrency = (amount: number, currency: string = 'USD'): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(amount);
};

export const formatDate = (date: string | Date): string => {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
};

export const formatAccountType = (type: string): string => {
  return type.charAt(0) + type.slice(1).toLowerCase();
};

export const calculateTotalBalance = (accounts: Array<{ balance: number; currency: string }>): string => {
  const totalsByCurrency = accounts.reduce((acc, account) => {
    acc[account.currency] = (acc[account.currency] || 0) + account.balance;
    return acc;
  }, {} as Record<string, number>);

  return Object.entries(totalsByCurrency)
    .map(([currency, amount]) => formatCurrency(amount, currency))
    .join(' + ');
}; 