'use client';

import { CreditCard, TrendingUp, AlertTriangle, FileText } from 'lucide-react';
import { KPICard } from '@/components/dashboard/KPICard';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useDashboardKPIs } from '@/lib/api/hooks';

const kpiData = [
  {
    title: 'Total Receivables',
    key: 'totalReceivables',
    icon: <CreditCard className="h-6 w-6" />,
    changeType: 'neutral' as const,
  },
  {
    title: 'Collected This Month',
    key: 'collectedThisMonth',
    icon: <TrendingUp className="h-6 w-6" />,
    changeType: 'increase' as const,
  },
  {
    title: 'Overdue Amount',
    key: 'overdueAmount',
    icon: <AlertTriangle className="h-6 w-6" />,
    changeType: 'decrease' as const,
  },
  {
    title: 'Pending Invoices',
    key: 'pendingInvoices',
    icon: <FileText className="h-6 w-6" />,
    changeType: 'neutral' as const,
  },
];

export function DashboardContent() {
  const { data: kpis, isLoading } = useDashboardKPIs();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">Overview of your receivables and collections</p>
        </div>
        <Button variant="outline" className="gap-2">
          <FileText className="h-4 w-4" />
          Export Report
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {kpiData.map((kpi) => (
          <KPICard
            key={kpi.key}
            title={kpi.title}
            value={
              isLoading ? undefined : formatCurrency(kpis?.[kpi.key as keyof typeof kpis] as number)
            }
            change={isLoading ? undefined : getChange(kpi.key)}
            changeType={kpi.changeType}
            icon={kpi.icon}
            loading={isLoading}
          />
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="lg:col-span-4">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Recent Invoices</CardTitle>
            <Button variant="ghost" size="sm">
              View All
            </Button>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="flex items-center gap-4">
                    <Skeleton className="h-10 w-10 rounded-full" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-4 w-1/2" />
                    </div>
                    <Skeleton className="h-4 w-24" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                {[
                  {
                    id: 'INV-001',
                    customer: 'Acme Corp',
                    amount: 45000,
                    status: 'pending',
                    date: '2024-01-15',
                  },
                  {
                    id: 'INV-002',
                    customer: 'TechStart Inc',
                    amount: 28000,
                    status: 'paid',
                    date: '2024-01-14',
                  },
                  {
                    id: 'INV-003',
                    customer: 'Global Solutions',
                    amount: 67000,
                    status: 'overdue',
                    date: '2024-01-10',
                  },
                  {
                    id: 'INV-004',
                    customer: 'Innovate Ltd',
                    amount: 12000,
                    status: 'pending',
                    date: '2024-01-12',
                  },
                  {
                    id: 'INV-005',
                    customer: 'Future Systems',
                    amount: 35000,
                    status: 'paid',
                    date: '2024-01-13',
                  },
                ].map((invoice) => (
                  <div key={invoice.id} className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                        <FileText className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium">{invoice.id}</p>
                        <p className="text-sm text-muted-foreground">{invoice.customer}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="font-medium">{formatCurrency(invoice.amount)}</span>
                      <Badge variant={getStatusVariant(invoice.status)}>{invoice.status}</Badge>
                      <span className="text-muted-foreground">{formatDate(invoice.date)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Top Customers by Outstanding</CardTitle>
            <Button variant="ghost" size="sm">
              View All
            </Button>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="flex items-center gap-4">
                    <Skeleton className="h-10 w-10 rounded-full" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-4 w-1/2" />
                    </div>
                    <Skeleton className="h-4 w-24" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                {[
                  { name: 'Acme Corp', outstanding: 125000, invoices: 8 },
                  { name: 'Global Solutions', outstanding: 98000, invoices: 5 },
                  { name: 'TechStart Inc', outstanding: 67000, invoices: 4 },
                  { name: 'Innovate Ltd', outstanding: 45000, invoices: 3 },
                ].map((customer, index) => (
                  <div key={customer.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary text-sm font-medium">
                        {index + 1}
                      </div>
                      <div>
                        <p className="font-medium">{customer.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {customer.invoices} invoices
                        </p>
                      </div>
                    </div>
                    <span className="font-medium">{formatCurrency(customer.outstanding)}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

function getChange(key: string): string {
  const changes: Record<string, string> = {
    totalReceivables: '+12.5%',
    collectedThisMonth: '+23.1%',
    overdueAmount: '-8.2%',
    pendingInvoices: '+3',
  };
  return changes[key] || '';
}

function getStatusVariant(status: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (status) {
    case 'paid':
      return 'default';
    case 'pending':
      return 'secondary';
    case 'overdue':
      return 'destructive';
    default:
      return 'outline';
  }
}
