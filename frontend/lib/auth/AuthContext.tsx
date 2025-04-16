'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useSession, signIn, signOut } from 'next-auth/react';
// import { useMutation, useQuery, gql } from '@apollo/client';

// Define user type
interface User {
  id: string;
  username: string;
  email: string;
  firstName?: string;
  lastName?: string;
}

// Auth context type
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (
    username: string,
    email: string,
    password: string,
    firstName?: string,
    lastName?: string
  ) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
}

// Register data type
interface RegisterData {
  username: string;
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
}

// Create the auth context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth provider props
interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const { data: session, status } = useSession();
  const [user, setUser] = useState<User | null>(null);
  
  // Set auth state based on NextAuth session
  useEffect(() => {
    if (session && session.user) {
      setUser({
        id: session.user.id as string,
        username: session.user.name || '',
        email: session.user.email || '',
        firstName: session.user.firstName as string | undefined,
        lastName: session.user.lastName as string | undefined
      });
    } else {
      setUser(null);
    }
  }, [session]);

  const isAuthenticated = !!session;
  const isLoading = status === 'loading';

  // Login function using NextAuth
  const login = async (username: string, password: string) => {
    try {
      const result = await signIn('credentials', {
        username,
        password,
        redirect: false
      });

      if (!result?.error) {
        return { success: true };
      } else {
        return { 
          success: false, 
          error: result.error || 'Login failed' 
        };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false,
        error: (error as Error).message || 'An unexpected error occurred' 
      };
    }
  };

  // Register function
  const register = async (
    username: string,
    email: string,
    password: string,
    firstName?: string,
    lastName?: string
  ) => {
    try {
      // Construct the data object from arguments
      const data: RegisterData = { username, email, password, firstName, lastName };

      // Use your API to register the user
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data), // Now stringifies the correctly constructed object
      });

      const responseData = await response.json();

      if (response.ok) {
        // After registration, log them in
        await login(data.username, data.password);
        return { success: true };
      } else {
        return {
          success: false,
          error: responseData.error || 'Registration failed'
        };
      }
    } catch (error) {
      console.error('Registration error:', error);
      return {
        success: false,
        error: (error as Error).message || 'An unexpected error occurred'
      };
    }
  };

  // Logout function
  const logout = () => {
    signOut({ callbackUrl: '/auth/login' });
  };

  const value = {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook for using auth context
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
} 