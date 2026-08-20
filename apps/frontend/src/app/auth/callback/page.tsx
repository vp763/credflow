'use client';

import { Suspense } from 'react';
import { AuthCallbackPageContent } from './AuthCallbackPageContent';

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={<div className="flex min-h-screen items-center justify-center">Loading...</div>}
    >
      <AuthCallbackPageContent />
    </Suspense>
  );
}
