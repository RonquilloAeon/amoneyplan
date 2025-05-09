import React, { ReactNode } from 'react';
import { MoneyPlanGraphic } from './EmptyStateGraphics';

interface EmptyStateProps {
  graphic?: ReactNode;
  title: string;
  description: string | string[];
  actionInstruction?: string;
  actionInstructionHighlight?: string;
  additionalContent?: ReactNode;
  className?: string;
}

export function EmptyState({
  graphic,
  title,
  description,
  actionInstruction,
  actionInstructionHighlight,
  additionalContent,
  className = '',
}: EmptyStateProps) {
  // We've removed the default icon since we now use specific graphics from EmptyStateGraphics

  // Handle array or string for description
  const descriptionArray = Array.isArray(description) ? description : [description];

  return (
    <div className={`text-center py-12 px-6 md:px-12 border rounded-lg bg-gray-50 ${className}`}>
      {/* Graphic */}
      {graphic && (
        <div className="flex justify-center mb-6">
          {graphic}
        </div>
      )}

      {/* Title */}
      <h3 className="text-lg font-medium mb-2">{title}</h3>

      {/* Description paragraphs */}
      {descriptionArray.map((paragraph, index) => (
        <p key={index} className="text-muted-foreground mb-4">
          {paragraph}
        </p>
      ))}

      {/* Additional content (buttons, etc.) */}
      {additionalContent && (
        <div className="mt-4 mb-4">
          {additionalContent}
        </div>
      )}

      {/* Action instruction with arrow */}
      {actionInstruction && (
        <div className="flex items-center justify-center mt-8">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-gray-400 mr-2"
          >
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 19 12 12 19"></polyline>
          </svg>
          <p className="text-gray-500">
            {actionInstruction}{' '}
            {actionInstructionHighlight && (
              <span className="font-medium text-primary">{actionInstructionHighlight}</span>
            )}{' '}
            to get started.
          </p>
        </div>
      )}
    </div>
  );
} 