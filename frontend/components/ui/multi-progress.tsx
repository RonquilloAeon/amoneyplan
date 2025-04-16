"use client"

import * as React from "react"
import * as ProgressPrimitive from "@radix-ui/react-progress"

import { cn } from "@/lib/utils"

export interface ProgressSegment {
  value: number;
  color: string;
}

interface MultiProgressProps extends 
  Omit<React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>, 'value'> {
  segments: ProgressSegment[];
  className?: string;
  totalMaxValue?: number;
}

const MultiProgress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  MultiProgressProps
>(({ className, segments, totalMaxValue = 100, ...props }, ref) => {
  // Calculate the total value of all segments
  const totalValue = segments.reduce((acc, segment) => acc + segment.value, 0)
  
  // Ensure progress never exceeds 100%
  const clampedTotalValue = Math.min(totalValue, totalMaxValue)
  
  // Scale factors if total is over 100%
  const scaleFactor = totalValue > totalMaxValue ? totalMaxValue / totalValue : 1
  
  return (
    <ProgressPrimitive.Root
      ref={ref}
      className={cn(
        "relative h-4 w-full overflow-hidden rounded-full bg-secondary",
        className
      )}
      {...props}
    >
      <div className="flex h-full w-full">
        {segments.map((segment, index) => {
          // Calculate the percentage width for this segment (clamped to ensure no overflow)
          const scaledValue = segment.value * scaleFactor
          const percentWidth = (scaledValue / totalMaxValue) * 100
          
          return (
            <div
              key={index}
              className={cn("h-full transition-all", segment.color)}
              style={{ width: `${percentWidth}%` }}
            />
          )
        })}
      </div>
    </ProgressPrimitive.Root>
  )
})
MultiProgress.displayName = "MultiProgress"

export { MultiProgress } 