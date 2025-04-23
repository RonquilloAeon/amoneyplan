'use client';

import { useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import Link from 'next/link';
import React, { Suspense } from 'react';

// New component containing the logic that uses useSearchParams
function AuthErrorContent() {
  const searchParams = useSearchParams();
  const error = searchParams.get('error') || 'Unknown error';
  
  // Map error codes to user-friendly messages
  const getErrorMessage = (errorCode: string) => {
    switch(errorCode) {
      case 'CredentialsSignin':
        return 'Invalid username or password. Please try again.';
      case 'SessionRequired':
        return 'You need to be signed in to access this page.';
      case 'AccessDenied':
        return 'You do not have permission to access this resource.';
      case 'Verification':
        return 'The verification link is invalid or has expired.';
      case 'Configuration':
        return 'There is a problem with the server configuration.';
      default:
        return 'An unknown error occurred during authentication.';
    }
  };
  
  const errorMessage = getErrorMessage(error);
  
  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="text-2xl">Authentication Error</CardTitle>
        <CardDescription>
          There was a problem authenticating your request
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Alert variant="destructive" className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{errorMessage}</AlertDescription>
        </Alert>
        
        <div className="text-sm text-muted-foreground mt-2">
          Error code: {error}
        </div>
      </CardContent>
      <CardFooter className="flex justify-center gap-4">
        <Button asChild variant="outline">
          <Link href="/auth/signin">Try Again</Link>
        </Button>
        <Button asChild>
          <Link href="/">Go Home</Link>
        </Button>
      </CardFooter>
    </Card>
  );
}

// Default export wraps the content component in Suspense
export default function AuthErrorPage() {
  return (
    <div className="flex items-center justify-center min-h-[80vh]">
      <Suspense fallback={<div>Loading error details...</div>}>
        <AuthErrorContent />
      </Suspense>
    </div>
  );
} 