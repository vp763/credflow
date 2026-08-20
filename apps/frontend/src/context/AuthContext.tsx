'use client';

import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { User } from '@/lib/api/hooks';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (redirectTo?: string) => void;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const KEYCLOAK_URL = process.env.NEXT_PUBLIC_KEYCLOAK_URL || 'http://localhost:8080';
const KEYCLOAK_REALM = process.env.NEXT_PUBLIC_KEYCLOAK_REALM || 'credflow';
const KEYCLOAK_CLIENT_ID = process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID || 'credflow-frontend';
const DEV_MODE = process.env.NEXT_PUBLIC_DEV_MODE === 'true';

const MOCK_USER: User = {
  id: 'dev-user-1',
  email: 'dev@credflow.local',
  name: 'Dev User',
  role: 'super_admin',
  companyId: 'dev-company-1',
  companyName: 'CredFlow Demo Company',
  avatarUrl: '',
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const fetchUser = useCallback(async () => {
    if (DEV_MODE) {
      setUser(MOCK_USER);
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/me`,
        {
          credentials: 'include',
        }
      );
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = useCallback(
    (redirectTo?: string) => {
      if (DEV_MODE) {
        setUser(MOCK_USER);
        router.push(redirectTo || '/dashboard');
        router.refresh();
        return;
      }

      const redirectUri = `${window.location.origin}/auth/callback${redirectTo ? `?redirect=${encodeURIComponent(redirectTo)}` : ''}`;
      const authUrl =
        `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/auth?` +
        `client_id=${KEYCLOAK_CLIENT_ID}&` +
        `redirect_uri=${encodeURIComponent(redirectUri)}&` +
        `response_type=code&` +
        `scope=openid profile email&` +
        `state=${encodeURIComponent(redirectTo || '/dashboard')}`;
      window.location.href = authUrl;
    },
    [router]
  );

  const logout = useCallback(async () => {
    if (DEV_MODE) {
      setUser(null);
      router.push('/login');
      router.refresh();
      return;
    }

    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch {
      // Ignore logout errors
    }
    setUser(null);
    router.push('/login');
    router.refresh();
  }, [router]);

  const refreshUser = useCallback(async () => {
    await fetchUser();
  }, [fetchUser]);

  const isAuthenticated = !!user;

  return (
    <AuthContext.Provider value={{ user, isLoading, isAuthenticated, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export function useRequireAuth(redirectTo?: string) {
  const { isAuthenticated, isLoading, login } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      login(redirectTo || pathname);
    }
  }, [isAuthenticated, isLoading, login, redirectTo, pathname, router]);

  return { isAuthenticated, isLoading };
}
