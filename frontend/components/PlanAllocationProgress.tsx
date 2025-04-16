'use client';

import * as React from 'react';
import { MultiProgress, ProgressSegment } from '@/components/ui/multi-progress';
import { Bucket } from './PlanAccountCard';
import { getCategoryStyles } from '@/lib/constants/bucketCategories';
import { formatCurrency } from '@/lib/utils/format';

interface PlanAllocationProgressProps {
  buckets: Bucket[];
  initialBalance: number;
  height?: string;
  showLabels?: boolean;
  showPercentages?: boolean;
  showAmounts?: boolean;
  className?: string;
}

// Map category values to vibrant colors for the progress bar
const getCategoryColor = (category: string): string => {
  switch(category) {
    case 'need':
      return 'bg-blue-500';
    case 'want':
      return 'bg-yellow-500';
    case 'savings/investing':
      return 'bg-green-500';
    case 'other':
      return 'bg-amber-500';
    default:
      return 'bg-gray-500';
  }
};

// Define category order for consistent display
const CATEGORY_ORDER = ['need', 'want', 'savings/investing', 'other'];

const PlanAllocationProgress: React.FC<PlanAllocationProgressProps> = ({
  buckets,
  initialBalance,
  height = 'h-3',
  showLabels = true,
  showPercentages = true,
  showAmounts = false,
  className = '',
}) => {
  // Group buckets by category and sum their allocated amounts
  const categoryTotals = buckets.reduce((acc, bucket) => {
    const category = bucket.category;
    if (!acc[category]) {
      acc[category] = 0;
    }
    acc[category] += bucket.allocatedAmount;
    return acc;
  }, {} as Record<string, number>);

  // Sort segments by defined category order and convert to array for the multi-progress bar
  const segments: ProgressSegment[] = CATEGORY_ORDER
    .filter(category => categoryTotals[category] !== undefined)
    .map(category => {
      const amount = categoryTotals[category] || 0;
      // Calculate percentage of the initial balance for this category
      const percentage = initialBalance > 0 ? (amount / initialBalance) * 100 : 0;
      
      // Use more vibrant colors for the progress bar
      const bgColor = getCategoryColor(category);
      
      return {
        value: percentage,
        color: bgColor,
      };
    });

  // Calculate the total allocated percentage
  const totalAllocated = buckets.reduce((sum, bucket) => sum + bucket.allocatedAmount, 0);
  const totalPercentage = initialBalance > 0 ? (totalAllocated / initialBalance) * 100 : 0;

  // Get sorted category entries for the legend
  const sortedCategories = CATEGORY_ORDER
    .filter(category => categoryTotals[category] !== undefined);

  return (
    <div className={`space-y-2 ${className}`}>
      {showLabels && (
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm font-medium">Allocation Progress</span>
          <div className="flex items-center gap-1">
            {showAmounts && (
              <span className="text-sm font-medium mr-2">
                {formatCurrency(totalAllocated)} / {formatCurrency(initialBalance)}
              </span>
            )}
            {showPercentages && (
              <span className="text-sm font-medium">
                {totalPercentage.toFixed(1)}%
              </span>
            )}
          </div>
        </div>
      )}
      
      <MultiProgress 
        segments={segments} 
        className={height}
        totalMaxValue={100}
      />
      
      {/* Category legend */}
      {showLabels && segments.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {sortedCategories.map(category => {
            const amount = categoryTotals[category];
            const percentage = initialBalance > 0 ? (amount / initialBalance) * 100 : 0;
            // For the legend, use the same vibrant colors as the progress bar
            const bgColor = getCategoryColor(category);
            
            return (
              <div key={category} className="flex items-center text-xs">
                <div className={`w-3 h-3 rounded-full mr-1 ${bgColor}`}></div>
                <span className="font-medium">{category.charAt(0).toUpperCase() + category.slice(1)}</span>
                {showPercentages && (
                  <span className="text-muted-foreground ml-1">
                    ({percentage.toFixed(1)}%)
                  </span>
                )}
                {showAmounts && (
                  <span className="text-muted-foreground ml-1">
                    ({formatCurrency(amount)})
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export { PlanAllocationProgress }; 