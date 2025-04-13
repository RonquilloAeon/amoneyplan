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
import { Trash2, ChevronDown, ChevronUp, CreditCard } from 'lucide-react';
import { formatCurrency } from '@/lib/utils/format';

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
  onRemove?: (id: string) => void;
  onUpdateNotes?: (id: string, notes: string) => void;
  editable?: boolean;
  highlighted?: boolean;
}

export function PlanAccountCard({ 
  planAccount, 
  onRemove, 
  onUpdateNotes,
  editable = true,
  highlighted = false
}: PlanAccountCardProps) {
  const [expanded, setExpanded] = useState(false);
  
  const totalAllocated = planAccount.buckets.reduce(
    (sum, bucket) => sum + bucket.allocatedAmount, 
    0
  );

  const getCategoryColor = (category: string) => {
    console.log('category', category);
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
    }`}>
      
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <div className="flex items-center">
            <CreditCard className="mr-2 h-5 w-5 text-primary" />
            <CardTitle className="text-xl">{planAccount.account.name}</CardTitle>
          </div>
          
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
        
        <CardDescription className="mt-2 flex justify-between items-center">
          <span>Total allocated</span>
          <span className="font-medium text-foreground">
            {formatCurrency(Number(totalAllocated))}
          </span>
        </CardDescription>
      </CardHeader>
      
      <CardContent className="pb-2 space-y-3">
        <div className={`space-y-2 transition-all duration-300 ${
          expanded ? 'max-h-80 opacity-100' : 'max-h-[72px] overflow-hidden opacity-90'
        }`}>
          {planAccount.buckets.length > 0 ? (
            planAccount.buckets.map((bucket) => (
              <div key={bucket.id} className="flex items-center justify-between rounded-md p-2 hover:bg-accent/50">
                <div className="flex items-center">
                  <div className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold mr-2 ${
                    getCategoryColor(bucket.category) === 'green' 
                      ? 'bg-green-200 text-green-800 border-green-200 dark:bg-green-800 dark:text-green-100 dark:border-green-700'
                      : 'bg-amber-300 text-amber-800 border-amber-200 dark:bg-amber-800 dark:text-amber-100 dark:border-amber-700'
                  }`}>
                    {bucket.category.charAt(0).toUpperCase() + bucket.category.slice(1)}
                  </div>
                  <span className="font-medium">{bucket.name}</span>
                </div>
                <span className="font-medium">{formatCurrency(bucket.allocatedAmount)}</span>
              </div>
            ))
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