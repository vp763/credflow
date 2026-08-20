'use client';

import { cn } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';

interface KPICardProps {
  title: string;
  value: string | number | undefined;
  change?: string;
  changeType?: 'increase' | 'decrease' | 'neutral';
  icon?: React.ReactNode;
  loading?: boolean;
}

export function KPICard({
  title,
  value,
  change,
  changeType = 'neutral',
  icon,
  loading = false,
}: KPICardProps) {
  return (
    <div className="rounded-lg border bg-card p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-muted-foreground">{title}</p>
          <div className="mt-2 flex items-baseline gap-2">
            {loading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <p className="text-3xl font-bold tracking-tight">{value}</p>
            )}
            {change && !loading && (
              <span
                className={cn(
                  'text-sm font-medium',
                  changeType === 'increase' && 'text-green-600 dark:text-green-400',
                  changeType === 'decrease' && 'text-red-600 dark:text-red-400',
                  changeType === 'neutral' && 'text-muted-foreground'
                )}
              >
                {change}
              </span>
            )}
          </div>
        </div>
        {icon && !loading && (
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-muted text-muted-foreground">
            {icon}
          </div>
        )}
        {icon && loading && <Skeleton className="h-12 w-12 rounded-lg" />}
      </div>
    </div>
  );
}
