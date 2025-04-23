'use client';

import React, { useState, Suspense } from 'react';
import { signIn } from 'next-auth/react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Label } from '@/components/ui/label';
import { Loader2 } from 'lucide-react';

// Component containing the actual sign-in form logic
function SignInForm() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get('callbackUrl') || '/plans';
  
  // Check for error messages from NextAuth
  const errorType = searchParams.get('error');
  
  // Display appropriate error message based on error type
  useState(() => {
    if (errorType === 'CredentialsSignin') {
      setError('Invalid username or password');
    } else if (errorType) {
      setError('An error occurred during sign in');
    }
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!username || !password) {
      setError('Please enter both username and password');
      return;
    }
    
    setError(null);
    setIsLoading(true);
    
    try {
      const result = await signIn('credentials', {
        username,
        password,
        redirect: false,
      });
      
      if (result?.error) {
        setError(result.error || 'Sign in failed');
        setIsLoading(false);
      } else if (result?.ok) {
        // Redirect on successful login
        router.push(callbackUrl);
      }
    } catch (err) {
      setError('An unexpected error occurred');
      console.error(err);
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="text-2xl">Sign In</CardTitle>
        <CardDescription>
          Enter your credentials to access your account
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          <div className="space-y-2">
            <Label htmlFor="username">Username</Label>
            <Input 
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isLoading}
              placeholder="Enter your username"
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input 
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
              placeholder="Enter your password"
            />
          </div>
        </CardContent>
        
        <CardFooter className="flex flex-col space-y-3">
          <Button 
            type="submit" 
            className="w-full" 
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </Button>
          
          <div className="text-sm text-center mt-4">
            Don't have an account?{' '}
            <Link 
              href="/auth/register" 
              className="text-primary hover:underline"
            >
              Register
            </Link>
          </div>
        </CardFooter>
      </form>
    </Card>
  );
}

// Default export wraps the form in Suspense
export default function SignInPage() {
  return (
    <div className="flex justify-center items-center min-h-[80vh]">
      <Suspense fallback={<div>Loading sign-in form...</div>}>
        <SignInForm />
      </Suspense>
    </div>
  );
} 