'use client';

import { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { cn } from '@/lib/utils';

interface DashboardLayoutProps {
  children: ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <Header />
      <main className={cn('min-h-screen pt-16 transition-all duration-300', 'lg:ml-64')}>
        <div className="p-4 lg:p-6">{children}</div>
      </main>
    </div>
  );
}
