'use client';

import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { DashboardContent } from '@/components/dashboard/DashboardContent';
import { useRequireAuth } from '@/context/AuthContext';

export default function DashboardPage() {
  useRequireAuth();

  return (
    <DashboardLayout>
      <DashboardContent />
    </DashboardLayout>
  );
}
