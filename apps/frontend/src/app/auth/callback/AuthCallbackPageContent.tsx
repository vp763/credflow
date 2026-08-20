'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

export function AuthCallbackPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const code = searchParams.get('code');
  const state = searchParams.get('state') || '/dashboard';
  const error = searchParams.get('error');
  const errorDescription = searchParams.get('error_description');

  useEffect(() => {
    const handleCallback = async () => {
      if (error) {
        console.error('Auth error:', error, errorDescription);
        return;
      }

      if (code) {
        try {
          const response = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/callback`,
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              credentials: 'include',
              body: JSON.stringify({
                code,
                redirectUri: `${window.location.origin}/auth/callback`,
              }),
            }
          );

          if (response.ok) {
            router.push(state);
            router.refresh();
          } else {
            console.error('Token exchange failed');
            router.push(`/login?error=auth_failed`);
          }
        } catch {
          router.push(`/login?error=network_error`);
        }
      } else {
        router.push(`/login?error=no_code`);
      }
    };

    handleCallback();
  }, [code, state, error, errorDescription, router]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-muted/50 px-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
                <AlertCircle className="h-7 w-7 text-destructive" />
              </div>
              <h2 className="text-xl font-semibold">Authentication Failed</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                {errorDescription || 'An error occurred during authentication. Please try again.'}
              </p>
              <Button className="mt-6 w-full" onClick={() => router.push('/login')}>
                Return to Login
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/50 px-4">
      <Card className="w-full max-w-md">
        <CardContent className="pt-6">
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
              <Loader2 className="h-7 w-7 animate-spin text-primary" />
            </div>
            <h2 className="text-xl font-semibold">Completing Sign In</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Please wait while we verify your credentials...
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
