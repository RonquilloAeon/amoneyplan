'use client';

import { useState } from 'react';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent, 
  CardFooter 
} from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Trash2, ChevronDown, ChevronUp, CreditCard, Edit } from 'lucide-react';
import { formatCurrency } from '@/lib/utils/format';
import { EditBucketsModal } from './EditBucketsModal';
import { usePlans } from '@/lib/hooks/usePlans';

export interface Bucket {
  id: string;
  name: string;
  category: string;
  allocatedAmount: number;
}

export interface Account {
  id: string;
  name: string;
}

export interface PlanAccount {
  id: string;
  account: Account;
  buckets: Bucket[];
  isChecked: boolean;
  notes: string;
}

interface PlanAccountCardProps {
  planAccount: PlanAccount;
  initialBalance?: number; // Plan's initial balance
  onRemove?: (id: string) => void;
  onUpdateNotes?: (id: string, notes: string) => void;
  onEdit?: (planAccount: PlanAccount) => void;
  editable?: boolean;
  highlighted?: boolean;
  viewMode?: 'grid' | 'list';
  planId: string; // Add planId to props
}

export function PlanAccountCard({ 
  planAccount, 
  initialBalance = 0,
  onRemove, 
  onUpdateNotes,
  onEdit,
  editable = true,
  highlighted = false,
  viewMode = 'grid',
  planId
}: PlanAccountCardProps) {
  const [expanded, setExpanded] = useState(viewMode === 'list');
  const { refetchDraft } = usePlans();
  
  const totalAllocated = planAccount.buckets.reduce(
    (sum, bucket) => sum + bucket.allocatedAmount, 
    0
  );

  // Calculate percentage of total allocated amount relative to initial balance
  const totalPercentage = initialBalance > 0 
    ? (totalAllocated / initialBalance) * 100 
    : 0;

  // Function to get the appropriate color for the progress bar
  const getProgressColor = (percentage: number) => {
    if (percentage <= 80) return 'bg-blue-500';
    if (percentage <= 95) return 'bg-amber-500';
    if (percentage <= 100) return 'bg-green-500';
    return 'bg-red-500';
  };

  const getCategoryColor = (category: string) => {
    // Simplify to just return the base color name that can be used in Tailwind classes
    const lowerCategory = category.toLowerCase();
    if (lowerCategory === 'need' || lowerCategory === 'savings' || lowerCategory === 'savings/investing') {
      return 'green';
    } else {
      return 'amber';
    }
  };

  return (
    <Card className={`relative overflow-hidden transition-all duration-200 ${
      highlighted ? 'border-primary border-2 shadow-md' : ''
    } ${viewMode === 'list' ? 'w-full' : ''}`}>
      
      <CardHeader className={`pb-2 ${viewMode === 'list' ? 'flex flex-row items-center justify-between' : ''}`}>
        <div className={`flex ${viewMode === 'list' ? 'flex-row items-center flex-1' : 'justify-between items-start'}`}>
          <div className="flex items-center">
            <CreditCard className="mr-2 h-5 w-5 text-primary" />
            <CardTitle className="text-xl">{planAccount.account.name}</CardTitle>
          </div>
          
          {viewMode === 'list' && (
            <div className="flex items-center space-x-4 mx-4">
              <div className="bg-primary/10 px-3 py-1 rounded-md flex items-center">
                <span className="text-sm font-medium text-primary">Total:</span>
                <div className="min-w-[100px] text-right">
                  <span className="ml-2 font-bold text-lg text-primary">
                    {formatCurrency(Number(totalAllocated))}
                  </span>
                </div>
                <div className="w-16 text-right">
                  <span className="ml-2 text-xs text-primary/80">
                    ({totalPercentage.toFixed(1)}%)
                  </span>
                </div>
              </div>
            </div>
          )}
          
          <div className="flex space-x-1">
            <Button 
              variant="ghost" 
              size="sm" 
              className="h-8 w-8 p-0"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? 
                <ChevronUp className="h-4 w-4" /> : 
                <ChevronDown className="h-4 w-4" />
              }
              <span className="sr-only">
                {expanded ? 'Collapse' : 'Expand'}
              </span>
            </Button>
            
            {editable && (
              <EditBucketsModal 
                planId={planId}
                planAccount={planAccount}
                onSuccess={() => {
                  refetchDraft();
                }}
              />
            )}
            
            {editable && onRemove && (
              <Button 
                variant="ghost" 
                size="sm" 
                className="h-8 w-8 p-0 hover:bg-destructive/10 hover:text-destructive"
                onClick={() => onRemove(planAccount.id)}
              >
                <Trash2 className="h-4 w-4" />
                <span className="sr-only">Remove account</span>
              </Button>
            )}
          </div>
        </div>
        
        {viewMode === 'grid' && (
          <>
            <CardDescription className="mt-2 flex justify-between items-center">
              <span>Total allocated</span>
              <span className="font-bold text-lg text-foreground">
                {formatCurrency(Number(totalAllocated))}
              </span>
            </CardDescription>
            
            {initialBalance > 0 && (
              <div className="mt-2 space-y-1">
                <div className="flex justify-between text-xs">
                  <span>Allocation</span>
                  <span className="font-medium">{totalPercentage.toFixed(1)}%</span>
                </div>
                <Progress 
                  value={totalPercentage} 
                  max={100} 
                  className="h-2"
                  indicatorClassName={getProgressColor(totalPercentage)}
                />
              </div>
            )}
          </>
        )}
      </CardHeader>
      
      <CardContent className="pb-2 space-y-3">
        {initialBalance > 0 && viewMode === 'list' && (
          <div className="w-full space-y-1 mb-3">
            <Progress 
              value={totalPercentage} 
              max={100} 
              className="h-2"
              indicatorClassName={getProgressColor(totalPercentage)}
            />
          </div>
        )}
        
        <div className={`space-y-2 transition-all duration-300 ${
          expanded ? 'max-h-full opacity-100' : 'max-h-[72px] overflow-hidden opacity-90'
        }`}>
          {planAccount.buckets.length > 0 ? (
            planAccount.buckets.map((bucket) => {
              // Calculate the bucket's percentage of the initial balance
              const bucketPercentage = initialBalance > 0 
                ? (bucket.allocatedAmount / initialBalance) * 100 
                : 0;
                
              return (
                <div key={bucket.id} className={`flex items-center justify-between rounded-md p-2 hover:bg-accent/50 ${
                  viewMode === 'list' ? 'border-b border-gray-100 last:border-0' : ''
                }`}>
                  <div className="flex items-center flex-1">
                    <div className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold mr-2 ${
                      getCategoryColor(bucket.category) === 'green' 
                        ? 'bg-green-200 text-green-800 border-green-200 dark:bg-green-800 dark:text-green-100 dark:border-green-700'
                        : 'bg-amber-300 text-amber-800 border-amber-200 dark:bg-amber-800 dark:text-amber-100 dark:border-amber-700'
                    }`}>
                      {bucket.category.charAt(0).toUpperCase() + bucket.category.slice(1)}
                    </div>
                    <span className="font-medium">{bucket.name}</span>
                  </div>
                  <div className="flex items-center min-w-[120px]">
                    <div className="flex-1 text-right">
                      <span className="font-medium">{formatCurrency(bucket.allocatedAmount)}</span>
                    </div>
                    {initialBalance > 0 && (
                      <div className="w-16 text-right">
                        <span className="text-xs text-muted-foreground ml-2">
                          ({bucketPercentage.toFixed(1)}%)
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          ) : (
            <p className="text-sm text-muted-foreground italic bg-muted p-2 rounded">
              No buckets configured
            </p>
          )}
        </div>
        
        {!expanded && planAccount.buckets.length > 2 && (
          <Button 
            variant="ghost" 
            size="sm" 
            className="w-full text-xs py-0 h-6"
            onClick={() => setExpanded(true)}
          >
            Show all ({planAccount.buckets.length}) buckets <ChevronDown className="ml-1 h-3 w-3" />
          </Button>
        )}
      </CardContent>
      
      {(editable || planAccount.notes) && (
        <CardFooter className="pt-2">
          {editable && onUpdateNotes ? (
            <Textarea 
              value={planAccount.notes || ''} 
              placeholder="Add notes for this account..."
              className="text-foreground text-sm min-h-[60px] resize-none focus:border-primary"
              onChange={(e) => onUpdateNotes(planAccount.id, e.target.value)}
            />
          ) : planAccount.notes ? (
            <div className="text-sm rounded-md bg-accent/30 p-3 w-full">
              <p className="text-foreground">{planAccount.notes}</p>
            </div>
          ) : null}
        </CardFooter>
      )}
    </Card>
  );
} 