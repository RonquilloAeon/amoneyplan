'use client';

import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body>
        <div className="flex flex-col items-center justify-center min-h-screen px-4">
          <div className="w-full max-w-md space-y-6">
            <div className="flex flex-col items-center text-center space-y-3">
              <AlertCircle className="h-12 w-12 text-red-500" />
              <h2 className="text-2xl font-semibold">Critical Error</h2>
              <p className="text-gray-500">
                {error.message || 'A critical error occurred. Please try again.'}
              </p>
            </div>

            <div className="flex justify-center space-x-4">
              <Button 
                className="bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded"
                onClick={() => window.location.href = '/'}
              >
                Go Home
              </Button>
              <Button 
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
                onClick={() => reset()}
              >
                Try Again
              </Button>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
} 