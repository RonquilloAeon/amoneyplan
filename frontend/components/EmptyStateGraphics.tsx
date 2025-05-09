import React from 'react';

interface EmptyStateGraphicProps {
  className?: string;
  size?: number;
}

export function MoneyPlanGraphic({ className = '', size = 120 }: EmptyStateGraphicProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`text-gray-300 ${className}`}
    >
      <rect width="20" height="14" x="2" y="5" rx="2" />
      <line x1="2" x2="22" y1="10" y2="10" />
      <path d="M6 15h4" />
      <path d="M14 15h4" />
      <path d="M9 5v4" />
      <path d="M9 15v4" />
      <path d="M15 5v4" />
      <path d="M15 15v4" />
      <path d="M6 10h.01" />
      <path d="M12 10h.01" />
      <path d="M18 10h.01" />
    </svg>
  );
}

export function AccountsGraphic({ className = '', size = 120 }: EmptyStateGraphicProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`text-gray-300 ${className}`}
    >
      {/* Bank/Wallet Illustration */}
      <rect x="2" y="6" width="20" height="12" rx="2" />
      <path d="M2 10h20" />
      <path d="M12 6v12" />
      
      {/* Left side - represents savings/accounts */}
      <circle cx="7" cy="15" r="2" />
      <path d="M7 10v1" />
      
      {/* Right side - represents cards/payment methods */}
      <rect x="14" y="13" width="5" height="3" rx="1" />
      <path d="M17 10v1" />
    </svg>
  );
}

export function NewPlanGraphic({ className = '', size = 120 }: EmptyStateGraphicProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`text-gray-300 ${className}`}
    >
      {/* Calendar/Plan Sheet */}
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <line x1="3" x2="21" y1="8" y2="8" />
      
      {/* Calendar Markers */}
      <line x1="9" x2="9" y1="4" y2="8" />
      <line x1="15" x2="15" y1="4" y2="8" />
      
      {/* Money/Cash Flow Visualization */}
      <path d="M8 12h8" />
      <path d="M8 16h5" />
      <circle cx="17" cy="16" r="1" />

      {/* Plus Sign (indicating new plan) */}
      <circle cx="18" cy="6" r="2" />
      <path d="M18 5v2" />
      <path d="M17 6h2" />
    </svg>
  );
}

// Default export for convenience
export default {
  MoneyPlanGraphic,
  AccountsGraphic,
  NewPlanGraphic,
}; 