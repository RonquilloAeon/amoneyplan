'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useMutation, useQuery, gql } from '@apollo/client';

// GraphQL operations
const LOGIN_MUTATION = gql`
  mutation Login($username: String!, $password: String!) {
    auth {
      login(username: $username, password: $password) {
        success
        token
        error
      }
    }
  }
`;

const REGISTER_MUTATION = gql`
  mutation Register($username: String!, $email: String!, $password: String!, $firstName: String, $lastName: String) {
    auth {
      register(
        username: $username
        email: $email
        password: $password
        firstName: $firstName
        lastName: $lastName
      ) {
        success
        token
        error
      }
    }
  }
`;

const ME_QUERY = gql`
  query Me {
    me {
      id
      username
      email
      firstName
      lastName
    }
  }
`;

// Define user type
interface User {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
}

// Auth context type
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (data: RegisterData) => Promise<{ success: boolean; error?: string }>;
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
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Login mutation
  const [loginMutation] = useMutation(LOGIN_MUTATION);
  
  // Register mutation
  const [registerMutation] = useMutation(REGISTER_MUTATION);

  // Me query
  const { data: userData, loading: userLoading, refetch: refetchUser } = useQuery(ME_QUERY, {
    skip: !hasToken(), // Skip the query if no token exists
    onCompleted: (data) => {
      if (data?.me) {
        setUser(data.me);
        setIsAuthenticated(true);
      } else {
        setUser(null);
        setIsAuthenticated(false);
      }
      setIsLoading(false);
    },
    onError: () => {
      setUser(null);
      setIsAuthenticated(false);
      setIsLoading(false);
      // If the query fails, likely the token is invalid, so remove it
      if (typeof window !== 'undefined') {
        localStorage.removeItem('authToken');
      }
    }
  });

  // Check if token exists
  function hasToken(): boolean {
    if (typeof window === 'undefined') return false;
    return !!localStorage.getItem('authToken');
  }

  // Check auth on initial load
  useEffect(() => {
    const checkAuth = async () => {
      if (hasToken()) {
        await refetchUser();
      } else {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, [refetchUser]);

  // Login function
  const login = async (username: string, password: string) => {
    try {
      const { data } = await loginMutation({
        variables: { username, password },
      });

      if (data?.auth?.login?.success) {
        const token = data.auth.login.token;
        
        // Save token to localStorage
        if (typeof window !== 'undefined') {
          localStorage.setItem('authToken', token);
        }
        
        // Refetch user data
        await refetchUser();
        
        return { success: true };
      } else {
        return { 
          success: false, 
          error: data?.auth?.login?.error || 'Login failed' 
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
  const register = async (data: RegisterData) => {
    try {
      const response = await registerMutation({
        variables: data,
      });

      const registerData = response.data?.auth?.register;

      if (registerData?.success) {
        const token = registerData.token;
        
        // Save token to localStorage
        if (typeof window !== 'undefined') {
          localStorage.setItem('authToken', token);
        }
        
        // Refetch user data
        await refetchUser();
        
        return { success: true };
      } else {
        return { 
          success: false, 
          error: registerData?.error || 'Registration failed' 
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
    if (typeof window !== 'undefined') {
      localStorage.removeItem('authToken');
    }
    setUser(null);
    setIsAuthenticated(false);
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