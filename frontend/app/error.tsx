'use client';

import { useEffect } from 'react';
import { Button } from '../src/components/ui/button';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <h1 className="text-4xl font-bold">Something went wrong!</h1>
      <p className="mt-4 text-center mb-8">
        An unexpected error has occurred. Please try again later.
      </p>
      <Button onClick={reset}>Try again</Button>
    </div>
  );
} 