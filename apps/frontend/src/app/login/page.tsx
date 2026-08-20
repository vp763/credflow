'use client';

import { Suspense } from 'react';
import { LoginPageContent } from './LoginPageContent';

export default function LoginPage() {
  return (
    <Suspense
      fallback={<div className="flex min-h-screen items-center justify-center">Loading...</div>}
    >
      <LoginPageContent />
    </Suspense>
  );
}
