import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryOptions,
  UseMutationOptions,
} from '@tanstack/react-query';
import { apiClient } from './client';

export const queryKeys = {
  invoices: ['invoices'] as const,
  invoice: (id: string) => ['invoices', id] as const,
  customers: ['customers'] as const,
  customer: (id: string) => ['customers', id] as const,
  payments: ['payments'] as const,
  dashboard: ['dashboard'] as const,
  user: ['user'] as const,
  companies: ['companies'] as const,
};

export interface Invoice {
  id: string;
  invoiceNumber: string;
  customerName: string;
  amount: number;
  status: 'paid' | 'pending' | 'overdue';
  date: string;
  dueDate: string;
}

export interface Customer {
  id: string;
  name: string;
  email: string;
  phone: string;
  gstin: string;
  address: string;
  outstandingAmount: number;
}

export interface Payment {
  id: string;
  invoiceId: string;
  amount: number;
  date: string;
  method: string;
  reference: string;
}

export interface DashboardKPIs {
  totalReceivables: number;
  overdueAmount: number;
  collectedThisMonth: number;
  pendingInvoices: number;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  companyId: string;
  companyName: string;
  avatarUrl?: string;
}

export interface Company {
  id: string;
  name: string;
  gstin: string;
  isActive: boolean;
}

export function useInvoices(
  options?: UseQueryOptions<Invoice[]>
): ReturnType<typeof useQuery<Invoice[]>> {
  return useQuery({
    queryKey: queryKeys.invoices,
    queryFn: () => apiClient.get<Invoice[]>('/invoices'),
    ...options,
  });
}

export function useInvoice(
  id: string,
  options?: UseQueryOptions<Invoice>
): ReturnType<typeof useQuery<Invoice>> {
  return useQuery({
    queryKey: queryKeys.invoice(id),
    queryFn: () => apiClient.get<Invoice>(`/invoices/${id}`),
    enabled: !!id,
    ...options,
  });
}

export function useCustomers(
  options?: UseQueryOptions<Customer[]>
): ReturnType<typeof useQuery<Customer[]>> {
  return useQuery({
    queryKey: queryKeys.customers,
    queryFn: () => apiClient.get<Customer[]>('/customers'),
    ...options,
  });
}

export function useCustomer(
  id: string,
  options?: UseQueryOptions<Customer>
): ReturnType<typeof useQuery<Customer>> {
  return useQuery({
    queryKey: queryKeys.customer(id),
    queryFn: () => apiClient.get<Customer>(`/customers/${id}`),
    enabled: !!id,
    ...options,
  });
}

export function usePayments(
  options?: UseQueryOptions<Payment[]>
): ReturnType<typeof useQuery<Payment[]>> {
  return useQuery({
    queryKey: queryKeys.payments,
    queryFn: () => apiClient.get<Payment[]>('/payments'),
    ...options,
  });
}

const DEV_MODE = process.env.NEXT_PUBLIC_DEV_MODE === 'true';

const MOCK_KPIS: DashboardKPIs = {
  totalReceivables: 1250000,
  collectedThisMonth: 450000,
  overdueAmount: 120000,
  pendingInvoices: 12,
};

export function useDashboardKPIs(
  options?: UseQueryOptions<DashboardKPIs>
): ReturnType<typeof useQuery<DashboardKPIs>> {
  return useQuery({
    queryKey: queryKeys.dashboard,
    queryFn: DEV_MODE
      ? async () => MOCK_KPIS
      : () => apiClient.get<DashboardKPIs>('/dashboard/kpis'),
    staleTime: DEV_MODE ? Infinity : undefined,
    ...options,
  });
}

export function useUser(options?: UseQueryOptions<User>): ReturnType<typeof useQuery<User>> {
  return useQuery({
    queryKey: queryKeys.user,
    queryFn: () => apiClient.get<User>('/auth/me'),
    ...options,
  });
}

export function useCompanies(
  options?: UseQueryOptions<Company[]>
): ReturnType<typeof useQuery<Company[]>> {
  return useQuery({
    queryKey: queryKeys.companies,
    queryFn: () => apiClient.get<Company[]>('/companies'),
    ...options,
  });
}

export function useSwitchCompany(
  options?: UseMutationOptions<void, Error, string>
): ReturnType<typeof useMutation<void, Error, string>> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (companyId: string) => apiClient.post('/auth/switch-company', { companyId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.user });
      queryClient.invalidateQueries({ queryKey: queryKeys.companies });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard });
    },
    ...options,
  });
}

export function useLogin(
  options?: UseMutationOptions<
    { accessToken: string; refreshToken: string },
    Error,
    { username: string; password: string }
  >
): ReturnType<
  typeof useMutation<
    { accessToken: string; refreshToken: string },
    Error,
    { username: string; password: string }
  >
> {
  return useMutation({
    mutationFn: (credentials: { username: string; password: string }) =>
      apiClient.post('/auth/login', credentials),
    ...options,
  });
}

export function useLogout(
  options?: UseMutationOptions<void, Error, void>
): ReturnType<typeof useMutation<void, Error, void>> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post('/auth/logout'),
    onSuccess: () => {
      queryClient.clear();
    },
    ...options,
  });
}
